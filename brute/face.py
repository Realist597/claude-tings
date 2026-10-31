"""The Brute's head: the R6 head (scaled to his body) with his face cut into it, drawn from the concept.

The face has no nose and no brows. It's cut in:
    sockets   two deep sockets, each topped by one hard straight line running from the side of the face down to a
              crease between the eyes, so together they make a V of a scowl. Under the line the socket's wall drops
              steeply in; below the eye it slopes gently back out
    eyes      teardrops, rounded at the outer end and drawn to a point at the inner corner, their tops slanting
              down with the scowl, sunk at the bottom of the sockets. They glow (their own mesh)
    mouth     a low trapezoid, its bottom corners drawn out to points. Inside, in the dark: two fangs crossing the
              bite (a long one hanging on the left, a broad one standing on the right) and between them two rows
              of blunt, blocky teeth
    folds     between the eyes the skin knots over a groove; two heavy wavy folds across the forehead; creases
              under the eyes
    scars     thin red cuts: two down the forehead to the left eye and one below it, one down to the right eye and
              two below it

The face is designed in 2D as seen from straight in front (X across, + toward the head's left; Z up; both -1..1, in
head radii: the head is 2 across and 2 tall). Each shape's signed distance sets how deep the face is cut there, and
the head's surface is cut in by that much along its normal. The same depth map makes both meshes:
    the detailed sculpt   a fine grid round the head, with every fold, crease and cut, painted
    the game mesh         its face triangulated so its edges run along the depth map's contour lines (the rims of
                          the sockets, the eyes, the mouth and each tooth), so its outlines stay crisp on few
                          triangles

    build_detail(scale, centre), build_game(scale, centre), eyes(scale, centre), bake(lo, hi, out_dir)
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector

D_SOCK = 0.095          # how deep the sockets are cut
D_POCKET = 0.05         # the pocket under each eye, behind its glowing mesh
D_EYE = 0.1             # where the glowing eye's rim sits
D_MOUTH = 0.2           # how deep the mouth goes


# ------------------------------------------------------------------ 2D shapes

def smooth01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sd_poly(X, Z, pts):
    """signed distance from each point to a closed polygon: negative inside"""
    P = np.asarray(pts, float)
    d2 = np.full(X.shape, np.inf)
    inside = np.zeros(X.shape, bool)
    for i in range(len(P)):
        ax, az = P[i - 1]
        bx, bz = P[i]
        ex, ez = bx - ax, bz - az
        t = np.clip(((X - ax) * ex + (Z - az) * ez) / max(ex * ex + ez * ez, 1e-12), 0, 1)
        d2 = np.minimum(d2, (X - ax - t * ex) ** 2 + (Z - az - t * ez) ** 2)
        cross = ((az > Z) != (bz > Z)) & (X < (bx - ax) * (Z - az) / (bz - az + 1e-12) + ax)
        inside ^= cross
    return np.where(inside, -1.0, 1.0) * np.sqrt(d2)


def seg_dist(X, Z, pts):
    """distance from each point to a polyline, and how far along it (0..1) the nearest point is"""
    best = np.full(X.shape, np.inf)
    along = np.zeros(X.shape)
    lens = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(lens) or 1.0
    acc = 0.0
    for i in range(len(pts) - 1):
        (ax, az), (bx, bz) = pts[i], pts[i + 1]
        ex, ez = bx - ax, bz - az
        t = np.clip(((X - ax) * ex + (Z - az) * ez) / max(ex * ex + ez * ez, 1e-12), 0, 1)
        d = np.hypot(X - ax - t * ex, Z - az - t * ez)
        closer = d < best
        best = np.where(closer, d, best)
        along = np.where(closer, (acc + t * lens[i]) / total, along)
        acc += lens[i]
    return best, along


def curve(ctrl, n):
    """a smooth open curve through the control points (Catmull-Rom), n points along it"""
    c = np.asarray(ctrl, float)
    c = np.concatenate([2 * c[:1] - c[1:2], c, 2 * c[-1:] - c[-2:-1]])
    out = []
    segs = len(c) - 3
    for t in np.linspace(0, segs, n):
        i = min(int(t), segs - 1)
        u = t - i
        p0, p1, p2, p3 = c[i:i + 4]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(out)


def ends(a, soft=0.2):
    return np.clip(a / soft, 0, 1) * np.clip((1 - a) / soft, 0, 1)


def ridge(X, Z, pts, w, h, taper=ends):
    """a line raised (h < 0: the depth map goes out) or cut in (h > 0) along a polyline"""
    d, a = seg_dist(X, Z, pts)
    return h * taper(a) * np.exp(-(d / w) ** 2)


# ------------------------------------------------------------------ the face, drawn on the head's right (x < 0)
#                                                                    and mirrored, except the scars

SCOWL = ((-0.985, 0.294), (-0.06, -0.012))        # the hard line over the socket, from the face's side inward

SOCKET = [(-0.985, 0.294), (-0.06, -0.012), (-0.015, -0.036),       # the line, running on into the crease
          (-0.04, -0.062), (-0.18, -0.068), (-0.32, -0.072), (-0.44, -0.09), (-0.56, -0.097), (-0.67, -0.082),
          (-0.75, -0.042), (-0.82, 0.045), (-0.9, 0.14), (-0.95, 0.205), (-0.985, 0.25)]

# the left eye's opening: a teardrop, rounded at its outer end and drawn to a point at its inner corner, its top
# edge slanting down along the scowl. From the inner corner along the top, round the outer end and back
EYE = [(-0.345, 0.003), (-0.43, 0.037), (-0.54, 0.07), (-0.63, 0.088), (-0.68, 0.08), (-0.703, 0.05),
       (-0.69, 0.018), (-0.64, -0.013), (-0.54, -0.043), (-0.43, -0.036), (-0.345, 0.003)]


def eye_poly(grow=0.0):
    """the left eye's opening as a closed polygon, sharp only at its inner corner"""
    pts = curve(EYE, 56)[:-1]
    if grow:
        c = pts.mean(0)
        pts = c + (pts - c) * (1 + grow / np.linalg.norm(pts - c, axis=1, keepdims=True))
    return pts


MOUTH = [(-0.26, -0.59), (0.26, -0.59), (0.44, -0.835), (0.22, -0.84), (0.0, -0.842), (-0.22, -0.84),
         (-0.44, -0.835)]


def block_tooth(c, top, bottom, w, rr=0.012):
    """a blunt tooth's outline: a rectangle with its corners rounded"""
    pts = []
    for cx, cz, a0 in ((c + w / 2 - rr, top - rr, 0.0), (c - w / 2 + rr, top - rr, 0.5),
                       (c - w / 2 + rr, bottom + rr, 1.0), (c + w / 2 - rr, bottom + rr, 1.5)):
        for k in range(5):
            a = math.pi * (a0 + k / 8)
            pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


def teeth_shapes():
    """every tooth's outline: (polygon, how far in its face sits). Two fangs that cross the bite, one hanging
    on the left, one standing on the right, and between them two long bars of blunt teeth set back in the dark,
    black above, between and below them"""
    out = [(block_tooth(-0.005, -0.66, -0.714, 0.29, 0.02), 0.058),            # the upper row, its big end tooth
           (block_tooth(0.185, -0.655, -0.732, 0.075, 0.03), 0.054),
           (block_tooth(-0.03, -0.76, -0.802, 0.28, 0.018), 0.062)]            # the lower row
    # the upper fang, on the left: long, from the top of the mouth nearly to its floor
    out.append(([(-0.265, -0.57), (-0.185, -0.57), (-0.183, -0.64), (-0.188, -0.71), (-0.2, -0.762),
                 (-0.218, -0.792), (-0.234, -0.786), (-0.25, -0.75), (-0.262, -0.69)], 0.045))
    # the lower fang, on the right: broad at its root, leaning up along the mouth's side to a point
    out.append(([(0.21, -0.87), (0.345, -0.87), (0.33, -0.79), (0.307, -0.715), (0.284, -0.655),
                 (0.271, -0.626), (0.26, -0.65), (0.243, -0.72), (0.225, -0.79)], 0.045))
    return out


# the cuts: two down the forehead to the left eye and one below it, one down to the right eye and two below it
SCARS = ([(-0.5, 0.96), (-0.43, 0.66), (-0.36, 0.4), (-0.3, 0.18), (-0.27, 0.085)],
         [(-0.6, 0.52), (-0.585, 0.36), (-0.565, 0.21)],
         [(-0.62, -0.075), (-0.69, -0.2), (-0.78, -0.37)],
         [(0.53, 0.93), (0.6, 0.72), (0.655, 0.49), (0.7, 0.3), (0.722, 0.2)],
         [(0.65, -0.105), (0.675, -0.28), (0.7, -0.47)],
         [(0.738, -0.07), (0.752, -0.21)])


def scowl_z(x):
    (x0, z0), (x1, z1) = SCOWL
    return z0 + (x - x0) * (z1 - z0) / (x1 - x0)


def relief(X, Z, detail=False):
    """how deep the face is cut at each point of the front (head radii, inward), and masks for painting it"""
    Xm = -np.abs(X)
    s = sd_poly(Xm, Z, SOCKET)
    steep = smooth01((Z - (scowl_z(Xm) - 0.06)) / 0.045)        # under the line: a steep wall; lower: a slope
    w = 0.075 - 0.035 * steep
    sock = D_SOCK * smooth01(-s / w)
    e = sd_poly(Xm, Z, eye_poly())
    pocket = D_POCKET * smooth01(-e / 0.004)
    m = sd_poly(X, Z, MOUTH)
    cavity = D_MOUTH * smooth01(-m / 0.014)
    d = sock + pocket + cavity
    tooth_m = np.zeros(X.shape)
    for poly, face_in in teeth_shapes():
        t = sd_poly(X, Z, poly)
        surf = face_in + 0.035 * (1 - smooth01(-t / 0.016))
        on = (t < 0) & (m < 0.004)
        d = np.where(on, np.minimum(d, surf), d)
        tooth_m = np.maximum(tooth_m, on * smooth01(-t / 0.004))
    d -= 0.007 * np.exp(-((m - 0.008) / 0.009) ** 2)               # a thin rolled lip round the mouth
    d -= 0.015 * np.cos(np.pi / 2 * np.clip(X / 0.9, -1, 1)) * np.cos(np.pi / 2 * np.clip(Z / 0.9, -1, 1))
    masks = dict(socket=smooth01(sock / D_SOCK), eye=smooth01(-e / 0.004), mouth=smooth01(-m / 0.004),
                 teeth=tooth_m, lip=np.exp(-((m - 0.006) / 0.012) ** 2))
    if detail:
        dd = np.zeros(X.shape)
        # the brow's mass bulging over each scowl line, so the line reads as an overhang
        dd += ridge(Xm, Z, [(-0.9, 0.315), (-0.5, 0.185), (-0.14, 0.07)], 0.05, -0.014, lambda a: ends(a, 0.25))
        # between the eyes the skin knots: a bulge either side of a deep groove, each bulge creased
        dd += -0.018 * np.exp(-(((Xm + 0.13) / 0.085) ** 2 + ((Z - 0.2) / 0.1) ** 2))
        dd += ridge(X, Z, [(0.0, -0.01), (0.004, 0.2), (0.0, 0.4)], 0.016, 0.012, lambda a: ends(a, 0.3))
        for (x0, z0), (x1, z1), w, h in ((( -0.03, 0.02), (-0.07, 0.3), 0.022, -0.009),
                                         ((-0.06, 0.02), (-0.16, 0.27), 0.01, 0.007),
                                         ((-0.09, 0.025), (-0.24, 0.24), 0.026, -0.008)):
            dd += ridge(Xm, Z, [(x0, z0), (x1, z1)], w, h, lambda a: ends(a, 0.35))
        # the forehead rounded, with three soft, uneven folds across it
        dd += -0.012 * np.exp(-((X / 0.6) ** 2 + ((Z - 0.6) / 0.32) ** 2))
        for z0, ph, span, amp in ((0.43, 0.0, 0.55, 0.018), (0.6, 1.3, 0.62, 0.022), (0.78, 2.4, 0.5, 0.015)):
            xs = np.linspace(-span, span, 9)
            wave = [(x, z0 + amp * math.sin(5.2 * x + ph) - 0.02 * max(0.0, 1 - abs(x) / 0.25)) for x in xs]
            dd += ridge(X, Z, wave, 0.042, -0.007)
            dd += ridge(X, Z, [(x, z + 0.06) for x, z in wave], 0.022, 0.004)
        # the cheeks a little full
        dd += -0.012 * np.exp(-(((Xm + 0.55) / 0.22) ** 2 + ((Z + 0.3) / 0.16) ** 2))
        # under each eye: the lid's bag, a crease under it and a fainter one lower
        dd += ridge(Xm, Z, [(-0.36, -0.03), (-0.45, -0.07), (-0.56, -0.08), (-0.66, -0.06)], 0.02, -0.007)
        dd += ridge(Xm, Z, [(-0.34, -0.08), (-0.45, -0.118), (-0.58, -0.128), (-0.7, -0.1)], 0.012, 0.009)
        dd += ridge(Xm, Z, [(-0.3, -0.135), (-0.42, -0.185), (-0.55, -0.205)], 0.016, 0.004)
        # the cuts
        sc = np.zeros(X.shape)
        for pts in SCARS:
            dist, a = seg_dist(X, Z, pts)
            k = ends(a, 0.15)
            dd += 0.006 * k * np.exp(-(dist / 0.006) ** 2)
            sc = np.maximum(sc, k * np.exp(-(dist / 0.0072) ** 2))
        masks['scar'] = sc
        flat = 1 - np.maximum(masks['socket'], masks['mouth'])       # keep it off the cut-in parts
        d = d + dd * flat
    return d, masks


# ------------------------------------------------------------------ the head

# The R6 head, in head radii: a cylinder 2 across and 2 tall, its top and bottom edges rounded over by half its
# radius. Its surface is mapped by the angle round it (th: 0 at the front, + toward the head's left, x > 0) and the
# distance up its profile (v: 0 at the middle of its bottom, up the side, over to the middle of its top). The face is
# drawn as seen from straight in front (X, Z) and cut in along the surface's normal
ER = 0.5                                         # how far its top and bottom edges are rounded over
L_EDGE = math.pi / 2 * ER
V_A = 1 - ER                                     # where the bottom edge starts to round up
V_S = V_A + L_EDGE                               # where the side starts
V_T = V_S + 2 * (1 - ER)                         # where the top edge starts to round over
V_B = V_T + L_EDGE                               # where the top starts
V_END = V_B + 1 - ER
TH_F = math.radians(100)                         # the face's band reaches this far round either side


def profile(v):
    """radius, height and outward normal (r, z) of the head's profile at each distance v up it"""
    v = np.asarray(v, float)
    a1 = np.clip((v - V_A) / ER, 0, math.pi / 2)
    a2 = np.clip((v - V_T) / ER, 0, math.pi / 2)
    conds = [v < V_A, v < V_S, v < V_T, v < V_B]
    r = np.select(conds, [v, 1 - ER + ER * np.sin(a1), np.ones_like(v), 1 - ER + ER * np.cos(a2)], V_END - v)
    z = np.select(conds, [-np.ones_like(v), -(1 - ER) - ER * np.cos(a1), v - V_S - (1 - ER),
                          (1 - ER) + ER * np.sin(a2)], np.ones_like(v))
    nr = np.select(conds, [np.zeros_like(v), np.sin(a1), np.ones_like(v), np.cos(a2)], np.zeros_like(v))
    nz = np.select(conds, [-np.ones_like(v), -np.cos(a1), np.zeros_like(v), np.sin(a2)], np.ones_like(v))
    return r, z, nr, nz


def surface(th, v):
    """points on the head and their outward normals"""
    th, v = np.broadcast_arrays(np.asarray(th, float), np.asarray(v, float))
    r, z, nr, nz = profile(v)
    s, c = np.sin(th), np.cos(th)
    return np.stack([r * s, -r * c, z], -1), np.stack([nr * s, -nr * c, nz], -1)


def z_to_v(Z):
    """how far up the profile the front's point at height Z is"""
    Z = np.asarray(Z, float)
    lo = V_A + ER * np.arccos(np.clip((-(1 - ER) - Z) / ER, -1, 1))
    hi = V_T + ER * np.arcsin(np.clip((Z - (1 - ER)) / ER, -1, 1))
    return np.where(Z < -(1 - ER), lo, np.where(Z < 1 - ER, V_S + Z + (1 - ER), hi))


def front_param(X, Z):
    """(th, v) of the point seen at (X, Z) from straight in front"""
    v = z_to_v(Z)
    return np.arcsin(np.clip(X / np.maximum(profile(v)[0], 1e-6), -1, 1)), v


def head_relief(th, v, detail=False):
    """relief() over the head: the face as seen from in front, faded out as the head turns away. Also returns the
    points' (X, Z)"""
    th, v = np.broadcast_arrays(np.asarray(th, float), np.asarray(v, float))
    r, z, _, _ = profile(v)
    X = r * np.sin(th)
    D, masks = relief(X, z, detail)
    k = smooth01((np.cos(th) - 0.03) / 0.12)
    return D * k, {key: m * k for key, m in masks.items()}, X, z


# the texture: the face's band (from the bottom's edge round to the top's, TH_F round either side) across the
# bottom; above it the band's back, the bottom and the top. All at their true proportions
UV_G = 0.008
KF = (1 - 2 * UV_G) / (2 * TH_F)
Y2 = UV_G + (V_B - V_A) * KF + 2 * UV_G
KC = 1 - UV_G - Y2
KB = KC / (V_B - V_A)
X_C1 = UV_G + (2 * math.pi - 2 * TH_F) * KB + 2 * UV_G
X_C2 = X_C1 + KC + 2 * UV_G


def uv_front(th, v):
    return UV_G + (th + TH_F) * KF, UV_G + (v - V_A) * KF


def uv_back(th, v):
    return UV_G + (th - TH_F) * KB, Y2 + (v - V_A) * KB


def uv_bottom(th, v):
    return X_C1 + KC / 2 + v * math.sin(th) * KC, Y2 + KC / 2 + v * math.cos(th) * KC


def uv_top(th, v):
    r = V_END - v
    return X_C2 + KC / 2 + r * math.sin(th) * KC, Y2 + KC / 2 - r * math.cos(th) * KC


# ------------------------------------------------------------------ the game mesh

def simplify(pts, tol):
    """Douglas-Peucker"""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    L = np.linalg.norm(ab)
    if L < 1e-9:
        d = np.linalg.norm(pts - a, axis=1)
    else:
        d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / L
    i = int(np.argmax(d))
    if d[i] > tol:
        return np.concatenate([simplify(pts[:i + 1], tol)[:-1], simplify(pts[i:], tol)])
    return np.array([a, b])


def contours(n=(1300, 960), levels=(0.003, 0.03, 0.06, 0.088, 0.105, 0.14, 0.18), tol=0.0015, seg=0.03):
    """the depth map's contour lines at the given depths over the face's band, simplified, as polylines in
    (th, v)"""
    from skimage import measure
    th = np.linspace(-TH_F, TH_F, n[0])
    v = np.linspace(V_A, V_B, n[1])
    D = head_relief(*np.meshgrid(th, v))[0]
    out = []
    for lv in levels:
        for c in measure.find_contours(D, lv):
            pts = np.stack([th[0] + c[:, 1] * (th[1] - th[0]), v[0] + c[:, 0] * (v[1] - v[0])], 1)
            closed = np.linalg.norm(pts[0] - pts[-1]) < 1e-6
            pts = simplify(pts, tol)
            if len(pts) < 3 or (closed and len(pts) < 4):
                continue
            dense = [pts[0]]
            for p, q in zip(pts[:-1], pts[1:]):
                k = max(1, int(math.ceil(np.linalg.norm(q - p) / seg)))
                for t in range(1, k + 1):
                    dense.append(p + (q - p) * t / k)
            out.append(np.array(dense))
    return out


TH_FS = np.linspace(-TH_F, TH_F, 47)                       # the coarse rows and columns the game mesh is built on
TH_BS = np.linspace(TH_F, 2 * math.pi - TH_F, 29)
V_SS = np.linspace(V_A, V_B, 35)
CAP_RINGS = 4


def front_triangles():
    """the face's band triangulated so its edges follow the cut-in shapes' contour lines; a coarse grid fills the
    rest. In (th, v)"""
    import triangle
    lines = contours()
    pts, segs, index = [], [], {}

    def vid(p):                        # one vertex per position, however many lines pass through it
        key = (round(float(p[0]), 6), round(float(p[1]), 6))
        if key not in index:
            index[key] = len(pts)
            pts.append(key)
        return index[key]
    for line in lines:
        closed = np.linalg.norm(line[0] - line[-1]) < 1e-6
        ids = [vid(p) for p in (line[:-1] if closed else line)]
        pairs = list(zip(ids[:-1], ids[1:])) + ([(ids[-1], ids[0])] if closed else [])
        segs.extend((i, j) for i, j in pairs if i != j)
    near = np.array(pts) if pts else np.zeros((0, 2))
    for i, th in enumerate(TH_FS):
        for j, v in enumerate(V_SS):
            edge = i in (0, len(TH_FS) - 1) or j in (0, len(V_SS) - 1)
            if not edge and len(near) and np.min(np.hypot(near[:, 0] - th, near[:, 1] - v)) < 0.012:
                continue
            vid((th, v))
    segs = sorted(set(tuple(sorted(sg)) for sg in segs))
    t = triangle.triangulate({'vertices': np.array(pts), 'segments': np.array(segs)}, 'pc')
    return t['vertices'], t['triangles']


def grid_triangles(ths, vs):
    """a grid over (th, v) as triangles: its points and their indices"""
    T, V = np.meshgrid(ths, vs, indexing='ij')
    pts = np.stack([T.ravel(), V.ravel()], 1)
    nv = len(vs)
    tris = []
    for i in range(len(ths) - 1):
        for j in range(nv - 1):
            a, b, c, d = i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1
            tris += [(a, b, c), (a, c, d)]
    return pts, np.array(tris)


def cap_triangles(top):
    """the bottom (or top): rings in to its middle, as triangles over (th, v)"""
    ths = np.concatenate([TH_FS, TH_BS[1:]])
    if top:
        vs = np.linspace(V_B, V_END, CAP_RINGS + 1)
    else:
        vs = np.linspace(V_A, 0.0, CAP_RINGS + 1)
    pts, tris = grid_triangles(ths, vs[:-1])
    nv = len(vs) - 1
    extra = []
    for i in range(len(ths) - 1):          # the middle: one point for each triangle, at the angle between
        extra.append((0.5 * (ths[i] + ths[i + 1]), vs[-1]))
        tris = np.vstack([tris, [(i * nv + nv - 1, (i + 1) * nv + nv - 1, len(pts) + len(extra) - 1)]])
    return np.vstack([pts, extra]), tris


def build_game(scale, centre, name='Brute_Head'):
    """the game mesh: the face's band triangulated along the face's contours and cut in; the back of the band, the
    bottom and the top plain. One closed mesh, UV'd"""
    bm = bmesh.new()
    centre = Vector(centre)
    uvl = bm.loops.layers.uv.new('UVMap')
    parts = [(*front_triangles(), uv_front), (*grid_triangles(TH_BS, V_SS), uv_back),
             (*cap_triangles(False), uv_bottom), (*cap_triangles(True), uv_top)]
    for prm, tris, uv in parts:
        D = head_relief(prm[:, 0], prm[:, 1])[0]
        P, N = surface(prm[:, 0], prm[:, 1])
        P = P - N * D[:, None]
        vs = [bm.verts.new(Vector(p) * scale + centre) for p in P]
        for tri in tris:
            a, b, c = (prm[k] for k in tri)
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0:   # counter-clockwise faces out
                tri = tri[::-1]
            try:
                f = bm.faces.new([vs[i] for i in tri])
            except ValueError:
                continue
            f.smooth = True
            for loop, k in zip(f.loops, tri):
                loop[uvl].uv = uv(*prm[k])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5 * scale)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7 * scale)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ the detailed sculpt

def build_detail(scale, centre, n=1000, name='Brute_Head_High'):
    """the sculpt: a fine grid round the head (finest over the face) with every fold, crease and cut, painted
    (vertex colour 'Col', 'Rough') for baking"""
    ths = np.concatenate([np.linspace(-TH_F, TH_F, n + 1), np.linspace(TH_F, 2 * math.pi - TH_F, n // 8 + 1)[1:-1]])
    nb = int(round(n * (V_B - V_A) / (2 * TH_F)))
    vs = np.concatenate([np.linspace(0, V_A, 41)[1:-1], np.linspace(V_A, V_B, nb + 1),
                         np.linspace(V_B, V_END, 41)[1:-1]])
    TT, VV = np.meshgrid(ths, vs)                           # rows up the profile, columns round
    D, masks, X, Z = head_relief(TT, VV, detail=True)
    P0, N = surface(TT, VV)
    C, R = paint(X, Z, D, masks, P0)
    P = P0 - N * D[..., None]
    nt, nv = len(ths), len(vs)
    verts = np.concatenate([P.reshape(-1, 3), [(0, 0, -1), (0, 0, 1)]]) * scale + np.array(centre)
    cols = np.concatenate([C.reshape(-1, 3), skin(np.array([[0, 0, -1.0], [0, 0, 1.0]]))])
    rough = np.concatenate([R.ravel(), [0.78, 0.78]])
    J, I = np.meshgrid(np.arange(nv - 1), np.arange(nt), indexing='ij')
    I1 = (I + 1) % nt                                       # round the back and back to the start
    quads = np.stack([J * nt + I, J * nt + I1, (J + 1) * nt + I1, (J + 1) * nt + I], -1).reshape(-1, 4)
    i = np.arange(nt)
    bottom = np.stack([np.full(nt, nv * nt), (i + 1) % nt, i], -1)
    top = np.stack([np.full(nt, nv * nt + 1), (nv - 1) * nt + i, (nv - 1) * nt + (i + 1) % nt], -1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], quads.tolist() + bottom.tolist() + top.tolist())
    a = me.attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    a.data.foreach_set('color', np.c_[cols, np.ones(len(cols))].ravel())
    me.attributes.new('Rough', 'FLOAT', 'POINT').data.foreach_set('value', rough)
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ paint

SKIN_BASE = '#4c4846'


def hexlin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)


_NOISE = {}


def skin_noise(P, seed, cells, blur):
    """smooth noise through the head's volume (-1..1), so the skin's mottling runs on unbroken over its edges"""
    from scipy import ndimage as ndi
    key = (seed, cells, blur)
    if key not in _NOISE:
        g = ndi.gaussian_filter(np.random.default_rng(seed).standard_normal((cells,) * 3), blur, mode='wrap')
        _NOISE[key] = g / np.abs(g).max()
    idx = (np.asarray(P, float).reshape(-1, 3).T + 1.0) / 2.0 * (cells - 1)
    return ndi.map_coordinates(_NOISE[key], idx, order=1, mode='nearest').reshape(np.shape(P)[:-1])


def skin(P):
    """the bare skin's colour (linear) at points on the head: the grey mottled warmer and cooler, with darker
    blotches"""
    mott = 0.7 * skin_noise(P, 5, 40, 2.2) + 0.3 * skin_noise(P, 6, 96, 1.6)
    blot = skin_noise(P, 7, 64, 1.8)
    col = np.broadcast_to(hexlin(SKIN_BASE), mott.shape + (3,)).copy()
    for mask, colour, k in ((np.clip(mott * 2, 0, 1), '#554a46', 0.3), (np.clip(-mott * 2, 0, 1), '#393635', 0.3),
                            (smooth01((blot - 0.25) / 0.3), '#2e2a29', 0.25)):
        mk = mask[..., None] * k
        col = col * (1 - mk) + hexlin(colour) * mk
    return col


def paint(A, B, D, masks, P):
    """the front's colour (linear) and roughness: the skin, darkening the deeper it's cut, black in the eye
    pockets and the mouth, the teeth bone-yellow and grimy at their roots, dark lips, the cuts raw red"""
    rng = np.random.default_rng(5)
    from scipy import ndimage as ndi
    fine = ndi.gaussian_filter(rng.standard_normal(A.shape), 1.0)
    fine /= np.abs(fine).max()
    col = skin(P)
    rough = np.full(A.shape, 0.78)

    def put(mask, colour, k=1.0, r=None):
        nonlocal col, rough
        mk = np.clip(mask, 0, 1) * k
        col = col * (1 - mk[..., None]) + hexlin(colour) * mk[..., None]
        if r is not None:
            rough = rough * (1 - mk) + r * mk
    col *= (1 + 0.05 * fine)[..., None]
    # creases darker: from the depth map's curvature
    lap = ndi.laplace(ndi.gaussian_filter(D, 2.0))
    put(np.clip(lap * 1500, 0, 1), '#1c1a19', 0.35)
    put(np.clip(-lap * 1500, 0, 1), '#6a6461', 0.2)
    put(smooth01(D / 0.05) * (1 - masks['mouth']), '#0b0909', 0.93, 0.85)   # the sockets in shadow
    put(masks['eye'], '#050303', 1.0)
    put(masks['lip'] * (1 - masks['mouth']), '#262121', 0.6, 0.65)
    put(masks['mouth'], '#090505', 1.0, 0.9)
    tcol = hexlin('#bcab86')
    t = masks['teeth']
    col = col * (1 - t[..., None]) + tcol * t[..., None]
    rough = rough * (1 - t) + 0.38 * t
    root = np.maximum(smooth01((B + 0.625) / 0.03), smooth01((-0.81 - B) / 0.03))    # grime at the gums
    gaps = sum(np.exp(-((A - x) / 0.005) ** 2) for x in (-0.11, -0.02, 0.07)) * (B > -0.72)   # between teeth
    gaps = gaps + sum(np.exp(-((A - x) / 0.005) ** 2) for x in (-0.1, 0.0)) * (B < -0.75)
    put(t * np.clip(gaps, 0, 1), '#3a2e1e', 0.7)
    put(t * root, '#5a4a30', 0.8)
    fang = np.exp(-(((A + 0.222) / 0.045) ** 2)) + np.exp(-(((A - 0.285) / 0.055) ** 2))  # the fangs cleaner
    put(t * np.clip(fang, 0, 1) * (1 - root * 0.5), '#e6d8b4', 0.85)
    put(masks.get('scar', np.zeros(A.shape)), '#a1241a', 0.92, 0.5)
    return col, rough


# ------------------------------------------------------------------ the eyes

def eyes(scale, centre, name='Brute_Eyes'):
    """the glowing eyes: each a gently domed almond a little bigger than its opening, sat at the bottom of its
    socket, its rim tucked under the socket's floor"""
    import triangle
    bm = bmesh.new()
    centre = Vector(centre)
    for side in (-1, 1):
        poly = eye_poly(grow=0.012)
        n = len(poly)
        t = triangle.triangulate({'vertices': poly, 'segments': np.array([(k, (k + 1) % n) for k in range(n)])},
                                 'pqa0.0015')
        V2 = t['vertices']
        e = sd_poly(V2[:, 0], V2[:, 1], eye_poly(grow=0.012))
        depth = D_EYE + 0.004 - 0.022 * smooth01(-e / 0.07)
        X = -V2[:, 0] if side > 0 else V2[:, 0]          # drawn on the head's right, mirrored to its left
        P, N = surface(*front_param(X, V2[:, 1]))
        P = P - N * depth[:, None]
        vs = [bm.verts.new(Vector(p) * scale + centre) for p in P]
        for tri in t['triangles']:
            f = bm.faces.new([vs[i] for i in tri])
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:              # face out of the head
        if f.normal.y > 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.new(name='UVMap')
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ baking

def bake(lo, hi, out_dir, name='Brute_Head', res=1024, cage=0.03, reach=0.09):
    """the sculpt onto the game mesh: its normals, and its painted colour and roughness through an emission pass.
    Returns the three images (saved as <name>_Color / _Normal / _Roughness.png)"""
    import os
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    bk = sc.render.bake
    bk.margin = 6
    bk.use_clear = True
    bk.use_selected_to_active = True
    bk.cage_extrusion = cage
    bk.max_ray_distance = reach
    pm = bpy.data.materials.new('FacePaint')
    pm.use_nodes = True
    nt = pm.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    src = {}
    for ch, attr, sock in (('Color', 'Col', 'Color'), ('Roughness', 'Rough', 'Fac')):
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = attr
        src[ch] = at.outputs[sock]
    hi.data.materials.clear()
    hi.data.materials.append(pm)
    tm = bpy.data.materials.new('FaceTarget')
    tm.use_nodes = True
    tnode = tm.node_tree.nodes.new('ShaderNodeTexImage')
    tm.node_tree.nodes.active = tnode
    lo.data.materials.clear()
    lo.data.materials.append(tm)
    for o in bpy.data.objects:
        o.select_set(False)
    hi.select_set(True)
    lo.select_set(True)
    bpy.context.view_layer.objects.active = lo
    maps = {}
    os.makedirs(out_dir, exist_ok=True)
    for ch in ('Color', 'Roughness', 'Normal'):
        img = bpy.data.images.new(f'{name}_{ch}', res, res, alpha=False)
        img.colorspace_settings.name = 'sRGB' if ch == 'Color' else 'Non-Color'
        tnode.image = img
        if ch == 'Normal':
            sc.cycles.samples = 8
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=6, use_selected_to_active=True)
        else:
            nt.links.new(src[ch], em.inputs['Color'])
            sc.cycles.samples = 4
            bpy.ops.object.bake(type='EMIT', margin=6, use_selected_to_active=True)
        img.filepath_raw = os.path.join(out_dir, f'{name}_{ch}.png')
        img.file_format = 'PNG'
        img.save()
        maps[ch] = img
        print('BAKED', img.name, flush=True)
    hi.select_set(False)
    lo.select_set(False)
    return maps


def baked_material(name, maps):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = {}
    for ch, img in maps.items():
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img
        tex[ch] = t
    nt.links.new(tex['Color'].outputs[0], b.inputs['Base Color'])
    nt.links.new(tex['Roughness'].outputs[0], b.inputs['Roughness'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = 0.3
    return m
