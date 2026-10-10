"""The Dark Knight's bow, traced from bow_reference.jpg, and an arrow for it.

The bow is not modelled by hand: its silhouette is cut out of the reference painting, given depth by
swelling it from its edges inward (thickest in the middle of each limb and blade, tapering to the
edges), and the painting itself becomes its colour map, so it matches the image exactly -- the
stylised metal, the highlights and the purple inlays. Normal, roughness and metalness maps are derived
from the painting so it still catches light like metal in Roblox. The string is a separate mesh along
the painted string.

The arrow is modelled (in the painting it's wrapped in flames): barbed broadhead, banded shaft,
jagged fletching, in stylised purple, baked to the same four maps.

    python build_bow.py -- [--stage preview|all] [--out DIR]
    -> export/BowKit.fbx: Weapon_Bow  Weapon_BowString  Weapon_Arrow, plus each one's
       _Color / _Normal / _Roughness / _Metalness.png

The bow stands in the XZ plane, 5 studs tall, with the grip at the origin and the string vertical on
its +X side; the arrow points up +Z with its nock at the origin.
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as am

STAGE = am.opt('--stage', 'all')
RES = int(am.opt('--res', '1024'))
am.OUT = OUT = os.path.abspath(am.opt('--out', os.path.join(HERE, 'export')))
am.PARTS.clear()
am.PARTS.update({'Arrow': ((3, 0, 0), None)})
ARROW_X = 3.0   # where the arrow stands beside the bow in the previews (moved back to the origin on export)

REF = os.path.join(HERE, 'bow_reference.jpg')
STRING = ((800, 298), (160, 1000))   # the string's ends in the painting (px), found by fitting the line
STRING_STUDS = 4.0                   # how long the string is in Roblox: sets the bow's size
GRID = 4                             # px per mesh cell when tracing
MAX_TRIS = 17000
EMISSIVE_STRENGTH = 1.6              # for the previews; set SurfaceAppearance.EmissiveStrength to taste in Studio


# ------------------------------------------------------------------ shapes

def spline(ctrl, n):
    """n points along a Catmull-Rom curve through the control points (x, z)"""
    P = [Vector((x, 0, z)) for x, z in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    segs = len(P) - 3
    for k in range(n):
        t = k / (n - 1) * segs
        i = min(int(t), segs - 1)
        f = t - i
        p0, p1, p2, p3 = P[i:i + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out


def frames(pts):
    """tangent, side (always +Y: the bow is flat in XZ) and in-plane normal at each point"""
    out = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        s = Vector((0, 1, 0))
        n = t.cross(s).normalized()
        out.append((t, s, n))
    return out


def new_bm():
    bm = bmesh.new()
    return bm, bm.loops.layers.uv.new('UVMap'), bm.loops.layers.uv.new('Detail')


def face(bm, uvl, dtl, vs, uvs):
    try:
        f = bm.faces.new(vs)
    except ValueError:
        return
    for loop, uv in zip(f.loops, uvs):
        loop[uvl].uv = uv
        loop[dtl].uv = uv


def tube(part, mat, pts, radii, ring=12, offset=None, bevel=0, name='tube'):
    """a swept solid along pts: radii[i] = (half-width in Y, half-depth in the bow's plane);
    offset(i) shifts the section along the in-plane normal (for inlays riding on a limb's edge)"""
    fr = frames(pts)
    bm, uvl, dtl = new_bm()
    rings, length = [], [0.0]
    for i, p in enumerate(pts):
        if i:
            length.append(length[-1] + (p - pts[i - 1]).length)
        t, s, n = fr[i]
        c = p + n * (offset(i) if offset else 0.0)
        rw, rd = radii[i]
        rings.append([bm.verts.new(c + s * rw * math.cos(a) + n * rd * math.sin(a))
                      for a in (math.tau * k / ring for k in range(ring))])
    per = lambda i: math.pi * (radii[i][0] + radii[i][1])
    for i in range(len(pts) - 1):
        for k in range(ring):
            k2 = (k + 1) % ring
            face(bm, uvl, dtl, (rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]),
                 ((length[i], per(i) * k / ring), (length[i + 1], per(i + 1) * k / ring),
                  (length[i + 1], per(i + 1) * (k + 1) / ring), (length[i], per(i) * (k + 1) / ring)))
    for i, rev in ((0, True), (len(pts) - 1, False)):   # end caps
        vs = rings[i][::-1] if rev else rings[i]
        rw, rd = radii[i]
        face(bm, uvl, dtl, vs, [(0.5 * rw * math.cos(math.tau * k / ring), 0.5 * rd * math.sin(math.tau * k / ring))
                                for k in (range(ring)[::-1] if rev else range(ring))])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return am.finish(part, mat, bm, bevel, name)


def prism(part, mat, outline, origin=(0, 0, 0), ax_a=(1, 0, 0), ax_b=(0, 0, 1), thick=0.03, bevel=0.008, name='blade'):
    """a flat blade: the 2D outline (a, b) laid out on axes ax_a, ax_b from origin, thickness along their normal"""
    O, A, B = Vector(origin), Vector(ax_a), Vector(ax_b)
    Nrm = A.cross(B).normalized()
    bm, uvl, dtl = new_bm()
    pt = lambda a, b, h: O + A * a + B * b + Nrm * h
    lo = [bm.verts.new(pt(a, b, -thick / 2)) for a, b in outline]
    hi = [bm.verts.new(pt(a, b, thick / 2)) for a, b in outline]
    face(bm, uvl, dtl, hi, list(outline))
    face(bm, uvl, dtl, lo[::-1], [(a + 3, b) for a, b in outline[::-1]])
    run = 0.0
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        d = (Vector(outline[j]) - Vector(outline[i])).length
        face(bm, uvl, dtl, (lo[i], lo[j], hi[j], hi[i]), ((run, -thick), (run + d, -thick), (run + d, 0), (run, 0)))
        run += d
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return am.finish(part, mat, bm, bevel, name)


# ------------------------------------------------------------------ the arrow

def arrow():
    X = ARROW_X
    shaft = [Vector((X, 0, z)) for z in (0.0, 0.8, 1.6, 2.4, 2.62)]
    tube('Arrow', 'Glow', shaft, [(0.032, 0.032)] * 5, ring=12, name='shaft')
    for z0, z1 in ((0.04, 0.12), (0.72, 0.78), (2.48, 2.62)):   # steel bands: nock, behind the fletching, ferrule
        band = [Vector((X, 0, z)) for z in (z0, (z0 + z1) / 2, z1)]
        tube('Arrow', 'Steel', band, [(0.04, 0.04), (0.045, 0.045), (0.04, 0.04)], ring=12, bevel=0.004, name='band')
    tube('Arrow', 'Steel', [Vector((X, 0, z)) for z in (-0.06, -0.03, 0.0)], [(0.036, 0.036)] * 3, ring=12, name='nock')
    # barbed broadhead: two crossed blades, each with a pair of barbs
    head = [(0.0, 3.08), (0.15, 2.8), (0.07, 2.84), (0.14, 2.66), (0.035, 2.7), (0.035, 2.58),
            (-0.035, 2.58), (-0.035, 2.7), (-0.14, 2.66), (-0.07, 2.84), (-0.15, 2.8)]
    for ax in ((1, 0, 0), (0, 1, 0)):
        prism('Arrow', 'PurplePolish', head, origin=(X, 0, 0), ax_a=ax, ax_b=(0, 0, 1), thick=0.028, bevel=0.006,
              name='head')
    # three jagged feather vanes
    vane = [(0.03, 0.66), (0.06, 0.6), (0.12, 0.5), (0.1, 0.45), (0.15, 0.36), (0.13, 0.31), (0.17, 0.2),
            (0.13, 0.17), (0.12, 0.13), (0.03, 0.15)]
    for k in range(3):
        a = math.radians(90 + 120 * k)
        prism('Arrow', 'PurplePolish', vane, origin=(X, 0, 0), ax_a=(math.cos(a), math.sin(a), 0), ax_b=(0, 0, 1),
              thick=0.012, bevel=0.003, name='vane')



# ------------------------------------------------------------------ tracing the bow

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
    bg = ring[r]
    return img, lum, sat, bg


def bow_mask(img, lum, sat, bg):
    """the bow: everything the backdrop can't reach from the edges of the picture, minus real openings
    (the loop guard, gaps between blades), minus the string and the arrows"""
    H, W = lum.shape
    backdrop_like = (np.abs(lum - bg) <= 10) & (sat <= 16)
    lab, n = ndi.label(backdrop_like)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ~np.isin(lab, list(edge))
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    openings = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 500 and (i + 1) not in edge])
    fg &= ~openings
    # cut the string away (keeping its anchors at the tips)
    (ax, ay), (bx, by) = STRING
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.array([bx - ax, by - ay], float)
    L = np.linalg.norm(d)
    t = ((xx - ax) * d[0] + (yy - ay) * d[1]) / L ** 2
    dist = np.abs((xx - ax) * d[1] - (yy - ay) * d[0]) / L
    fg &= ~((dist < 3.5) & (t > 0.03) & (t < 0.97))
    fg = ndi.binary_opening(fg, iterations=1)
    L_, m = ndi.label(fg)
    left = [i for i in np.unique(L_[:, :120]) if i]           # the bow is the piece reaching the left edge
    bow = L_ == max(left, key=lambda i: (L_ == i).sum())
    return ndi.binary_fill_holes(bow) & ~openings


def frame():
    """painting px -> bow plane (x, z) in studs: string vertical, grip at the origin"""
    (ax, ay), (bx, by) = STRING
    a = np.array([ax, -ay], float)
    d = np.array([bx - ax, -(by - ay)], float)
    s = STRING_STUDS / np.linalg.norm(d)
    rot = -math.pi / 2 - math.atan2(d[1], d[0])
    c, sn = math.cos(rot), math.sin(rot)
    R = np.array([[c, -sn], [sn, c]])
    return lambda px, py: (R @ (np.stack([np.asarray(px, float), -np.asarray(py, float)]) - a[:, None])).T * s, s


def textures(img, lum, sat, mask, box):
    """colour from the painting itself (the backdrop filled in from the nearest bow pixel so nothing grey
    bleeds in at the edges); normal from the painting's shading; roughness and metalness by material"""
    y0, y1, x0, x1 = box
    S = max(y1 - y0, x1 - x0)
    sq = lambda a, fill: np.pad(a, ((0, S - (y1 - y0)), (0, S - (x1 - x0))) + ((0, 0),) * (a.ndim - 2),
                                constant_values=fill)
    m = mask[y0:y1, x0:x1]
    _, (iy, ix) = ndi.distance_transform_edt(~m, return_indices=True)
    col = img[y0:y1, x0:x1][iy, ix]
    L = col.mean(2) / 255.0
    sat_ = (col.max(2) - col.min(2)) / 255.0
    purple = (sat_ > 0.12) & (col[..., 2] > col[..., 1] + 12)
    # normal: the painting's light and shade read as relief (fine detail only; the shape is in the mesh)
    h = ndi.gaussian_filter(L, 1.0) - ndi.gaussian_filter(L, 6.0)
    gy, gx = np.gradient(h)
    k = 1.2
    nrm = np.dstack([-gx * k, gy * k, np.ones_like(h)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = nrm * 0.5 + 0.5
    # the purple inlays, softly: how purple each pixel is (saturated, blue above green)
    w = np.clip((sat_ - 0.07) / 0.1, 0, 1) * np.clip(((col[..., 2] - col[..., 1]) / 255.0 - 0.02) / 0.07, 0, 1)
    w = ndi.gaussian_filter(w, 0.7) * m
    # a gradient along the bow: deep violet at the grip, vivid purple, light lavender at the tips...
    (ax, ay), (bx, by) = STRING
    yy, xx = np.mgrid[y0:y1, x0:x1]
    t = ((xx - ax) * (bx - ax) + (yy - ay) * (by - ay)) / float((bx - ax) ** 2 + (by - ay) ** 2)
    g = np.clip(np.abs(t - 0.5) * 2, 0, 1)
    stops = np.array([[0.22, 0.04, 0.58], [0.52, 0.14, 1.0], [0.82, 0.38, 1.0]])
    ramp = np.where((g < 0.5)[..., None], stops[0] + (stops[1] - stops[0]) * (g / 0.5)[..., None],
                    stops[1] + (stops[2] - stops[1]) * ((g - 0.5) / 0.5)[..., None])
    # ...and across each inlay: a bright core fading to its edges
    core = np.clip(ndi.distance_transform_edt(w > 0.5) / 3.0, 0, 1)
    shade = 0.5 + 0.5 * L                       # keep the painting's light and shade on top
    tinted = np.clip(ramp * shade[..., None] + core[..., None] * 0.08, 0, 1)
    col = col / 255.0 * (1 - w[..., None]) + tinted * w[..., None]
    emissive = w * (0.5 + 0.5 * core)           # glow: where the purple is, strongest along the cores
    rough = np.clip(0.48 - 0.22 * L, 0.18, 0.6)
    rough[purple] = 0.3
    metal = np.where(purple, 0.2, 0.38)
    maps = {'Color': sq(col, 0.0), 'Normal': sq(nrm, 0.5), 'Roughness': sq(rough, 0.5), 'Metalness': sq(metal, 0.5),
            'Emissive': sq(emissive, 0.0)}
    out = {}
    for ch, a in maps.items():
        a = np.clip(a, 0, 1)
        if a.ndim == 2:
            a = np.dstack([a] * 3)
        pim = Image.fromarray((a * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
        path = os.path.join(OUT, f'Weapon_Bow_{ch}.png')
        pim.save(path)
        out[ch] = path
    return out, S


def bow_mesh(mask, box, S):
    """the traced silhouette as a solid: a grid of cells inside the outline, front and back faces swollen
    apart by the distance to the edge (so limbs and blades are thickest along their middles), joined by a
    thin rim, the stair-stepped outline smoothed, then reduced to fit Roblox's triangle limit"""
    y0, y1, x0, x1 = box
    to_plane, s = frame()
    dist = ndi.distance_transform_edt(mask)
    H, W = mask.shape
    g = GRID
    ys = list(range(y0, y1 + 1, g))
    xs = list(range(x0, x1 + 1, g))
    inside = {}
    for j, y in enumerate(ys[:-1]):
        for i, x in enumerate(xs[:-1]):
            cy, cx = min(y + g // 2, H - 1), min(x + g // 2, W - 1)
            if mask[cy, cx]:
                inside[(i, j)] = True
    nodes = {}
    for (i, j) in inside:
        for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nodes[(i + di, j + dj)] = None
    # outline edges: a cell side with the cell inside and its neighbour outside
    edges = []
    for (i, j) in inside:
        for (di, dj), (a, b) in (((0, -1), ((i, j), (i + 1, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))),
                                 ((0, 1), ((i + 1, j + 1), (i, j + 1))), ((-1, 0), ((i, j + 1), (i, j)))):
            if (i + di, j + dj) not in inside:
                edges.append((a, b))
    pos = {k: np.array([xs[k[0]] if k[0] < len(xs) else xs[-1] + g, ys[k[1]] if k[1] < len(ys) else ys[-1] + g], float)
           for k in nodes}
    nbr = {}
    for a, b in edges:
        nbr.setdefault(a, []).append(b)
        nbr.setdefault(b, []).append(a)
    for _ in range(4):   # smooth the stair-stepped outline
        new = {k: pos[k] * 0.5 + 0.5 * np.mean([pos[q] for q in v], 0) for k, v in nbr.items()}
        pos.update(new)
    def thick(k):
        px, py = pos[k]
        d = dist[int(min(max(py, 0), H - 1)), int(min(max(px, 0), W - 1))]
        if k in nbr:
            d = 0.0
        return 0.006 + 0.05 * min(1.0, d / 14.0) ** 0.7
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    front, back, uv = {}, {}, {}
    for k in nodes:
        px, py = pos[k]
        (X, Z), = to_plane([px], [py])
        h = thick(k)
        front[k] = bm.verts.new((X, -h, Z))
        back[k] = bm.verts.new((X, h, Z))
        uv[k] = ((px - x0) / S, 1 - (py - y0) / S)
    def quad(vs, ks):
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for loop, k in zip(f.loops, ks):
            loop[uvl].uv = uv[k]
    for (i, j) in inside:
        ks = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        quad([front[k] for k in ks], ks)
        quad([back[k] for k in ks[::-1]], ks[::-1])
    for a, b in edges:
        quad([front[a], front[b], back[b], back[a]], [a, b, b, a])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Weapon_Bow')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('Weapon_Bow', me)
    bpy.context.scene.collection.objects.link(ob)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    if tris > MAX_TRIS:
        md = ob.modifiers.new('fit', 'DECIMATE')
        md.ratio = MAX_TRIS / tris
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear()
        ob.data = me2
    am.smooth(ob.data)
    return ob, to_plane


def texture_material(name, paths):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    t = {}
    for ch, p in paths.items():
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(p)
        if ch != 'Color':
            n.image.colorspace_settings.name = 'Non-Color'
        t[ch] = n
    nt.links.new(t['Color'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(t['Roughness'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(t['Metalness'].outputs[0], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(t['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    if 'Emissive' in t:   # glow: the colour map, wherever the emissive mask says (as Roblox does it)
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        nt.links.new(t['Color'].outputs[0], mul.inputs[6])
        nt.links.new(t['Emissive'].outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = EMISSIVE_STRENGTH
    return m


def bow_string(img, lum, sat, bg, to_plane):
    """a thin cord between the painted string's ends, in the string's own colour"""
    (ax, ay), (bx, by) = STRING
    t = np.linspace(0.1, 0.9, 400)
    xs_, ys_ = (ax + (bx - ax) * t).astype(int), (ay + (by - ay) * t).astype(int)
    samples = img[ys_, xs_]
    sel = (samples.max(1) - samples.min(1)) > 12
    colour = samples[sel].mean(0) / 255.0 if sel.any() else np.array([0.62, 0.5, 0.85])
    (X0, Z0), (X1, Z1) = to_plane([ax, bx], [ay, by])
    pts = [Vector((X0 + (X1 - X0) * k / 10, 0, Z0 + (Z1 - Z0) * k / 10)) for k in range(11)]
    ob = tube('BowString', 'Glow', pts, [(0.014, 0.014)] * 11, ring=8, name='Weapon_BowString')
    am.PIECES.remove(('BowString', ob))
    ob.name = 'Weapon_BowString'
    flat = {'Color': np.dstack([np.full((64, 64), c) for c in colour]), 'Normal': np.dstack([np.full((64, 64), v) for v in (0.5, 0.5, 1.0)]),
            'Roughness': np.full((64, 64, 3), 0.35), 'Metalness': np.full((64, 64, 3), 0.3),
            'Emissive': np.full((64, 64, 3), 0.8)}
    paths = {}
    for ch, a in flat.items():
        p = os.path.join(OUT, f'Weapon_BowString_{ch}.png')
        Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(p)
        paths[ch] = p
    return ob, paths



# ------------------------------------------------------------------ build, preview, export

def build_bow():
    img, lum, sat, bg = load_reference()
    mask = bow_mask(img, lum, sat, bg)
    ys, xs = np.nonzero(mask)
    pad = 8
    box = (max(ys.min() - pad, 0), min(ys.max() + pad, mask.shape[0]), max(xs.min() - pad, 0), min(xs.max() + pad, mask.shape[1]))
    paths, S = textures(img, lum, sat, mask, box)
    bow, to_plane = bow_mesh(mask, box, S)
    bow.data.materials.append(texture_material('Weapon_Bow', paths))
    string, spaths = bow_string(img, lum, sat, bg, to_plane)
    string.data.materials.clear()
    string.data.materials.append(texture_material('Weapon_BowString', spaths))
    # grip at the origin: the point of the bow farthest from the string
    verts = [v.co for v in bow.data.vertices]
    sx = min(v.co.x for v in string.data.vertices)
    far = max(verts, key=lambda v: abs(v.x - sx))
    grip = Matrix.Translation((-far.x, 0, -far.z))
    for ob in (bow, string):
        ob.data.transform(grip)
    return bow, string


def build_arrow():
    am.HIGH[0] = False
    arrow()
    low = am.join_parts('Weapon_')
    am.PIECES.clear()
    am.HIGH[0] = True
    arrow()
    high = am.join_parts('High_')
    am.HIGH[0] = False
    return low, high


def preview(path, samples=48):
    sc, cam, cam_d = am.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 1000, 1100
    cam_d.lens = 50
    for i, (loc, tgt) in enumerate((((1.0, -12.0, 0.0), (1.0, 0, 0.0)), ((5.5, -8.5, 2.0), (0.6, 0, 0.0)))):
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path.replace('.png', f'_{i}.png') if i else path
        bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def export(objs):
    for o in bpy.data.objects:
        o.select_set(False)
    for ob in objs:
        ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'BowKit.fbx'), use_selection=True, object_types={'MESH'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True,
                             path_mode='STRIP')
    print('EXPORTED', os.path.join(OUT, 'BowKit.fbx'), flush=True)


def main():
    am.reset()
    os.makedirs(OUT, exist_ok=True)
    am.materials()
    am.mk_material('Glow', 'purple', '#9a63e8', '#8550d6', '#e2ccff', (0.22, 0.32), 0.6, groove_col='#2a1048',
                   engraved=False)
    bow, string = build_bow()
    low, high = build_arrow()
    arrow_ob = low['Arrow']
    for ob in (bow, string, arrow_ob, high['Arrow']):
        print(ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), flush=True)
    if STAGE == 'preview':
        arrow_ob.hide_render = True
        preview(os.path.join(OUT, 'preview.png'), samples=32)
        return
    maps = am.bake(low, high, RES)
    am.baked_materials(low, maps)
    preview(os.path.join(OUT, 'preview.png'))
    arrow_ob.data.transform(Matrix.Translation((-ARROW_X, 0, 0)))   # back to the origin
    export([bow, string, arrow_ob])


main()
