"""The Brute: an original hulking barbarian for the Roblox R6 rig.

A muscle-sculpted body over each R6 part (one mesh per part, so it moves with R6 animations), iron cuffs, a war-belt
and loincloth, a wild mane rigged for Smart Bones, and a separate iron cleaver with its own PBR maps.

The body is built as a smooth shell round each R6 block (a rounded box, a clean quad grid closing to a pole on top
and bottom), pushed out along its normal by the muscles: each muscle is a soft-edged ellipsoid, and where two meet
the shell takes the higher of the two, so a crease forms between them like real muscle definition.

    python build_brute.py -- --stage blocking|muscles|preview|all [--res 1024]
    step snapshots (clay + wireframe) land in export/steps/
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as A                 # noqa: E402
from build_armor import lin, TAU        # noqa: E402

STAGE = A.STAGE
RES = A.RES
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
STEPS = os.path.join(OUT, 'steps')
BODY = A.PARTS
A.PARTS = PARTS = {'Torso': ((0, 0, 3), None), 'LeftArm': ((1.5, 0, 3), None), 'RightArm': ((-1.5, 0, 3), None),
                   'LeftLeg': ((0.5, 0, 1), None), 'RightLeg': ((-0.5, 0, 1), None)}
MATS, HIGH = A.MATS, A.HIGH


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


# ------------------------------------------------------------------ the shell

OFFSET = 0.05      # the shell sits this far outside the R6 block, so its rounded edges still cover the block's corners
EDGE_R = 0.12      # rounding of the top and bottom edges
CORNER_R = 0.15    # rounding of the vertical edges


def rr_ring(u, hw, hd, r):
    """point u (0..1, evenly by length) round a rounded rectangle, starting at the front middle"""
    r = max(min(r, hw - 1e-3, hd - 1e-3), 1e-3)
    half = 2 * (hw - r) + 2 * (hd - r) + math.pi * r
    x, y = A.rr_point(-half + 2 * half * u, hw, hd, r)
    return x, y


def shell_rows(hz, spacing):
    """the shell's meridian, bottom pole to top pole: (kind, value) rows spaced about `spacing` apart"""
    rows = []
    nflat = 4
    for i in range(nflat + 1):                         # the bottom face, from its middle outward
        rows.append(('cap', -1, i / nflat))
    nroll = 4
    for i in range(1, nroll + 1):                      # round the bottom edge
        rows.append(('roll', -1, (i / nroll) * math.pi / 2))
    side = 2 * (hz - EDGE_R)
    ns = max(2, int(round(side / spacing)))
    for i in range(1, ns):
        rows.append(('side', 0, -1 + 2 * i / ns))
    for i in range(nroll, 0, -1):                      # round the top edge
        rows.append(('roll', 1, (i / nroll) * math.pi / 2))
    for i in range(nflat, -1, -1):                     # the top face, in to its middle
        rows.append(('cap', 1, i / nflat))
    return rows


def base_point(c, h, row, u):
    """a point on the plain rounded box (no muscles)"""
    kind, sgn, q = row
    hx, hy, hz = h
    if kind == 'cap':       # flat face: rings shrinking to the middle
        x, y = rr_ring(u, hx - EDGE_R, hy - EDGE_R, CORNER_R - EDGE_R + 0.02)
        return Vector((c[0] + x * q, c[1] + y * q, c[2] + sgn * hz))
    if kind == 'roll':      # the rounded edge: q from 0 (on the face) to pi/2 (on the side)
        inset = EDGE_R * (1 - math.sin(q))
        z = c[2] + sgn * (hz - EDGE_R + EDGE_R * math.cos(q))
        x, y = rr_ring(u, hx - inset, hy - inset, CORNER_R - inset)
        return Vector((c[0] + x, c[1] + y, z))
    z = c[2] + q * (hz - EDGE_R)
    x, y = rr_ring(u, hx, hy, CORNER_R)
    return Vector((c[0] + x, c[1] + y, z))


MASS = 1.4   # how much everything bulges: a heavyweight


def perim_half(h):
    hw, hd, r = h[0], h[1], CORNER_R
    return 2 * (hw - r) + 2 * (hd - r) + math.pi * r


def row_height(c, h, row):
    """where a shell row sits on the unfolded map: its height up the side, carried on over the top and bottom faces
    (so a muscle drawn above the top edge lies on the top face, running in toward its middle)"""
    kind, sgn, q = row
    top = h[2] - EDGE_R
    if kind == 'side':
        return c[2] + q * top
    roll = EDGE_R * math.pi / 2
    inward = min(h[0], h[1]) - EDGE_R
    if kind == 'roll':
        return c[2] + sgn * (top + EDGE_R * (math.pi / 2 - q))
    return c[2] + sgn * (top + roll + inward * (1 - q))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = clamp(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def inside_poly(px, py, poly):
    hit = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def muscle_height(s_, z, period, muscles):
    """the muscles' height at (s, z) on the unfolded map. Each muscle is an outline with a firm, slightly domed
    plateau and a rounded edge falling to nothing at its border, so where two meet a clean groove parts them"""
    d = 0.0
    for poly, H, w in muscles:
        for s2 in (s_, s_ + 2 * period, s_ - 2 * period):    # the map wraps round at the back
            if not inside_poly(s2, z, poly):
                continue
            e = min(seg_dist(s2, z, *poly[i], *poly[(i + 1) % len(poly)]) for i in range(len(poly)))
            x = clamp(e / w)
            dome = 0.82 + 0.18 * clamp(e / (3 * w))
            d = max(d, H * MASS * (1 - (1 - x) ** 2) * dome)
    return d


def body_part(part, c, size, muscles, spacing, name):
    """the skin over one R6 block: a rounded box OFFSET outside it, pushed out along its normal by the muscles"""
    h = tuple(s / 2 + OFFSET for s in size)
    rows = shell_rows(h[2], spacing)
    half = perim_half(h)
    nu = max(16, int(round(2 * half / spacing / 4)) * 4)
    us = [i / nu for i in range(nu + 1)]

    def fn(u, j):
        p = base_point(c, h, rows[j], u)
        pu = base_point(c, h, rows[j], (u + 1e-3) % 1.0) - base_point(c, h, rows[j], (u - 1e-3) % 1.0)
        a, b = rows[max(j - 1, 0)], rows[min(j + 1, len(rows) - 1)]
        pv = base_point(c, h, b, u) - base_point(c, h, a, u)
        n = pu.cross(pv)
        if n.length < 1e-9:
            n = Vector((0, 0, rows[j][1] or 1))
        n.normalize()
        if n.dot(p - Vector(c)) < 0:
            n = -n
        s_ = (2 * u - 1) * half          # round the part from its front middle: + toward +X, the back at +-half
        return tuple(p + n * muscle_height(s_, row_height(c, h, rows[j]), half, muscles))
    return surface(part, 'Skin', fn, us, list(range(len(rows))), closed_u=True, out=lambda p: c, name=name)


def surface(part, mat, fn, us, vs, closed_u=False, closed_v=False, out=None, name='surface'):
    """a single-walled quad grid over fn(u, v) at the given u and v positions; out(p): a point it faces away from.
    UVs in studs: U along u, V along v"""
    bm = bmesh.new()
    uvl, dtl = bm.loops.layers.uv.new('UVMap'), bm.loops.layers.uv.new('Detail')
    nu, nv = len(us) - 1, len(vs) - 1
    cols, rows = (nu if closed_u else nu + 1), (nv if closed_v else nv + 1)
    P = [[Vector(fn(us[i], vs[j])) for j in range(nv + 1)] for i in range(nu + 1)]
    V = [[bm.verts.new(P[i][j]) for j in range(rows)] for i in range(cols)]
    U = [[0.0] * (nv + 1) for _ in range(nu + 1)]
    W = [[0.0] * (nv + 1) for _ in range(nu + 1)]
    for j in range(nv + 1):
        for i in range(1, nu + 1):
            U[i][j] = U[i - 1][j] + (P[i][j] - P[i - 1][j]).length
    for i in range(nu + 1):
        for j in range(1, nv + 1):
            W[i][j] = W[i][j - 1] + (P[i][j] - P[i][j - 1]).length
    for i in range(nu):
        for j in range(nv):
            ids = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            try:
                f = bm.faces.new([V[a % cols][b % rows] for a, b in ids])
            except ValueError:
                continue
            f.smooth = True
            for loop, (a, b) in zip(f.loops, ids):
                loop[uvl].uv = loop[dtl].uv = (U[a][b], W[a][b])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if out is not None:
        bm.normal_update()
        score = sum(f.normal.dot(f.calc_center_median() - Vector(out(f.calc_center_median()))) for f in bm.faces)
        if score < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    return A.finish(part, mat, bm, 0, name)


# ------------------------------------------------------------------ the muscles, traced from the reference
#
# Drawn on each part's unfolded surface: s runs round the part from its front middle (+ toward +X, the back middle
# at +-half the way round), z is height, carried on over the top and bottom faces. The torso's map: its front runs
# to s 0.9, the corner to 1.14, the side to 1.94, the corner to 2.17, the back to its middle at 3.07; above z 4.05
# is its top face. The arms' and legs': front to 0.4, corner to 0.64, side to 1.44, corner to 1.67, back middle 2.07.
# Each muscle: (outline, height, edge softness).

def mirror(muscles):
    return muscles + [([(-x, z) for x, z in reversed(poly)], H, w) for poly, H, w in muscles]


B = 3.072   # the torso's back middle


def back(x):   # the torso's back face: s at a given x
    return B - x


TORSO = mirror([
    # pecs: a heavy wedge from the sternum out to the armpit, square along the bottom
    ([(0.035, 3.97), (0.95, 4.0), (1.08, 3.55), (0.84, 3.2), (0.25, 3.16), (0.035, 3.26)], 0.24, 0.16),
    # abs: four blocks a side, the lowest smallest
    ([(0.035, 3.12), (0.4, 3.12), (0.42, 2.9), (0.035, 2.89)], 0.1, 0.07),
    ([(0.035, 2.86), (0.42, 2.87), (0.42, 2.64), (0.035, 2.63)], 0.1, 0.07),
    ([(0.035, 2.6), (0.42, 2.61), (0.41, 2.38), (0.035, 2.37)], 0.1, 0.07),
    ([(0.035, 2.34), (0.4, 2.35), (0.36, 2.12), (0.035, 2.08)], 0.08, 0.07),
    # obliques, with the serratus fingers up under the pec
    ([(0.46, 3.12), (0.84, 3.14), (1.1, 3.0), (1.12, 2.4), (0.78, 2.16), (0.46, 2.3)], 0.12, 0.12),
    ([(0.86, 3.17), (1.1, 3.27), (1.12, 3.06), (0.9, 3.0)], 0.07, 0.05),
    # the lats where they show at the side
    ([(1.14, 3.62), (1.92, 3.68), (2.12, 3.25), (1.92, 2.78), (1.14, 2.92)], 0.13, 0.15),
    # traps: over the top face from the neck to the shoulder, and down the upper back
    ([(0.15, 4.12), (0.95, 4.08), (1.1, 4.3), (0.25, 4.5)], 0.18, 0.14),
    ([(B, 3.45), (back(0.5), 3.62), (back(0.85), 3.95), (back(0.95), 4.3), (B, 4.5)], 0.2, 0.15),
    # the back: rear shoulder blade, rhomboid, lats, the erectors either side of the spine, the top of the glutes
    ([(back(0.98), 3.9), (back(0.52), 3.86), (back(0.46), 3.46), (back(0.82), 3.32), (back(1.0), 3.48)], 0.15, 0.12),
    ([(back(0.45), 3.56), (back(0.035), 3.6), (back(0.035), 3.3), (back(0.45), 3.26)], 0.1, 0.09),
    ([(back(1.05), 3.4), (back(0.5), 3.22), (back(0.13), 3.06), (back(0.17), 2.76), (back(0.66), 2.76), (back(1.05), 2.92)],
     0.16, 0.14),
    ([(back(0.16), 3.1), (back(0.035), 3.1), (back(0.035), 2.25), (back(0.4), 2.25), (back(0.42), 2.7)], 0.12, 0.1),
    ([(back(0.9), 2.42), (back(0.035), 2.46), (back(0.035), 1.95), (back(0.9), 1.95)], 0.1, 0.12),
])

ARM = [   # the left arm (+X): s 0 its front middle, + round its outer side, - round its inner side
    # deltoid: three heads capping the shoulder, coming to a point down the outer side
    ([(-0.6, 3.7), (-0.2, 3.62), (0.62, 3.4), (0.62, 4.75), (-0.6, 4.75)], 0.24, 0.16),
    ([(0.58, 3.4), (1.0, 3.28), (1.42, 3.4), (1.42, 4.75), (0.58, 4.75)], 0.26, 0.16),
    ([(1.38, 3.42), (1.9, 3.55), (2.5, 3.72), (2.5, 4.75), (1.38, 4.75)], 0.22, 0.16),
    ([(-2.08, 3.9), (-1.0, 3.92), (-0.56, 3.75), (-0.56, 4.75), (-2.08, 4.75)], 0.12, 0.14),
    # biceps, and the brachialis beside it
    ([(-0.38, 3.56), (0.3, 3.5), (0.47, 3.2), (0.32, 2.85), (-0.3, 2.85), (-0.46, 3.2)], 0.22, 0.15),
    ([(0.5, 3.32), (0.92, 3.22), (1.02, 2.76), (0.62, 2.72), (0.48, 3.0)], 0.12, 0.1),
    # triceps: the long head down the back, the inner head
    ([(1.12, 3.36), (1.75, 3.45), (2.5, 3.5), (2.5, 2.85), (1.6, 2.8), (1.12, 2.95)], 0.2, 0.15),
    ([(-2.08, 3.62), (-1.45, 3.55), (-1.4, 2.95), (-2.08, 2.9)], 0.14, 0.12),
    # forearm: extensors round the outside, flexors round the front and inside
    ([(0.48, 2.7), (1.42, 2.74), (1.5, 2.3), (0.5, 2.28)], 0.14, 0.12),
    ([(-0.92, 2.8), (0.42, 2.76), (0.44, 2.28), (-0.92, 2.3)], 0.13, 0.12),
    ([(1.52, 2.78), (2.5, 2.78), (2.5, 2.3), (1.55, 2.28)], 0.1, 0.1),
    ([(-2.08, 2.8), (-0.98, 2.82), (-0.98, 2.3), (-2.08, 2.3)], 0.1, 0.1),
    # the fist: knuckles across the front, the thumb on the inside
    ([(-0.38, 2.2), (-0.2, 2.2), (-0.2, 2.07), (-0.38, 2.07)], 0.05, 0.04),
    ([(-0.17, 2.21), (0.0, 2.21), (0.0, 2.07), (-0.17, 2.07)], 0.05, 0.04),
    ([(0.03, 2.21), (0.2, 2.21), (0.2, 2.07), (0.03, 2.07)], 0.05, 0.04),
    ([(0.23, 2.2), (0.38, 2.2), (0.38, 2.07), (0.23, 2.07)], 0.05, 0.04),
    ([(-0.85, 2.32), (-0.6, 2.3), (-0.58, 2.08), (-0.85, 2.1)], 0.08, 0.05),
]

LEG = [   # the left leg (+X): s 0 its front middle, + round its outer side
    ([(0.15, 1.96), (0.78, 1.88), (0.92, 1.3), (0.6, 1.05), (0.25, 1.25)], 0.18, 0.15),     # quads: outer
    ([(-0.22, 1.96), (0.12, 1.96), (0.2, 1.25), (0.0, 1.1), (-0.16, 1.3)], 0.16, 0.13),     # the middle
    ([(-0.47, 1.42), (-0.13, 1.3), (-0.06, 1.0), (-0.3, 0.94), (-0.52, 1.1)], 0.16, 0.12),  # the teardrop
    ([(-0.5, 1.96), (-1.15, 1.96), (-1.05, 1.42), (-0.52, 1.46)], 0.1, 0.12),               # adductors
    ([(-0.14, 0.99), (0.2, 0.99), (0.18, 0.86), (-0.12, 0.86)], 0.05, 0.04),                # kneecap
    ([(1.45, 1.66), (1.95, 1.66), (1.95, 1.12), (1.5, 1.08)], 0.15, 0.13),                  # hamstrings
    ([(2.0, 1.66), (2.5, 1.66), (2.45, 1.08), (2.0, 1.1)], 0.15, 0.13),
    ([(1.0, 2.0), (3.15, 2.0), (3.15, 1.62), (1.1, 1.7)], 0.18, 0.15),                      # glute
    ([(1.3, 0.96), (1.95, 0.96), (1.92, 0.46), (1.45, 0.5)], 0.2, 0.13),                     # calves
    ([(2.0, 0.96), (2.62, 0.96), (2.52, 0.5), (2.02, 0.45)], 0.2, 0.13),
    ([(0.6, 0.92), (1.26, 0.92), (1.22, 0.42), (0.66, 0.42)], 0.12, 0.12),                  # outer calf
    ([(0.14, 0.86), (0.45, 0.86), (0.45, 0.3), (0.2, 0.3)], 0.08, 0.08),                    # shin
] + [([(x - 0.075, 0.15), (x + 0.075, 0.15), (x + 0.075, -0.02), (x - 0.075, -0.02)], 0.06, 0.04)
     for x in (-0.36, -0.18, 0.0, 0.17, 0.33)]                                              # toes


def body(stage):
    """stage 'blocking': the plain shells; 'muscles': sculpted"""
    sp = 0.05 if HIGH[0] else 0.07
    m = (lambda ms: ms) if stage != 'blocking' else (lambda ms: [])
    body_part('Torso', (0, 0, 3), (2, 1, 2), m(TORSO), sp, 'skin')
    body_part('LeftArm', (1.5, 0, 3), (1, 1, 2), m(ARM), sp, 'skin')
    body_part('LeftLeg', (0.5, 0, 1), (1, 1, 2), m(LEG), sp, 'skin')
    A.mirror_left_to_right()


# ------------------------------------------------------------------ materials

def clay():
    m = bpy.data.materials.new('Skin')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin('#5b4f4a')
    b.inputs['Roughness'].default_value = 0.55
    MATS['Skin'] = m


# ------------------------------------------------------------------ step snapshots

def snapshot(name, objs, wire=True):
    """a viewport-style render of the build so far: clay, with the wireframe drawn over it"""
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = 16
    sc.render.resolution_x, sc.render.resolution_y = 1400, 760
    extra = []
    if wire:
        black = bpy.data.materials.get('WireLine') or bpy.data.materials.new('WireLine')
        black.use_nodes = True
        nt = black.node_tree
        nt.nodes.clear()
        o = nt.nodes.new('ShaderNodeOutputMaterial')
        e = nt.nodes.new('ShaderNodeEmission')
        e.inputs[0].default_value = (0.02, 0.02, 0.02, 1)
        nt.links.new(e.outputs[0], o.inputs[0])
        for ob in objs:
            w = ob.copy()
            w.data = ob.data.copy()
            bpy.context.scene.collection.objects.link(w)
            md = w.modifiers.new('w', 'WIREFRAME')
            md.thickness = 0.006
            md.use_replace = True
            w.data.materials.clear()
            w.data.materials.append(black)
            extra.append(w)
    os.makedirs(STEPS, exist_ok=True)
    head = load_head()
    shots = []
    for i, az in enumerate((-25, 155)):
        a = math.radians(az - 90)
        cam_d.lens = 70
        cam.location = (15 * math.cos(a), 15 * math.sin(a), 4.2)
        cam.rotation_euler = (Vector((0, 0, 2.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = 700, 760
        f = os.path.join(STEPS, f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    import numpy as np
    ims = [bpy.data.images.load(f) for f in shots]
    W, H = ims[0].size
    strip = np.zeros((H, W * 2, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        strip[:, k * W:(k + 1) * W] = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
    out = bpy.data.images.new(name, W * 2, H, alpha=False)
    out.pixels = strip.ravel()
    out.filepath_raw = os.path.join(STEPS, name + '.png')
    out.file_format = 'PNG'
    out.save()
    for f in shots:
        os.remove(f)
    for w in extra + [head]:
        bpy.data.objects.remove(w)
    print('STEP', out.filepath_raw, flush=True)


def load_head():
    """the R6 head, for scale in the snapshots (the player's own head is used in game)"""
    A.PARTS = BODY
    refs = A.load_rig()
    A.PARTS = PARTS
    for k, o in list(refs.items()):
        if k != 'Head':
            bpy.data.objects.remove(o)
    h = refs['Head']
    h.data.materials.clear()
    h.data.materials.append(MATS['Skin'])
    return h


def main():
    A.reset()
    clay()
    A.PIECES.clear()
    if STAGE in ('blocking', 'muscles'):
        body(STAGE)
        objs = [ob for p, ob in A.PIECES]
        for p, ob in A.PIECES:
            print(p, ob.name, 'tris', sum(len(f.vertices) - 2 for f in ob.data.polygons))
        snapshot('step_01_blocking' if STAGE == 'blocking' else 'step_02_muscles', objs)
        return


if __name__ == '__main__':
    main()
