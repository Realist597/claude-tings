"""Tracing the bow out of bow_reference.jpg (numpy / scipy / scikit-image / triangle; no Blender).

    load_reference()  the painting and an estimate of its grey backdrop
    bow_mask()        the bow's pixels: what the backdrop can't reach from the picture's edges, minus the
                      string and the arrows
    upright()         the bow resampled at 2x with its string vertical, and its grip found
    symmetric()       its lower half mirrored over the grip, so both limbs match (the painting's two
                      limbs aren't drawn alike, and the upper one's highlights read as holes)
    outline()         that silhouette as precise polygons (outer edges and real openings)
    triangulate()     a quality triangle mesh of them
"""
import math, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'bow_reference.jpg')
STRING = ((800, 298), (160, 1000))   # the string's ends in the painting (px), found by fitting the line
UP = 2.0                             # resampling scale for tracing


def load_reference():
    img = np.asarray(Image.open(REF).convert('RGB')).astype(np.float32)
    H, W, _ = img.shape
    lum, sat = img.mean(2), img.max(2) - img.min(2)
    # the backdrop is a neutral radial gradient: estimate it ring by ring from the grey pixels
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot(yy - H / 2, xx - W / 2).astype(int)
    grey = sat < 10
    ring, last = np.zeros(r.max() + 5), 66.0
    for k in range(0, r.max() + 1, 4):
        sel = grey & (r >= k) & (r < k + 4)
        if sel.sum() > 20:
            last = float(np.median(lum[sel]))
        ring[k:k + 4] = last
    return img, lum, sat, ring[r]


def bow_mask(img, lum, sat, bg):
    H, W = lum.shape
    backdrop_like = (np.abs(lum - bg) <= 10) & (sat <= 16)
    lab, n = ndi.label(backdrop_like)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ~np.isin(lab, list(edge))
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    openings = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 500 and (i + 1) not in edge])
    fg &= ~openings
    (ax, ay), (bx, by) = STRING
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.array([bx - ax, by - ay], float)
    L = np.linalg.norm(d)
    t = ((xx - ax) * d[0] + (yy - ay) * d[1]) / L ** 2
    dist = np.abs((xx - ax) * d[1] - (yy - ay) * d[0]) / L
    fg &= ~((dist < 3.5) & (t > 0.03) & (t < 0.97))
    fg = ndi.binary_opening(fg, iterations=1)
    L_, m = ndi.label(fg)
    left = [i for i in np.unique(L_[:, :120]) if i]
    bow = L_ == max(left, key=lambda i: (L_ == i).sum())
    return ndi.binary_fill_holes(bow) & ~openings


def upright(img, mask):
    """resample at UP x with the string vertical (top anchor at the top) and the bow's body on the left;
    returns the soft mask, the colour, the string's column and its ends' rows, and the grip row"""
    (ax, ay), (bx, by) = STRING
    A, B = np.array([ax, ay], float), np.array([bx, by], float)
    e = (B - A) / np.linalg.norm(B - A)          # down the string
    f = np.array([-e[1], e[0]])                  # across it
    ys, xs = np.nonzero(mask)
    P = np.stack([xs, ys], 1).astype(float)
    if ((P - A) @ f).mean() > 0:                  # keep the body on the left (-u)
        f = -f
    u, v = (P - A) @ f * UP, (P - A) @ e * UP
    pad = 24
    u0, v0 = -u.min() + pad, -v.min() + pad
    W, H = int(u.max() + u0 + pad), int(v.max() + v0 + pad)
    uu, vv = np.meshgrid(np.arange(W, dtype=float), np.arange(H, dtype=float))
    sx = A[0] + (uu - u0) / UP * f[0] + (vv - v0) / UP * e[0]
    sy = A[1] + (uu - u0) / UP * f[1] + (vv - v0) / UP * e[1]
    m = ndi.map_coordinates(mask.astype(np.float32), [sy, sx], order=1, cval=0)
    col = np.dstack([ndi.map_coordinates(img[..., c], [sy, sx], order=3, cval=0) for c in range(3)])
    L = np.linalg.norm(B - A) * UP
    gv = v0 + L / 2                               # the grip: level with the middle of the string
    row = np.nonzero(m[int(gv)] > 0.5)[0]
    return dict(mask=m, col=np.clip(col, 0, 255), u0=u0, v_top=v0, v_bot=v0 + L, grip_v=gv,
                grip_u=row.mean() if len(row) else u0 / 2)


def symmetric(up):
    """mirror the lower limb (below the grip) over the grip to make the upper one"""
    m, col, g = up['mask'], up['col'], int(round(up['grip_v']))
    below = m.shape[0] - g
    H = 2 * below
    mm = np.zeros((H, m.shape[1]), np.float32)
    cc = np.zeros((H, m.shape[1], 3), np.float32)
    mm[below:] = m[g:]
    cc[below:] = col[g:]
    mm[:below] = m[g:][::-1]
    cc[:below] = col[g:][::-1]
    # the string: its lower end kept, the upper mirrored to match
    half = up['v_bot'] - g
    return dict(mask=mm, col=cc, u0=up['u0'], grip_v=below, grip_u=up['grip_u'], v_top=below - half, v_bot=below + half)


def outline(mask, tol=0.6, min_area=40):
    """the silhouette's boundary as polygons (x, y in pixels), outer edges and holes, sharp corners kept"""
    from skimage import measure
    soft = ndi.gaussian_filter(mask.astype(np.float32), 0.9)
    polys = []
    for c in measure.find_contours(soft, 0.5):
        c = measure.approximate_polygon(c, tolerance=tol)
        if len(c) < 4:
            continue
        xy = c[:, ::-1][:-1]                      # (row, col) -> (x, y); drop the repeated end
        area = 0.5 * abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))
        if area >= min_area:
            polys.append(xy)
    return polys, soft


def triangulate(polys, soft, max_area):
    """a quality (no slivers) triangulation of the silhouette; returns vertices, triangles, and which
    vertices lie on the outline"""
    import triangle as tr
    verts, segs, holes = [], [], []
    for p in polys:
        k = len(verts)
        verts += p.tolist()
        segs += [(k + i, k + (i + 1) % len(p)) for i in range(len(p))]
        # seed the openings: any empty point strictly inside this ring (for an outer edge that can only be
        # inside one of its openings, which is harmless)
        seed = _interior_seed(p, soft, empty=True)
        if seed is not None:
            holes.append(seed)
    data = dict(vertices=np.array(verts), segments=np.array(segs))
    if holes:
        data['holes'] = np.array(holes)
    out = tr.triangulate(data, f'pq30a{max_area:.1f}')
    V, T = out['vertices'], out['triangles']
    on_edge = np.zeros(len(V), bool)
    on_edge[np.unique(out['segments'])] = True
    return V, T, on_edge, out['segments']


def _point_in(poly, pt):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _interior_seed(poly, soft, empty):
    """a point strictly inside poly where the mask is empty (for holes) -- tried along a few scanlines"""
    ys = np.linspace(poly[:, 1].min(), poly[:, 1].max(), 17)[1:-1]
    for y in ys:
        xs = np.linspace(poly[:, 0].min(), poly[:, 0].max(), 90)
        for x in xs:
            if _point_in(poly, (x, y)) and (soft[int(y), int(x)] < 0.5) == empty:
                return (x, y)
    return None
