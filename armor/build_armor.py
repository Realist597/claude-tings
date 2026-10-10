"""Dark knight armour for a Roblox R6 character, in black steel with purple metal trim.

Builds every piece procedurally, fitted to the R6 body in r6_rig_body.fbx (1 unit = 1 stud, Z up,
the character faces -Y). Pieces are joined into one mesh per body part, so each one welds to a
single part in Roblox:
    Armor_Head  Armor_Torso  Armor_LeftArm  Armor_RightArm  Armor_LeftLeg  Armor_RightLeg
    Armor_Cape  Armor_Tabard  Armor_SkirtBack (cloth with bones, each welded to the torso)

Surfaces are procedural Cycles materials (blackened steel, purple metal, black leather, purple
cloth) baked down to PBR maps per mesh for Roblox SurfaceAppearance:
    <Mesh>_Color.png  <Mesh>_Normal.png (OpenGL / +Y)  <Mesh>_Roughness.png  <Mesh>_Metalness.png

    blender -b --factory-startup --python build_armor.py -- [--stage preview|bake|all] [--res 1024] [--out DIR]
    (or: python build_armor.py ...  with the pip `bpy` module)

    preview    build the meshes and render preview.png with the live procedural materials (fast)
    timelapse  film the armour being put together piece by piece (build_timelapse.mp4)
    live       open Blender's window and watch it being built piece by piece in the viewport:
                 blender --python build_armor.py -- --stage live
    bake     build, UV, bake the maps, render preview.png with the baked maps, export ArmorKit.fbx
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]


def opt(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


STAGE = opt('--stage', 'all')
ONLY = opt('--only', '')   # bake / preview just this body part (for quick tests)
RES = int(opt('--res', '1024'))
OUT = os.path.abspath(opt('--out', os.path.join(HERE, 'export')))
RIG = os.path.join(HERE, 'r6_rig_body.fbx')
TAU = math.tau
HIGH = [False]   # True while building the detailed high-poly pass that gets baked down

# R6 body parts in Blender space: centre and size (studs)
PARTS = {
    'Head': ((0, 0, 4.5), None),
    'Torso': ((0, 0, 3), (2, 1, 2)),
    'LeftArm': ((1.5, 0, 3), (1, 1, 2)),
    'RightArm': ((-1.5, 0, 3), (1, 1, 2)),
    'LeftLeg': ((0.5, 0, 1), (1, 1, 2)),
    'RightLeg': ((-0.5, 0, 1), (1, 1, 2)),
    'Cape': ((0, 0, 3), None),     # cloth with bones: its own mesh (and texture), welded to the torso
    'Tabard': ((0, 0, 3), None),   # the front cloth panel, likewise
    'SkirtBack': ((0, 0, 3), None),   # the back cloth panel behind the cape, likewise
}
BODY_PARTS = [p for p in PARTS if p not in ('Cape', 'Tabard', 'SkirtBack')]


# ------------------------------------------------------------------ scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.unit_settings.scale_length = 1.0
    return sc


def lin(hexv):
    h = hexv.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


# ------------------------------------------------------------------ geometry

PIECES = []   # (part, object)


def normal_at(fn, u, v, inside, closed_u=False):
    eps = 1e-4
    cu = (lambda x: x) if closed_u else (lambda x: min(max(x, 0.0), 1.0))
    cv = lambda x: min(max(x, 0.0), 1.0)
    p = Vector(fn(u, v))
    du = Vector(fn(cu(u + eps), v)) - Vector(fn(cu(u - eps), v))
    dv = Vector(fn(u, cv(v + eps))) - Vector(fn(u, cv(v - eps)))
    n = du.cross(dv)
    out = p - Vector(inside(p))
    if n.length < 1e-9:
        n = out
    n.normalize()
    return -n if n.dot(out) < 0 else n


def slab(part, mat, fn, nu, nv, th, inside, closed_u=False, bevel=0.01, name='piece', trim=None, uvd=1.0):
    """A solid plate of thickness `th` grown outward from the parametric surface fn(u, v), u, v in
    [0, 1]. `inside(P)` gives a point behind the surface so the plate grows away from the body.
    trim: dict(w, th, mat, sides) adds a raised border running round the plate's edges
    (sides: any of b t l r = v=0, v=1, u=0, u=1)."""
    cols = nu if closed_u else nu + 1
    P = [[Vector(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(cols)]
    N = [[normal_at(fn, i / nu, j / nv, inside, closed_u) for j in range(nv + 1)] for i in range(cols)]
    Q = [[P[i][j] + N[i][j] * th for j in range(nv + 1)] for i in range(cols)]
    # UVs straight from the plate's own surface, in studs: the outside face is one island with the
    # rims unfolded off its edges; the inside face (against the body, rarely seen) is its own island
    # at a third of the texel density
    U = [[0.0] * (nv + 1) for _ in range(nu + 1)]
    V = [[0.0] * (nv + 1) for _ in range(nu + 1)]
    for j in range(nv + 1):
        acc = 0.0
        for i in range(1, nu + 1):
            acc += (Q[i % cols][j] - Q[(i - 1) % cols][j]).length
            U[i][j] = acc
        for i in range(nu + 1):
            U[i][j] -= acc / 2
    for i in range(nu + 1):
        acc = 0.0
        for j in range(1, nv + 1):
            acc += (Q[i % cols][j] - Q[i % cols][j - 1]).length
            V[i][j] = acc
    IN = 0.35
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')     # packed, what the baked maps use
    dtl = bm.loops.layers.uv.new('Detail')    # raw studs, what the procedural materials use
    inner = [[bm.verts.new(P[i][j]) for j in range(nv + 1)] for i in range(cols)]
    outer = [[bm.verts.new(Q[i][j]) for j in range(nv + 1)] for i in range(cols)]
    inner_set = {v for row in inner for v in row}
    outer_set = {v for row in outer for v in row}

    def quad(vs, uvs):
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        k = IN if vs[0] in inner_set else 1.0
        if vs[0] in inner_set and any(v in outer_set for v in vs):
            k = 1.0   # a rim face
        for loop, uv in zip(f.loops, uvs):
            raw = (uv[0] / k, uv[1] / k)
            loop[uvl].uv = (uv[0] * uvd, uv[1] * uvd)
            loop[dtl].uv = raw
    spans = cols if closed_u else nu
    for i in range(spans):
        i2, k = (i + 1) % cols, i + 1
        for j in range(nv):
            quad((outer[i][j], outer[i2][j], outer[i2][j + 1], outer[i][j + 1]),
                 ((U[i][j], V[i][j]), (U[k][j], V[k][j]), (U[k][j + 1], V[k][j + 1]), (U[i][j + 1], V[i][j + 1])))
            quad((inner[i][j + 1], inner[i2][j + 1], inner[i2][j], inner[i][j]),
                 ((IN * U[i][j + 1], IN * V[i][j + 1]), (IN * U[k][j + 1], IN * V[k][j + 1]), (IN * U[k][j], IN * V[k][j]),
                  (IN * U[i][j], IN * V[i][j])))
        quad((inner[i][0], inner[i2][0], outer[i2][0], outer[i][0]),
             ((U[i][0], -th), (U[k][0], -th), (U[k][0], 0.0), (U[i][0], 0.0)))
        quad((outer[i][nv], outer[i2][nv], inner[i2][nv], inner[i][nv]),
             ((U[i][nv], V[i][nv]), (U[k][nv], V[k][nv]), (U[k][nv], V[k][nv] + th), (U[i][nv], V[i][nv] + th)))
    if not closed_u:
        for j in range(nv):
            quad((inner[0][j], outer[0][j], outer[0][j + 1], inner[0][j + 1]),
                 ((U[0][j] - th, V[0][j]), (U[0][j], V[0][j]), (U[0][j + 1], V[0][j + 1]), (U[0][j + 1] - th, V[0][j + 1])))
            quad((inner[nu][j + 1], outer[nu][j + 1], outer[nu][j], inner[nu][j]),
                 ((U[nu][j + 1] + th, V[nu][j + 1]), (U[nu][j + 1], V[nu][j + 1]), (U[nu][j], V[nu][j]),
                  (U[nu][j] + th, V[nu][j])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = finish(part, mat, bm, bevel, name)
    if trim:
        add_trims(part, fn, inside, closed_u, nu, nv, th, trim)
    return ob


def add_trims(part, fn, inside, closed_u, nu, nv, plate_th, trim):
    w, tt = trim.get('w', 0.065), trim.get('th', 0.035)
    mat, sides = trim.get('mat', 'Purple'), trim.get('sides', 'btlr')

    def length(f, n=8):
        pts = [Vector(f(k / n)) for k in range(n + 1)]
        return max(sum((pts[k + 1] - pts[k]).length for k in range(n)), 1e-4)

    def lifted(u, v, lift):
        uc = u if closed_u else min(max(u, 0.0), 1.0)
        return Vector(fn(u, v)) + normal_at(fn, uc, min(max(v, 0.0), 1.0), inside, closed_u) * lift

    def band(side, d0, d1, m, th_, lift, uvd, bevel, label):
        """a strip along one edge of the plate, from d0 to d1 studs in from that edge. On the game mesh it
        is coarser and unbevelled: the high pass carries the rounding into the normal map"""
        if not HIGH[0]:
            bevel = 0
        cols = nu if HIGH[0] else max(4, (nu + 1) // 2)
        rows = max(3, nv) if HIGH[0] else max(2, (nv + 1) // 2)
        if side in 'bt':
            def g(s_, t):
                a = min(0.48, (d0 + t * (d1 - d0)) / length(lambda q: fn(s_, q)))
                return tuple(lifted(s_, a if side == 'b' else 1 - a, lift))
            slab(part, m, g, cols, 1, th_, inside, closed_u=closed_u, bevel=bevel, name=label, uvd=uvd)
            return g, closed_u
        u_edge = 0.0 if side == 'l' else 1.0
        Lv = length(lambda q: fn(u_edge, q))
        vb = min(0.45, d1 / Lv) if 'b' in sides else 0.0   # meet the b / t bands, don't overlap them
        vt = min(0.45, d1 / Lv) if 't' in sides else 0.0

        def g(s_, t):
            v = vb + (1 - vb - vt) * s_
            a = min(0.48, (d0 + t * (d1 - d0)) / length(lambda q: fn(q, v)))
            return tuple(lifted(a if side == 'l' else 1 - a, v, lift))
        slab(part, m, g, rows, 1, th_, inside, bevel=bevel, name=label, uvd=uvd)
        return g, False
    for side in sides:
        g, cl = band(side, -0.12 * w, w, mat, tt, plate_th - 0.012, 2.6, 0.008, 'trim')
        if HIGH[0]:
            # a fine steel bead running inside the trim, and rivets set along it
            band(side, w + 0.022, w + 0.04, 'Steel', 0.014, plate_th - 0.005, 1.0, 0.005, 'bead')
            n = int(length(lambda q: g(q, 0.5), 24) / 0.3)
            for k in range(n):
                q = (k + 0.5) / n
                nrm = normal_at(g, q, 0.5, inside, cl)
                rivet(part, 'Steel', tuple(Vector(g(q, 0.5)) + nrm * (tt - 0.004)), nrm, 0.017, flat=0.6)


def finish(part, mat, bm, bevel, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(MATS[mat])
    if bevel:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = 3 if HIGH[0] else 1   # high pass: rounded; game mesh: a chamfer the normal map rounds off
        md.profile = 0.6
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(40)
    PIECES.append((part, ob))
    return ob


def se(theta, ex):
    """superellipse unit point: ex 2 = circle, higher = squarer"""
    c, s = math.cos(theta), math.sin(theta)
    return (math.copysign(abs(c) ** (2 / ex), c), math.copysign(abs(s) ** (2 / ex), s))


def val(f, *x):
    return f(*x) if callable(f) else f


def wrap(part, mat, c, z0, z1, a, b, th0, th1, ex=4.0, th=0.05, nu=40, nv=6, closed=False, bevel=0.01, extra=None,
         name='wrap', trim=None):
    """plate wrapped round a vertical axis through c=(x, y): theta 0 = +X, -90 deg = front (-Y), 90 = back.
    z0, z1: bottom and top, numbers or functions of theta in degrees. a, b: half-widths in X and Y,
    numbers or functions of z. extra(theta_deg, z) pushes the surface further out."""
    t0, t1 = math.radians(th0), math.radians(th1)
    if closed:
        t1 = t0 + TAU

    def fn(u, v):
        t = t0 + (t1 - t0) * u
        d = math.degrees(t)
        lo, hi = val(z0, d), val(z1, d)
        z = lo + (hi - lo) * v
        x, y = se(t, ex)
        e = extra(d, z) if extra else 0.0
        return (c[0] + x * (val(a, z) + e), c[1] + y * (val(b, z) + e), z)
    return slab(part, mat, fn, nu, nv, th, lambda p: (c[0], c[1], p[2]), closed_u=closed, bevel=bevel, name=name, trim=trim)


def rr_point(s_, hw, hd, r):
    """point s_ studs round a rounded rectangle (half-width hw in X, half-depth hd in Y, corner radius
    r), measured from the front centre (0, -hd), positive toward +X, negative toward -X"""
    if s_ < 0:
        x, y = rr_point(-s_, hw, hd, r)
        return (-x, y)
    a, b, q = hw - r, hd - r, math.pi * r / 2
    half = 2 * a + 2 * b + 2 * q
    if s_ > half:
        x, y = rr_point(2 * half - s_, hw, hd, r)
        return (-x, y)
    for seg in range(5):
        if seg == 0 and s_ <= a:
            return (s_, -hd)
        if seg == 0:
            s_ -= a
        if seg == 1 and s_ <= q:
            p = -math.pi / 2 + s_ / r
            return (a + r * math.cos(p), -b + r * math.sin(p))
        if seg == 1:
            s_ -= q
        if seg == 2 and s_ <= 2 * b:
            return (hw, -b + s_)
        if seg == 2:
            s_ -= 2 * b
        if seg == 3 and s_ <= q:
            p = s_ / r
            return (a + r * math.cos(p), b + r * math.sin(p))
        if seg == 3:
            s_ -= q
    return (a - s_, hd)


def bwrap(part, mat, c, z0, z1, hw, hd, r, s0, s1, th=0.05, nu=40, nv=6, extra=None, bevel=0.01, name='bwrap', trim=None):
    """plate wrapped round a rounded box (half-sizes hw, hd, corner radius r, numbers or functions of z)
    about the vertical axis through c, from s0 to s1 studs round from the front centre. z0, z1 and
    extra(s, z) (outward offset) take that perimeter position, so ridges and peaks are placed in studs"""
    def fn(u, v):
        s_ = s0 + (s1 - s0) * u
        lo, hi = val(z0, s_), val(z1, s_)
        z = lo + (hi - lo) * v
        e = extra(s_, z) if extra else 0.0
        x, y = rr_point(s_, val(hw, z) + e, val(hd, z) + e, r)
        return (c[0] + x, c[1] + y, z)
    return slab(part, mat, fn, nu, nv, th, lambda p: (c[0], c[1], p[2]), bevel=bevel, name=name, trim=trim)


FACES = {   # outward normal, across
    'front': ((0, -1, 0), (1, 0, 0)),
    'back': ((0, 1, 0), (-1, 0, 0)),
    'right': ((1, 0, 0), (0, -1, 0)),   # the +X side
    'left': ((-1, 0, 0), (0, 1, 0)),
}


def sheet(part, mat, face, plane, x0, x1, bot, top, h, th=0.05, nu=16, nv=8, bevel=0.01, name='sheet', trim=None):
    """plate over one face of a body block: x runs across the face, z up it, bot/top(x) its edges,
    h(x, z) its height off the face plane. plane = (distance of the face from the axis, centre
    across), so the torso front at y=-0.5 is plane=(0.5, 0)."""
    nrm, acr = (Vector(v) for v in FACES[face])
    d, xc = plane

    def fn(u, v):
        x = x0 + (x1 - x0) * u
        z = val(bot, x) + (val(top, x) - val(bot, x)) * v
        return tuple(nrm * (d + h(x, z)) + acr * (xc + x) + Vector((0, 0, z)))
    return slab(part, mat, fn, nu, nv, th, lambda p: tuple(Vector(p) - nrm * 5), bevel=bevel, name=name, trim=trim)


def fin(part, mat, path, out, height, th, nu=32, taper=None, name='fin'):
    """a blade standing up off a surface along path(s): out(s) the surface's outward direction"""
    def fn(u, v):
        k = val(taper, u) if taper else 1.0
        return tuple(Vector(path(u)) + Vector(out(u)) * (v - 0.35) * height * k)
    side = lambda p: (p[0] - 1, p[1], p[2])   # the blade runs in the YZ plane; grow it along +X
    ob = slab(part, mat, lambda u, v: tuple(Vector(fn(u, v)) - Vector((th / 2, 0, 0))), nu, 2, th, side, bevel=0.008,
              name=name)
    return ob


def rivet(part, mat, p, n, r=0.035, flat=0.55):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    dtl = bm.loops.layers.uv.new('Detail')
    seg = (16, 8) if HIGH[0] else (10, 5)
    bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=r, calc_uvs=True)
    for f in bm.faces:
        for loop in f.loops:
            loop[uvl].uv = (loop[uvl].uv.x * TAU * r, loop[uvl].uv.y * math.pi * r * flat)
            loop[dtl].uv = loop[uvl].uv
    n = Vector(n).normalized()
    rot = n.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    for v in bm.verts:
        v.co.z *= flat
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(p), verts=bm.verts)
    return finish(part, mat, bm, 0, 'rivet')


def cutter(center, size):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    me = bpy.data.meshes.new('cut')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('cut', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = True
    return ob


def boolean(ob, cut):
    md = ob.modifiers.new('cut', 'BOOLEAN')
    md.operation = 'DIFFERENCE'
    md.object = cut
    md.solver = 'EXACT'
    ob.modifiers.move(len(ob.modifiers) - 1, 0)   # cut before the bevel


def dome(r0, top, h, floor=0.012):
    """radius profile: straight up to `top`, then a dome of height h"""
    return lambda z: r0 if z < top else max(r0 * math.sqrt(max(0.0, 1 - ((z - top) / h) ** 2)), floor)


TRIM = dict(w=0.065, th=0.035, mat='Purple')


def T(sides, **kw):
    d = dict(TRIM, sides=sides)
    d.update(kw)
    return d


# ------------------------------------------------------------------ the armour

def helmet():
    R = 0.72
    skull = dome(R, 4.95, 0.5)
    helm = wrap('Head', 'Steel', (0, 0), 4.04, 5.45, skull, lambda z: skull(z) * 1.08, -90, 270, ex=2.4, th=0.055, nu=48,
                nv=16, closed=True, bevel=0.012, name='helm', trim=T('b'))
    boolean(helm, cutter((0, -0.8, 4.6), (0.96, 0.6, 0.085)))   # eye slit
    # brow plate over the slit and the faceplate under it, both standing proud of the skull
    wrap('Head', 'Steel', (0, 0), 4.655, lambda d: 4.86 + 0.06 * max(0.0, 1 - abs(d + 90) / 40), R + 0.05,
         (R + 0.05) * 1.08, -158, -22, ex=2.4, th=0.05, nu=26, nv=3, name='brow', trim=T('bt', w=0.045))
    keel = lambda d, z: 0.13 * max(0.0, 1 - abs(d + 90) / 38) ** 1.6 * (0.4 + 0.6 * (4.56 - z) / 0.6)
    chin = lambda d: 3.9 - 0.14 * max(0.0, 1 - abs(d + 90) / 55)
    face = wrap('Head', 'Steel', (0, 0), chin, 4.55, R + 0.05, (R + 0.05) * 1.08, -150, -30, ex=2.4, th=0.055, nu=30,
                nv=8, extra=keel, name='face', trim=T('btlr', w=0.05))
    for s in (-1, 1):   # breaths: three short slots each side
        for k in range(3):
            boolean(face, cutter((s * 0.33, -0.86, 4.13 + k * 0.1), (0.2, 0.3, 0.035)))
    # a purple keel down the face, as on the concept
    path = lambda s: (0, -((R + 0.05) * 1.08 + keel(-90, 4.55 - s * 0.62) + 0.05), 4.55 - s * 0.68)
    fin('Head', 'Purple', path, lambda s: (0, -1, 0.15), 0.07, 0.11, nu=12, name='face_keel')
    # dark padding behind the slit
    wrap('Head', 'Leather', (0, 0), 4.45, 4.75, 0.66, 0.7, -160, -20, ex=2.4, th=0.02, nu=16, nv=2, bevel=0, name='padding')
    # crest: a steel fin from brow to nape over the dome
    prof = lambda s: (-60 + 245 * s)
    path = lambda s: (0, -math.cos(math.radians(max(prof(s), 0))) * (R * 1.08 + 0.03) if prof(s) >= 0 else -(R * 1.08 + 0.03),
                      4.95 + math.sin(math.radians(max(prof(s), 0))) * 0.53 if prof(s) >= 0 else 4.95 + prof(s) / 60 * 0.08)
    outd = lambda s: (0, -math.cos(math.radians(max(prof(s), 0))), math.sin(math.radians(max(prof(s), 0))) + 0.01)
    fin('Head', 'Steel', path, outd, 0.16, 0.07, nu=40, taper=lambda s: 0.5 + 0.5 * math.sin(min(1.0, s * 2.5) * math.pi / 2),
        name='crest')
    fin('Head', 'Purple', lambda s: tuple(Vector(path(s)) + Vector(outd(s)) * 0.085), outd, 0.05, 0.085, nu=40,
        taper=lambda s: 0.5 + 0.5 * math.sin(min(1.0, s * 2.5) * math.pi / 2), name='crest_edge')
    # flared neck guard at the back
    wrap('Head', 'Steel', (0, 0), 3.86, 4.16, lambda z: R + 0.06 + 0.25 * (4.16 - z), lambda z: (R + 0.06 + 0.25 * (4.16 - z)) * 1.08,
         15, 165, ex=2.4, th=0.05, nu=26, nv=3, name='neckguard', trim=T('b', w=0.05))
    for t in (-140, -115, -65, -40):   # rivets along the brow
        x, y = se(math.radians(t), 2.4)
        rivet('Head', 'Purple', (x * (R + 0.11), y * (R + 0.11) * 1.08, 4.78), (x, y, 0), 0.028)
    for s_ in (-1, 1):   # rosettes over the ears
        rivet('Head', 'Purple', (s_ * (R + 0.06), 0.0, 4.42), (s_, 0, 0), 0.15, flat=0.3)
        rivet('Head', 'Steel', (s_ * (R + 0.105), 0.0, 4.42), (s_, 0, 0), 0.05, flat=0.6)
    # hood behind the helm, as on the concept's back view
    hood = lambda z: R + 0.12 + 0.3 * max(0.0, 4.2 - z)
    wrap('Head', 'Cloth', (0, 0.06), 3.9, lambda d: 4.22 + 0.14 * math.sin(math.radians(d)) ** 2, hood,
         lambda z: hood(z) * 1.12, 2, 178, ex=2.4, th=0.04, nu=36, nv=5,
         extra=lambda d, z: 0.035 * math.sin(math.radians(d) * 11) * min(1.0, max(0.0, 4.4 - z) * 2), bevel=0.006,
         name='cowl')


def torso():
    chest = lambda z: max(0.0, 1 - ((z - 3.3) / 1.05) ** 2)
    hf = lambda x, z: 0.06 + 0.17 * chest(z) * (1 - 0.55 * x * x) + 0.05 * max(0.0, 1 - abs(x) / 0.5)   # breast, keeled
    hb = lambda x, z: 0.06 + 0.1 * chest(z) * (1 - 0.5 * x * x)
    bot = lambda x: 2.4 + 0.32 * abs(x)
    # a padded cloth jacket wrapped right round the torso under the plates, matching the sleeves, so its
    # sides stay covered when the arms swing away
    wrap('Torso', 'Cloth', (0, 0), 1.97, 4.0, 1.006, 0.506, -90, 270, ex=14, th=0.02, nu=64, nv=8, closed=True, bevel=0.004,
         extra=lambda d, z: 0.006 * math.sin(z * 30) * max(0.0, math.cos(math.radians(d))) ** 4, name='jacket')
    slab('Torso', 'Cloth', lambda u, v: (-1.0 + 2.0 * u, -0.5 + 1.0 * v, 1.97), 8, 4, 0.02, lambda p: (p[0], p[1], p[2] + 1),
         bevel=0, name='jacket_hem')
    # breastplate and backplate
    sheet('Torso', 'Steel', 'front', (0.5, 0), -0.98, 0.98, bot, lambda x: 3.78 + 0.2 * abs(x), hf, th=0.06, nu=22, nv=12,
          name='breast', trim=T('btlr'))
    sheet('Torso', 'Steel', 'back', (0.5, 0), -0.98, 0.98, bot, 3.96, hb, th=0.06, nu=18, nv=10, name='back', trim=T('btlr'))
    # the emblem, as on the concept: a bar across the chest with flared points, crossed by a blade running
    # from the collar down to a point, and two sweeps curving up the lower ribs
    lift = lambda x, z: hf(x, z) + 0.05
    W = 0.9
    zc = lambda x: 3.42 - 0.1 * (abs(x) / W) ** 2
    hh = lambda x: 0.085 + 0.08 * math.sin(math.pi * min(1.0, abs(x) / W) ** 0.7) * (1 - abs(x) / W) ** 0.25 \
        - 0.08 * (abs(x) / W) ** 6
    sheet('Torso', 'PurplePolish', 'front', (0.5, 0), -W, W, lambda x: zc(x) - max(hh(x), 0.004),
          lambda x: zc(x) + max(hh(x), 0.004) * 0.85, lift, th=0.035, nu=30, nv=3, bevel=0.008, name='emblem_bar')
    sheet('Torso', 'PurplePolish', 'front', (0.5, 0), -0.2, 0.2, lambda x: 2.58 + 3.0 * abs(x), lambda x: 3.84 - 0.9 * abs(x),
          lambda x, z: lift(x, z) + 0.014, th=0.04, nu=6, nv=12, bevel=0.008, name='emblem_blade')
    for x0, x1 in ((0.24, 0.92), (-0.92, -0.24)):
        k = lambda x: (abs(x) - 0.24) / 0.68
        sheet('Torso', 'PurplePolish', 'front', (0.5, 0), x0, x1, lambda x: 2.62 + 0.5 * k(x) ** 1.3 - 0.04 * (1 - k(x)),
              lambda x: 2.62 + 0.5 * k(x) ** 1.3 + 0.12 * (1 - k(x)) ** 0.6 + 0.006, lift, th=0.035, nu=14, nv=2,
              bevel=0.008, name='emblem_rib')
    rivet('Torso', 'Steel', (0, -(0.5 + hf(0, 3.42) + 0.1), 3.42), (0, -1, 0), 0.06, flat=0.6)
    # back: a broad purple spade between the shoulder blades, as on the concept's back view
    sheet('Torso', 'PurplePolish', 'back', (0.5, 0), -0.84, 0.84, lambda x: 2.7 + 1.2 * abs(x) ** 1.2, 3.86,
          lambda x, z: hb(x, z) + 0.05, th=0.035, nu=16, nv=6, bevel=0.008, name='back_emblem',
          trim=T('b', w=0.025, th=0.012, mat='Steel'))
    # abdomen lames under the breastplate's point
    for face, h0 in (('front', 0.075), ('back', 0.07)):
        sheet('Torso', 'Steel', face, (0.5, 0), -0.95, 0.95, lambda x: 2.24 + 0.2 * abs(x), lambda x: 2.56 + 0.3 * abs(x),
              lambda x, z, h0=h0: h0 + 0.04 * (1 - x * x) + 0.16 * (z - 2.24), th=0.05, nu=12, nv=3, name='lame',
              trim=T('b', w=0.05))
    # collar: high at the back and sides, dipping at the front
    A = lambda z: 0.74 + 0.28 * (z - 3.9)
    wrap('Torso', 'Steel', (0, 0.02), 3.88, lambda d: 4.24 + 0.1 * math.sin(math.radians(d)), A, lambda z: A(z) * 1.06,
         -90, 270, ex=2.4, th=0.055, nu=40, nv=4, closed=True, name='collar', trim=T('t'))
    # mantle over the torso's flat top
    slab('Torso', 'Steel', lambda u, v: (-0.98 + 1.96 * u, -0.62 + 1.24 * v,
                                         4.02 + 0.05 * (1 - (2 * u - 1) ** 2) - 0.14 * max(0.0, abs(2 * v - 1) - 0.8) / 0.2),
         10, 8, 0.045, lambda p: (p[0], p[1], p[2] - 1), name='mantle')
    # belt: one loop right round the waist (snug at the sides, where the hands hang), with a square buckle
    wrap('Torso', 'Leather', (0, 0), 1.98, 2.22, 1.035, 0.6, -90, 270, ex=6, th=0.045, nu=56, nv=2, closed=True, name='belt')
    sheet('Torso', 'Steel', 'front', (0.5, 0), -0.16, 0.16, 1.96, 2.24, lambda x, z: 0.145, th=0.03, nu=4, nv=3,
          name='buckle', trim=T('btlr', w=0.04, th=0.025))
    # skirt: long cloth panels front, back and sides with purple hems, steel tassets over the hips
    fold = lambda x, z, k=13: 0.055 * math.sin(x * k) * min(1.0, (2.1 - z) * 1.5)
    sheet('Tabard', 'Cloth', 'front', (0.5, 0), -0.6, 0.6, lambda x: 0.7 + 0.5 * abs(x) / 0.6, 2.1,
          lambda x, z: 0.13 + 0.17 * (2.1 - z) + fold(x, z), th=0.03, nu=24, nv=10, bevel=0.006, name='skirt_front',
          trim=T('blr', w=0.06, th=0.025))
    sheet('SkirtBack', 'Cloth', 'back', (0.5, 0), -0.98, 0.98, lambda x: 0.5 + 0.4 * abs(x), 2.1,
          lambda x, z: 0.12 + 0.17 * (2.1 - z) + fold(x, z, 9), th=0.03, nu=24, nv=8, bevel=0.006, name='skirt_back',
          trim=T('blr', w=0.06, th=0.025))
    for face in ('right', 'left'):
        sheet('Torso', 'Cloth', face, (1.0, 0), -0.55, 0.55, lambda x: 0.85 + 0.25 * (x + 0.55), 1.97,
              lambda x, z: 0.06 + 0.2 * (1.97 - z) + fold(x, z, 11), th=0.03, nu=10, nv=8, bevel=0.006, name='skirt_side',
              trim=T('b', w=0.06, th=0.025))
        for zt, zb, f in ((1.98, 1.55, 0.1), (1.66, 1.2, 0.17)):
            sheet('Torso', 'PurplePolish', face, (1.0, 0), -0.52, 0.52, lambda x, zb=zb: zb + 0.08 * (1 - (x / 0.52) ** 2), zt,
                  lambda x, z, zt=zt, f=f: 0.04 + f + 0.24 * (zt - z) + 0.05 * (1 - (x / 0.55) ** 2), th=0.05, nu=10,
                  nv=4, name='hip_flap', trim=T('blr', w=0.04, th=0.025, mat='Steel'))
    # cape: tucked under the collar, falling in deep folds to the ankles, widening as it goes, with an
    # engraved purple hem and the cross embroidered on its back
    TOP = 4.04
    k_ = lambda z: (TOP - z) / 3.88   # 0 at the shoulders, 1 at the hem

    def cape_y(x, z):
        k = max(0.0, k_(z))
        hug = 0.5 + hb(x, z) + 0.11                     # lying on the backplate
        free = 0.62 + 0.5 * k ** 1.25                   # hanging free below it
        y = (hug + free + math.sqrt((hug - free) ** 2 + 0.06 ** 2)) / 2   # a smooth max of the two
        return y + 0.08 * k * math.sin(x * 8.5 + 0.6) + 0.025 * k * math.sin(x * 21 + 1.3)
    width = lambda z: 0.86 + 0.36 * max(0.0, k_(z))
    hem = lambda xn: 0.16 + 0.1 * xn * xn

    def cape(u, v):
        xn = 2 * u - 1
        z = hem(xn) + (TOP - hem(xn)) * v
        x = xn * width(z)
        return (x, cape_y(x, z), z)
    slab('Cape', 'Cloth', cape, 40, 22, 0.03, lambda p: (p[0], p[1] - 1, p[2]), bevel=0.006, name='cape',
         trim=T('blr', w=0.06, th=0.022))

    def on_cape(x0, x1, bot, top):   # a patch lying on the cape's outer face
        def fn(u, v):
            x = x0 + (x1 - x0) * u
            z = bot(x) + (top(x) - bot(x)) * v
            return (x, cape_y(x, z) + 0.03, z)
        return fn
    for sx in (-1, 1):   # studs pinning it at the shoulders
        rivet('Cape', 'PurplePolish', (sx * 0.74, cape_y(sx * 0.74, 3.86) + 0.035, 3.86), (0, 1, 0), 0.075, flat=0.5)
        rivet('Cape', 'Steel', (sx * 0.74, cape_y(sx * 0.74, 3.86) + 0.065, 3.86), (0, 1, 0), 0.03, flat=0.6)
    hb_ = lambda x: 0.03 + 0.09 * (1 - abs(x) / 0.62) ** 0.6
    slab('Cape', 'Embroidery', on_cape(-0.62, 0.62, lambda x: 3.05 - hb_(x), lambda x: 3.05 + hb_(x) * 0.85), 24, 2, 0.012,
         lambda p: (p[0], p[1] - 1, p[2]), bevel=0.003, name='cape_cross')
    slab('Cape', 'Embroidery', on_cape(-0.15, 0.15, lambda x: 2.1 + 4.0 * abs(x), lambda x: 3.6 - 1.2 * abs(x)), 6, 14, 0.016,
         lambda p: (p[0], p[1] - 1, p[2]), bevel=0.003, name='cape_cross')


def arm():
    """the left arm (+X); the right one is its mirror"""
    cx = 1.5
    # black cloth sleeve under it all
    # purple cloth sleeve (the concept's sleeves match its tabard), gathered in soft folds, closed over the shoulder
    wrap('LeftArm', 'Cloth', (cx, 0), 2.0, 4.0, 0.535, 0.545, -180, 180, ex=8, th=0.03, nu=36, nv=8, bevel=0.006,
         closed=True, extra=lambda d, z: 0.018 * math.sin(math.radians(d) * 9 + z * 6) * (0.6 + 0.4 * math.sin(z * 9)),
         name='sleeve')
    slab('LeftArm', 'Cloth', lambda u, v: (1.0 + u, -0.55 + 1.1 * v, 4.0 + 0.04 * math.sin(math.pi * u) * math.sin(math.pi * v)),
         8, 8, 0.03, lambda p: (p[0], p[1], p[2] - 1), bevel=0.006, name='sleeve_top')
    # pauldron: a big dome and two lames below it, each pointed at the outside, all trimmed
    cap = dome(0.66, 3.86, 0.34)
    wrap('LeftArm', 'Steel', (cx + 0.02, 0),
         lambda d: 3.52 - 0.14 * max(0.0, math.cos(math.radians(d))) ** 2, 4.2, cap,
         lambda z: cap(z) * 0.95, -180, 180, ex=2.6, th=0.06, nu=48, nv=10, closed=True, name='pauldron', trim=T('b'),
         # closed all round and drawn in at the neck, in proportion to the dome's radius so it vanishes at the top
         extra=lambda d, z: -0.29 * cap(z) * max(0.0, -math.cos(math.radians(d))) ** 1.5)
    for k, (zb, rb) in enumerate(((3.22, 0.76), (2.96, 0.8)), 1):
        R = lambda z, zb=zb, rb=rb: rb - 0.42 * (z - zb)
        span = 116 - 10 * k
        wrap('LeftArm', 'Steel', (cx + 0.02 + 0.04 * k, 0),
             lambda d, zb=zb, span=span: zb - 0.12 * max(0.0, math.cos(math.radians(d))) ** 2,
             zb + 0.38, R, lambda z, R=R: R(z) * 0.93, -span, span, ex=2.6, th=0.055, nu=34, nv=4, name='lame', trim=T('blr'))
    for t in (-60, -25, 25, 60):   # rivets round the dome
        x, y = se(math.radians(t), 2.6)
        rivet('LeftArm', 'Purple', (cx + 0.02 + x * 0.72, y * 0.68, 3.68), (x, y, 0.1), 0.03)
    # elbow cop on the outside: a domed disc with a purple boss and a fan
    r = 0.3
    sheet('LeftArm', 'PurplePolish', 'right', (2.0, 0), -r, r, lambda x: 2.88 - math.sqrt(max(r * r - x * x, 0)),
          lambda x: 2.88 + math.sqrt(max(r * r - x * x, 0)),
          lambda x, z: 0.07 + 0.11 * max(0.0, 1 - (x * x + (z - 2.88) ** 2) / (r * r)), th=0.05, nu=12, nv=8,
          name='elbow', trim=T('bt', w=0.04, th=0.025, mat='Steel'))
    rivet('LeftArm', 'Steel', (2.0 + 0.24, 0, 2.88), (1, 0, 0), 0.08, flat=0.6)
    # bracer, flared toward the elbow with a ridge down the outside
    B = lambda z: 0.55 + 0.08 * (z - 2.2) / 0.62
    ridge = lambda d, z: 0.06 * max(0.0, math.cos(math.radians(d))) ** 6
    wrap('LeftArm', 'Steel', (cx + 0.02, 0), 2.2, lambda d: 2.72 + 0.06 * max(0.0, math.cos(math.radians(d))) ** 2, B,
         lambda z: B(z) + 0.01, -150, 150, ex=4.5, th=0.05, nu=36, nv=5, extra=ridge, name='bracer', trim=T('bt', w=0.055))
    for z in (2.42,):   # a leather strap
        wrap('LeftArm', 'Leather', (cx + 0.02, 0), z, z + 0.07, lambda zz: B(zz) + 0.045, lambda zz: B(zz) + 0.055, -150, 150,
             ex=4.5, th=0.025, nu=36, nv=1, extra=ridge, bevel=0.005, name='strap')
    # gauntlet: leather glove and steel knuckle plate
    wrap('LeftArm', 'Leather', (cx + 0.01, 0), 1.97, 2.24, 0.525, 0.53, -152, 152, ex=5, th=0.035, nu=30, nv=3, name='glove')
    # the glove's palm, closing the bottom of the hand
    slab('LeftArm', 'Leather', lambda u, v: (1.0 + 1.04 * u, -0.54 + 1.08 * v, 1.975 - 0.02 * math.sin(math.pi * u) * math.sin(math.pi * v)),
         6, 6, 0.03, lambda p: (p[0], p[1], p[2] + 1), bevel=0.006, name='palm')
    # purple gauntlet cuff and back-of-hand plate, as on the concept
    Cf = lambda z: 0.585 + 0.25 * (z - 2.16)
    wrap('LeftArm', 'PurplePolish', (cx + 0.02, 0), 2.16, 2.34, Cf, lambda z: Cf(z) + 0.01, -150, 150, ex=5, th=0.045,
         nu=30, nv=2, name='cuff', trim=T('t', w=0.03, th=0.02, mat='Steel'))
    sheet('LeftArm', 'PurplePolish', 'right', (2.0, 0), -0.36, 0.36, 2.0, lambda x: 2.17 - 0.05 * (x / 0.36) ** 2,
          lambda x, z: 0.05 + 0.04 * (1 - (x / 0.4) ** 2), th=0.04, nu=8, nv=2, name='hand_plate')


def leg():
    """the left leg (+X); the right one is its mirror. Angular, as on the concept: boxy plates with
    soft corners, a sharp ridge down the front, flat sides and pointed edges"""
    cx = 0.5
    tri = lambda s_, w: max(0.0, 1 - abs(s_) / w)   # 1 at the front centre falling to 0 at +-w studs
    R = 0.13
    # open on the inner side (toward the other leg): from just round the front-inner corner, over the
    # front, the outer side and the back, to just round the back-inner corner
    def span(hw, hd):
        a, b, q = hw - R, hd - R, math.pi * R / 2
        return -(a + q + 0.04), 2 * a + 2 * b + 2 * q + a + q + 0.04
    wrap('LeftLeg', 'Fabric', (0.5, 0), 0.0, 2.0, 0.535, 0.545, -180, 180, ex=8, th=0.03, nu=30, nv=3, bevel=0.006, closed=True,
         extra=lambda d, z: 0.012 * math.sin(math.radians(d) * 7 + z * 14), name='trousers')
    # cuisse: a ridged plate over the front and outside of the thigh, pointed at the bottom
    bwrap('LeftLeg', 'Steel', (cx, 0), lambda s_: 1.52 - 0.1 * tri(s_, 0.4), 1.95, 0.575, 0.58, R, -0.44, 0.74, nu=22, nv=4,
          extra=lambda s_, z: 0.06 * tri(s_, 0.25), name='cuisse', trim=T('btlr', w=0.05))
    # knee: a lame above and below a peaked purple cop, and a kite-shaped wing on the outside
    for zb, zt, pk in ((1.34, 1.52, 0.0), (0.8, 0.96, 0.06)):
        bwrap('LeftLeg', 'Steel', (cx, 0), lambda s_, zb=zb, pk=pk: zb - pk * tri(s_, 0.35), zt, 0.585, 0.59, R, -0.44, 0.66,
              nu=20, nv=2, extra=lambda s_, z: 0.05 * tri(s_, 0.25), name='knee_lame', trim=T('b', w=0.04, th=0.025))
    bwrap('LeftLeg', 'PurplePolish', (cx, 0), lambda s_: 0.94 - 0.1 * tri(s_, 0.3), lambda s_: 1.34 + 0.08 * tri(s_, 0.3),
          0.62, 0.63, R, -0.3, 0.3, nu=14, nv=6,
          extra=lambda s_, z: 0.1 * tri(s_, 0.3) + 0.03 * math.sin(math.pi * min(max((z - 0.84) / 0.58, 0.0), 1.0)),
          name='knee', trim=T('btlr', w=0.032, th=0.022, mat='Steel'))
    kw = 0.2
    sheet('LeftLeg', 'PurplePolish', 'right', (1.0, 0), -kw, kw, lambda x: 1.14 - 0.19 * (1 - abs(x) / kw),
          lambda x: 1.14 + 0.19 * (1 - abs(x) / kw), lambda x, z: 0.11 + 0.05 * (1 - abs(x) / kw), th=0.045, nu=8, nv=4,
          name='knee_wing', trim=T('bt', w=0.03, th=0.02, mat='Steel'))
    rivet('LeftLeg', 'Steel', (cx, -(0.63 + 0.1 + 0.07), 1.14), (0, -1, 0), 0.05, flat=0.55)
    # greave: flat-sided, tapering to the ankle, ridged down the shin, peaked under the knee, flared over the boot
    G = lambda z: 0.55 + 0.04 * (z - 0.3) / 0.66
    g0, g1 = span(0.57, 0.57)
    bwrap('LeftLeg', 'Steel', (cx, 0), 0.3, lambda s_: 0.94 + 0.14 * tri(s_, 0.32), G, lambda z: G(z) + 0.01, R, g0, g1,
          nu=56, nv=6, extra=lambda s_, z: 0.08 * tri(s_, 0.2) + 0.03 * max(0.0, (0.42 - z) / 0.12),
          name='greave', trim=T('tlr', w=0.05))
    # boot: a squared leather shaft and sole, three ridged sabaton lames and a pointed toe cap
    bwrap('LeftLeg', 'Leather', (cx, 0), 0.04, 0.38, 0.565, 0.57, R, g0, g1, nu=48, nv=3, name='boot')
    bwrap('LeftLeg', 'Leather', (cx, -0.03), 0.0, 0.06, 0.59, 0.61, R, g0, g1, nu=48, nv=1, name='sole')
    # the underside of the boot (stops at the inner edge so the two soles don't meet)
    slab('LeftLeg', 'Leather', lambda u, v: (1.1 * u, -0.66 + 1.24 * v, 0.0), 8, 8, 0.03,
         lambda p: (p[0], p[1], p[2] + 1), bevel=0.006, name='sole_bottom')
    for k, (zb, zt) in enumerate(((0.24, 0.38), (0.14, 0.28), (0.05, 0.19))):
        A = lambda z, k=k, zt=zt: 0.585 + 0.025 * k + 0.1 * (zt - z)
        bwrap('LeftLeg', 'Steel', (cx, 0), zb, zt, A, lambda z, A=A: A(z) + 0.01, R, -0.52, 0.52, nu=18, nv=2,
              extra=lambda s_, z: 0.045 * tri(s_, 0.3), name='sabaton', trim=T('b', w=0.03, th=0.022))
    sheet('LeftLeg', 'Steel', 'front', (0.5, cx), -0.42, 0.42, 0.05, 0.15,
          lambda x, z: 0.15 + 0.12 * (1 - abs(x) / 0.42) * (1 - (z - 0.05) / 0.1 * 0.6), th=0.045, nu=8, nv=2, name='toe',
          trim=T('b', w=0.025, th=0.018))
    # a purple diamond on the outer ankle
    aw = 0.11
    sheet('LeftLeg', 'PurplePolish', 'right', (1.0, 0), -aw, aw, lambda x: 0.6 - 0.11 * (1 - abs(x) / aw),
          lambda x: 0.6 + 0.11 * (1 - abs(x) / aw), lambda x, z: 0.1 + 0.03 * (1 - abs(x) / aw), th=0.035, nu=6, nv=3,
          name='ankle_diamond')


# ------------------------------------------------------------------ materials

MATS = {}
FILIGREE_PERIOD = 0.24   # studs along a trim per repeat of the engraving
TRIM_UV_W = 0.065 * 1.12  # studs across a trim (its Detail-UV V runs 0 .. this)


def filigree_image(w=384, h=128):
    """a tileable strip of engraved scrollwork: a wavy stem throwing off spiral tendrils with leaf
    tips, between two border lines. 1 = groove (cut into the metal), 0 = polished face."""
    import numpy as np
    asp = w / h
    X, Y = np.meshgrid((np.arange(w) + 0.5) / h, (np.arange(h) + 0.5) / h)   # units of strip height
    pts = []
    xs = np.linspace(-0.2, asp + 0.2, 500)
    pts.append(np.stack([xs, 0.5 + 0.17 * np.sin(2 * np.pi * xs / asp * 2)], 1))   # the stem, two waves a tile
    for k in range(4):   # a spiral tendril off each crest and trough, curling the other way each time
        x0 = (k * 0.5 + 0.25) * asp / 2
        up = 1 if k % 2 == 0 else -1
        cx, cy = x0 + 0.2 * asp / 8, 0.5 - up * 0.06
        ph = np.linspace(0, 2.3 * np.pi, 160)
        r = 0.2 * (1 - ph / (2.6 * np.pi))
        a0 = np.pi / 2 * up
        pts.append(np.stack([cx + r * np.cos(a0 - up * ph) * 1.2, cy + r * np.sin(a0 - up * ph)], 1))
        lx = x0 - 0.12 * asp / 8   # a leaf on the other side of the stem
        t = np.linspace(-1, 1, 60)
        pts.append(np.stack([lx + 0.16 * t, 0.5 + up * 0.17 + up * 0.09 * (1 - t * t)], 1))
    for by in (0.07, 0.93):   # border lines
        pts.append(np.stack([xs, np.full_like(xs, by)], 1))
    P = np.concatenate(pts)
    P = np.concatenate([P, P + [asp, 0], P - [asp, 0]])   # wrap so the tile repeats seamlessly
    d = np.full(X.shape, 9.0)
    for c in np.array_split(P, 40):
        dd = np.sqrt((X[..., None] - c[:, 0]) ** 2 + (Y[..., None] - c[:, 1]) ** 2).min(-1)
        d = np.minimum(d, dd)
    width = 0.032
    g = np.clip((width - d) / (width * 0.6), 0, 1)
    g = g * g * (3 - 2 * g)
    img = bpy.data.images.new('Filigree', w, h, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    px = np.zeros((h, w, 4), np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = g
    px[..., 3] = 1
    img.pixels = px.ravel()
    img.pack()
    return img


def mk_material(name, kind, c1, c2, edge_col, rough, metal, groove_col=None, engraved=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(bsdf.outputs[0], out.inputs['Surface'])
    tc = N.new('ShaderNodeTexCoord')
    det = N.new('ShaderNodeUVMap')
    det.uv_map = 'Detail'

    def mapped(vec, scale, rot=(0, 0, 0)):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale
        mp.inputs['Rotation'].default_value = rot
        L.new(vec, mp.inputs['Vector'])
        return mp.outputs['Vector']

    def noise(scale, detail=4, rough_=0.5, vec=None):
        n = N.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough_
        L.new(vec or tc.outputs['Object'], n.inputs['Vector'])
        return n.outputs['Fac']

    def op(kind_, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath')
        n.operation = kind_
        n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def rng(x, a, b, c=0.0, d=1.0):
        n = N.new('ShaderNodeMapRange')
        n.clamp = True
        L.new(x, n.inputs['Value'])
        n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = a, b
        n.inputs['To Min'].default_value, n.inputs['To Max'].default_value = c, d
        return n.outputs['Result']

    def mix(f, a, b, blend='MIX'):
        n = N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        if isinstance(f, (int, float)):
            n.inputs['Factor'].default_value = f
        else:
            L.new(f, n.inputs['Factor'])
        for sock, c in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(c, tuple):
                sock.default_value = c
            else:
                L.new(c, sock)
        return n.outputs[2]

    def grey(x):
        c = N.new('ShaderNodeCombineColor')
        for i in range(3):
            L.new(x, c.inputs[i])
        return c.outputs[0]

    duv = N.new('ShaderNodeSeparateXYZ')
    L.new(det.outputs['UV'], duv.inputs[0])
    du_, dv_ = duv.outputs['X'], duv.outputs['Y']   # studs along / across (from the bottom edge) of each plate

    def filigree(period, height, v0=0.0):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1.0 / period, 1.0 / height, 1.0)
        mp.inputs['Location'].default_value = (0.0, -v0 / height, 0.0)
        L.new(det.outputs['UV'], mp.inputs['Vector'])
        t = N.new('ShaderNodeTexImage')
        t.image = FILIGREE
        t.interpolation = 'Cubic'
        t.extension = 'REPEAT'
        L.new(mp.outputs['Vector'], t.inputs['Vector'])
        sp = N.new('ShaderNodeSeparateColor')
        L.new(t.outputs['Color'], sp.inputs[0])
        return sp.outputs[0]

    def band(x, a, b, soft=0.004):   # 1 between a and b
        return op('MULTIPLY', rng(x, a - soft, a), rng(x, b + soft, b))

    geo = N.new('ShaderNodeNewGeometry')
    # edges: where a wide bevel normal turns away from the true normal
    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.012
    bev.samples = 8
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.998, 0.96)
    # cavity: creases and the gaps between plates
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.045
    ao.samples = 24
    cav = rng(ao.outputs['AO'], 0.1, 1.0, 0.55, 1.0)
    low = noise(3.0, 3, 0.5)
    r0, r1 = rough
    height = None
    if kind == 'steel':
        # satin gunmetal: brushed grain along each plate, faint forging waves, polished edges
        grain = noise(1.0, 3, 0.6, vec=mapped(det.outputs['UV'], (6.0, 420.0, 1.0)))
        grain2 = noise(1.0, 2, 0.5, vec=mapped(det.outputs['UV'], (2.0, 160.0, 1.0)))
        col = mix(op('MULTIPLY', low, 0.6), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', edge, 0.55), col, lin(edge_col))
        rgh = op('ADD', rng(grain, 0.3, 0.7, r0 - 0.025, r0 + 0.025), rng(grain2, 0.35, 0.65, -0.02, 0.02))
        rgh = op('ADD', rgh, op('MULTIPLY', low, r1 - r0))
        rgh = op('SUBTRACT', rgh, op('MULTIPLY', edge, 0.12), clamp=True)
        # acid-etched scroll band just inside the bottom edge of each plate: darker, matte, barely recessed
        etch = op('MULTIPLY', filigree(0.36, 0.11, 0.105), band(dv_, 0.105, 0.215))
        col = mix(op('MULTIPLY', etch, 0.75), col, lin('#16171b'))
        rgh = op('ADD', rgh, op('MULTIPLY', etch, 0.3), clamp=True)
        # forging: shallow hammer dimples
        ham = N.new('ShaderNodeTexVoronoi')
        ham.feature = 'SMOOTH_F1'
        ham.inputs['Scale'].default_value = 7.0
        L.new(tc.outputs['Object'], ham.inputs['Vector'])
        dimple = rng(ham.outputs['Distance'], 0.0, 0.5)
        # grime settling in creases, rougher and darker
        grime = op('MULTIPLY', rng(ao.outputs['AO'], 0.4, 0.95, 1.0, 0.0), rng(noise(7.0, 5, 0.6), 0.35, 0.65))
        col = mix(op('MULTIPLY', grime, 0.6), col, lin('#14120f'))
        rgh = op('ADD', rgh, op('MULTIPLY', grime, 0.22), clamp=True)
        # micro-scratches catching the light
        micro = []
        for rot in ((0.3, 0.0, 0.2), (1.1, 0.7, 2.0), (0.0, 1.3, 0.9)):
            micro.append(rng(noise(1.0, 1, 0.5, vec=mapped(tc.outputs['Object'], (160.0, 160.0, 2.5), rot)), 0.7, 0.74))
        mic = op('MULTIPLY', op('MAXIMUM', op('MAXIMUM', micro[0], micro[1]), micro[2]), rng(noise(3.0, 2), 0.45, 0.62))
        col = mix(op('MULTIPLY', mic, 0.35), col, lin(edge_col))
        rgh = op('SUBTRACT', rgh, op('MULTIPLY', mic, 0.12), clamp=True)
        height = op('ADD', op('ADD', op('MULTIPLY', grain, 0.04), op('MULTIPLY', dimple, 0.35)),
                    op('SUBTRACT', op('MULTIPLY', noise(5.0, 2, 0.4), 0.3), op('ADD', op('MULTIPLY', etch, 0.25),
                                                                            op('MULTIPLY', mic, 0.15))))
        bump_strength, bump_dist = 0.12, 0.004
    elif kind == 'purple':
        # engraved scrollwork: dark rough grooves cut into a polished face, raised edges brightest
        fil = N.new('ShaderNodeTexImage')
        fil.image = FILIGREE
        fil.interpolation = 'Cubic'
        fil.extension = 'REPEAT'
        L.new(mapped(det.outputs['UV'], (1.0 / FILIGREE_PERIOD, 1.0 / TRIM_UV_W, 1.0)), fil.inputs['Vector'])
        groove = fil.outputs['Color']
        sep = N.new('ShaderNodeSeparateColor')
        L.new(groove, sep.inputs[0])
        g = sep.outputs[0] if engraved else op('MULTIPLY', sep.outputs[0], 0.0)
        col = mix(op('MULTIPLY', low, 0.7), lin(c1), lin(c2))
        col = mix(rng(noise(1.6, 3, 0.5), 0.45, 0.7, 0.0, 0.45), col, lin('#4a35c4'))   # anodised tone shifts
        col = mix(op('MULTIPLY', edge, 0.6), col, lin(edge_col))
        col = mix(g, col, lin(groove_col))
        grime_p = op('MULTIPLY', rng(ao.outputs['AO'], 0.4, 0.95, 1.0, 0.0), 0.5)
        col = mix(grime_p, col, lin('#170a26'))
        rgh = op('ADD', rng(low, 0.3, 0.7, r0, r0 + 0.06), op('MULTIPLY', g, r1 - r0), clamp=True)
        rgh = op('SUBTRACT', rgh, op('MULTIPLY', edge, 0.08), clamp=True)
        height = op('ADD', op('MULTIPLY', g, -1.0), op('MULTIPLY', noise(40.0, 3), 0.03))
        bump_strength, bump_dist = 0.55, 0.0025
    elif kind == 'leather':
        cells = N.new('ShaderNodeTexVoronoi')
        cells.inputs['Scale'].default_value = 70
        L.new(tc.outputs['Object'], cells.inputs['Vector'])
        wrinkle = noise(9.0, 6, 0.65)
        col = mix(op('MULTIPLY', low, 0.8), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', edge, 0.5), col, lin(edge_col))
        rgh = op('ADD', rng(wrinkle, 0.3, 0.7, r0, r1), op('MULTIPLY', edge, -0.15), clamp=True)
        st_mp = N.new('ShaderNodeMath')
        st_mp.operation = 'FRACT'
        L.new(op('DIVIDE', du_, 0.03), st_mp.inputs[0])
        stitch = op('MULTIPLY', band(st_mp.outputs[0], 0.15, 0.65, 0.08), band(dv_, 0.014, 0.022, 0.003))
        groove_l = band(dv_, 0.008, 0.028, 0.004)
        col = mix(op('MULTIPLY', stitch, 0.9), col, lin('#6b5440'))
        col = mix(op('MULTIPLY', groove_l, 0.35), col, lin('#0c0806'))
        height = op('ADD', op('ADD', op('MULTIPLY', cells.outputs['Distance'], 0.5), op('MULTIPLY', wrinkle, 0.6)),
                    op('SUBTRACT', op('MULTIPLY', stitch, 0.6), op('MULTIPLY', groove_l, 0.4)))
        bump_strength, bump_dist = 0.3, 0.004
    else:   # cloth: a fine twill weave
        uv = det.outputs['UV']
        wa = N.new('ShaderNodeTexWave')
        wa.inputs['Scale'].default_value = 1.0
        wa.bands_direction = 'DIAGONAL'
        L.new(mapped(uv, (110.0, 110.0, 1.0)), wa.inputs['Vector'])
        wb = N.new('ShaderNodeTexWave')
        wb.inputs['Scale'].default_value = 1.0
        wb.bands_direction = 'X'
        L.new(mapped(uv, (220.0, 220.0, 1.0)), wb.inputs['Vector'])
        weave = op('MULTIPLY', wa.outputs['Fac'], wb.outputs['Fac'])
        col = mix(op('MULTIPLY', low, 0.8), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', weave, 0.25), col, lin(edge_col))
        dam = filigree(0.42, 0.14)   # the scroll, woven in a slightly lighter, sheenier thread
        col = mix(op('MULTIPLY', dam, 0.45), col, lin(edge_col))
        rgh = op('SUBTRACT', rng(weave, 0.0, 1.0, r0, r1), op('MULTIPLY', dam, 0.12), clamp=True)
        height = op('ADD', op('MULTIPLY', weave, 0.6), op('MULTIPLY', noise(4.0, 3), 0.4))
        bump_strength, bump_dist = 0.35, 0.003
    col = mix(1.0, col, grey(cav), 'MULTIPLY')
    rb = N.new('ShaderNodeBevel')
    rb.inputs['Radius'].default_value = 0.006
    rb.samples = 8
    bn = N.new('ShaderNodeBump')
    bn.inputs['Strength'].default_value = bump_strength
    bn.inputs['Distance'].default_value = bump_dist
    L.new(height, bn.inputs['Height'])
    L.new(rb.outputs['Normal'], bn.inputs['Normal'])
    tags = {}
    mv = N.new('ShaderNodeValue')
    mv.outputs[0].default_value = metal
    for tag, sock in (('COL', col), ('ROUGH', rgh), ('METAL', mv.outputs[0]), ('NRM', bn.outputs['Normal'])):
        rr = N.new('NodeReroute')
        rr.name = 'OUT_' + tag
        L.new(sock, rr.inputs[0])
        tags[tag] = rr
    L.new(tags['COL'].outputs[0], bsdf.inputs['Base Color'])
    L.new(tags['ROUGH'].outputs[0], bsdf.inputs['Roughness'])
    L.new(tags['METAL'].outputs[0], bsdf.inputs['Metallic'])
    L.new(tags['NRM'].outputs[0], bsdf.inputs['Normal'])
    MATS[name] = m
    return m


FILIGREE = None


def materials():
    global FILIGREE
    FILIGREE = filigree_image()
    mk_material('Steel', 'steel', '#3a3c43', '#45474f', '#8d9099', (0.36, 0.44), 1.0)
    mk_material('Purple', 'purple', '#6a2fb8', '#5a27a0', '#c4a2f5', (0.2, 0.62), 1.0, groove_col='#120720')
    mk_material('PurplePolish', 'purple', '#7434c8', '#6229ae', '#c9a6f8', (0.3, 0.38), 1.0, groove_col='#120720',
                engraved=False)
    mk_material('Leather', 'leather', '#24150d', '#2e1b11', '#4a2e1e', (0.5, 0.72), 0.0)
    mk_material('Cloth', 'cloth', '#1a0830', '#230b40', '#341457', (0.78, 0.95), 0.0)
    mk_material('Fabric', 'cloth', '#121216', '#18181e', '#26262e', (0.8, 0.95), 0.0)
    mk_material('Embroidery', 'cloth', '#6b33b5', '#7a3fc6', '#a57de0', (0.55, 0.7), 0.0)


# ------------------------------------------------------------------ assembly

def mirror_left_to_right():
    for part, ob in list(PIECES):
        if not part.startswith('Left'):
            continue
        cp = ob.copy()
        cp.data = ob.data.copy()
        bpy.context.scene.collection.objects.link(cp)
        bm = bmesh.new()
        bm.from_mesh(cp.data)
        bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=bm.verts)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(cp.data)
        bm.free()
        PIECES.append((part.replace('Left', 'Right'), cp))


def smooth(me):
    """smooth shading, with hard edges where faces meet at more than 35 degrees"""
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(35):
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


def join_parts(prefix='Armor_'):
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for part in PARTS:
        obs = [ob for p, ob in PIECES if p == part]
        bm = bmesh.new()
        mats = []
        for ob in obs:
            ev = ob.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev)
            for poly in me.polygons:
                m = ob.data.materials[0]
                if m not in mats:
                    mats.append(m)
                poly.material_index = mats.index(m)
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        for ob in obs:
            bpy.data.objects.remove(ob)
        me = bpy.data.meshes.new(prefix + part)
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(prefix + part, me)
        bpy.context.scene.collection.objects.link(ob)
        smooth(me)
        out[part] = ob
    for ob in [o for o in bpy.data.objects if o.name.startswith('cut')]:
        bpy.data.objects.remove(ob)
    return out


def pieces():
    helmet()
    torso()
    arm()
    leg()
    mirror_left_to_right()


def build(high=True):
    """the game meshes (Armor_*) and, unless high=False, the detailed pass baked onto them (High_*)"""
    materials()
    HIGH[0] = False
    pieces()
    if STAGE == 'stats':
        dg = bpy.context.evaluated_depsgraph_get()
        rows = {}
        for part, ob in PIECES:
            me = ob.evaluated_get(dg).to_mesh()
            k = (part, ob.name.split('.')[0])
            rows[k] = rows.get(k, 0) + sum(len(p.vertices) - 2 for p in me.polygons)
        for (part, name), n in sorted(rows.items(), key=lambda r: -r[1]):
            print(f'{part:10s} {name:14s} {n}')
    low = join_parts('Armor_')
    if not high:
        return low, {}
    PIECES.clear()
    HIGH[0] = True
    pieces()
    hi = join_parts('High_')
    HIGH[0] = False
    return low, hi


# ------------------------------------------------------------------ uv + bake

def unwrap(ob):
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=True, scale=True, shape_method='CONCAVE', margin_method='FRACTION', margin=0.006)
        bpy.ops.object.mode_set(mode='OBJECT')
        ob.select_set(False)


def bake(objs, highs, res):
    """bake each High_ mesh onto its Armor_ mesh: normals, and colour / roughness / metalness through
    an emission pass, so every engraving, bead, rivet and rounded edge lands in the maps"""
    sc = bpy.context.scene
    bk = sc.render.bake
    bk.margin = 12
    bk.use_clear = True
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.016
    bk.max_ray_distance = 0.04
    os.makedirs(OUT, exist_ok=True)
    maps = {}
    for part, ob in objs.items():
        if ONLY and part != ONLY:
            continue
        hi = highs[part]
        unwrap(ob)
        imgs = {}
        for ch, nonc in (('Color', False), ('Normal', True), ('Roughness', True), ('Metalness', True)):
            img = bpy.data.images.new(f'{ob.name}_{ch}', res, res, alpha=False)
            img.colorspace_settings.name = 'Non-Color' if nonc else 'sRGB'
            img.generated_color = (0.5, 0.5, 1, 1) if ch == 'Normal' else (0, 0, 0, 1)
            imgs[ch] = img
        # the game mesh gets a bare material whose only job is to hold the target image
        tm = bpy.data.materials.new(ob.name + '_Target')
        tm.use_nodes = True
        tnode = tm.node_tree.nodes.new('ShaderNodeTexImage')
        tm.node_tree.nodes.active = tnode
        ob.data.materials.clear()
        ob.data.materials.append(tm)
        for o in bpy.data.objects:
            o.select_set(False)
        hi.select_set(True)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        for ch, img in imgs.items():
            tnode.image = img
            restore = []
            if ch != 'Normal':
                for m in hi.data.materials:
                    nt = m.node_tree
                    em = nt.nodes.get('BAKE_EMIT') or nt.nodes.new('ShaderNodeEmission')
                    em.name = 'BAKE_EMIT'
                    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
                    old = out.inputs['Surface'].links[0].from_socket
                    src = nt.nodes['OUT_' + {'Color': 'COL', 'Roughness': 'ROUGH', 'Metalness': 'METAL'}[ch]].outputs[0]
                    nt.links.new(src, em.inputs['Color'])
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                    restore.append((nt, old, out))
            if ch == 'Normal':
                sc.cycles.samples = 16
                bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=12, use_selected_to_active=True)
            else:
                sc.cycles.samples = 24 if ch == 'Color' else 8
                bpy.ops.object.bake(type='EMIT', margin=12, use_selected_to_active=True)
            for nt, old, out in restore:
                nt.links.new(old, out.inputs['Surface'])
            img.filepath_raw = os.path.join(OUT, f'{ob.name}_{ch}.png')
            img.file_format = 'PNG'
            img.save()
            print('BAKED', img.name, flush=True)
        maps[part] = imgs
        hi.select_set(False)
        ob.select_set(False)
        hi.hide_render = True
    return maps


def baked_materials(objs, maps):
    """swap each mesh onto one material driven by its baked maps (what Roblox will show)"""
    for part, ob in objs.items():
        if part not in maps:
            continue
        m = bpy.data.materials.new(ob.name + '_Baked')
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes['Principled BSDF']
        uvs = {}
        for ch, img in maps[part].items():
            t = nt.nodes.new('ShaderNodeTexImage')
            t.image = img
            uvs[ch] = t
        nt.links.new(uvs['Color'].outputs[0], bsdf.inputs['Base Color'])
        nt.links.new(uvs['Roughness'].outputs[0], bsdf.inputs['Roughness'])
        nt.links.new(uvs['Metalness'].outputs[0], bsdf.inputs['Metallic'])
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(uvs['Normal'].outputs[0], nm.inputs['Color'])
        nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
        ob.data.materials.clear()
        ob.data.materials.append(m)


# ------------------------------------------------------------------ rig, preview, export

def load_rig():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=RIG)
    rig = [o for o in bpy.data.objects if o not in before]
    body = bpy.data.materials.new('Body')
    body.use_nodes = True
    b = body.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin('#a3a2a5')
    b.inputs['Roughness'].default_value = 0.6
    named = {}
    for o in rig:
        o.data.materials.clear()
        o.data.materials.append(body)
        c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
        part = min(BODY_PARTS, key=lambda p: (Vector(PARTS[p][0]) - c).length)
        o.name = 'Ref_' + part
        named[part] = o
    return named


def studio():
    """the grey studio the previews and the timelapse are shot in: world, three area lights, a camera"""
    sc = bpy.context.scene
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 560, 760
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.025, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.32, 0.32, 0.36, 1)
    mr = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value = -1
    nt.links.new(mr.outputs[0], ramp.inputs[0])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Factor'])
    nt.links.new(ramp.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = lin('#7d7d82')
    nt.links.new(mix.outputs[2], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.5

    def light(name, loc, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy, ld.size, ld.color = energy, size, color
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = Vector((0, 0, 2.6)) - Vector(loc)
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    light('key', (-5, -7, 7), 2600, 4)
    light('fill', (7, -4, 3), 700, 6, (0.85, 0.85, 1.0))
    light('rim', (2, 8, 6), 2200, 3, (0.9, 0.8, 1.0))
    cam_d = bpy.data.cameras.new('cam')
    cam_d.lens = 85
    cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam, cam_d


def preview(path, samples=48):
    sc, cam, cam_d = studio()
    sc.cycles.samples = samples
    shots = []
    for i, (az, el) in enumerate(((0, 8), (35, 10), (180, 8))):
        a = math.radians(az - 90)
        d = 16.5
        cam_d.lens = 85
        cam.location = (d * math.cos(a) * math.cos(math.radians(el)), d * math.sin(a) * math.cos(math.radians(el)),
                        2.6 + d * math.sin(math.radians(el)))
        cam.rotation_euler = (Vector((0, 0, 2.55)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        f = path.replace('.png', f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    # stitch the three views side by side
    ims = [bpy.data.images.load(f) for f in shots]
    W, H = ims[0].size
    import numpy as np
    strip = np.zeros((H, W * 3, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        px = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
        strip[:, k * W:(k + 1) * W] = px
    out = bpy.data.images.new('preview', W * 3, H, alpha=False)
    out.pixels = strip.ravel()
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()
    for f in shots:
        os.remove(f)
    # close-up of the upper body from the front three-quarter
    cam_d.lens = 85
    sc.render.resolution_x, sc.render.resolution_y = 900, 900
    a = math.radians(-28 - 90)
    cam.location = (9 * math.cos(a), 9 * math.sin(a), 4.6)
    cam.rotation_euler = (Vector((0, 0, 3.55)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path.replace('.png', '_closeup.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def build_sequence():
    """build every detailed piece as its own object and return them in the order they were made, each
    right-hand piece just after its left-hand twin"""
    materials()
    HIGH[0] = True
    pieces()
    HIGH[0] = False
    for ob in [o for o in bpy.data.objects if o.name.startswith('cut')]:
        ob.hide_render = True
        ob.hide_set(True)
    for p, ob in PIECES:
        smooth(ob.data)
    left = [ob for p, ob in PIECES if p.startswith('Left')]
    twins = dict(zip(left, [ob for p, ob in PIECES if p.startswith('Right')]))
    order = []
    for p, ob in PIECES:
        if p.startswith('Right'):
            continue
        order.append(ob)
        if ob in twins:
            order.append(twins[ob])
    return order


def live(per_tick=3, interval=0.05):
    """watch it being built in Blender's own window: the R6 body appears, then the armour piece by piece
    in the viewport, in material preview, while the view slowly circles. Run with a window (no -b)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    order = build_sequence()
    load_rig()
    for ob in order:
        ob.hide_set(True)
    state = {'i': 0, 'turn': 0.0}

    def views():
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D':
                    yield area.spaces.active

    def frame_view():
        for sp in views():
            sp.shading.type = 'MATERIAL'
            sp.overlay.show_floor = False
            sp.overlay.show_axis_x = sp.overlay.show_axis_y = False
            r3 = sp.region_3d
            r3.view_perspective = 'PERSP'
            r3.view_location = (0, 0, 2.5)
            r3.view_distance = 13
        return None

    def tick():
        i = state['i']
        for ob in order[i:i + per_tick]:
            ob.hide_set(False)
        state['i'] = i + per_tick
        state['turn'] += 0.004
        for sp in views():
            from mathutils import Euler
            sp.region_3d.view_rotation = Euler((math.radians(80), 0, math.radians(-30) + state['turn']), 'XYZ').to_quaternion()
        if state['i'] >= len(order):
            print('LIVE ALL DONE', flush=True)
            return None
        return interval
    bpy.app.timers.register(frame_view, first_interval=0.5)
    bpy.app.timers.register(tick, first_interval=2.0)


def timelapse(path, build_frames=200, hold_frames=72, fps=24, size=540, samples=10):
    """film the armour being put together: every plate, trim, bead and rivet appears in the order the
    script makes it (right-hand pieces just after their left-hand twins), the camera circling as it goes,
    then a full turn round the finished suit. Frames go to <path>_frames/, the video to path (MP4)."""
    import subprocess
    order = build_sequence()
    load_rig()
    sc, cam, cam_d = studio()
    sc.cycles.samples = samples
    sc.render.use_persistent_data = True
    sc.render.resolution_x = sc.render.resolution_y = size
    cam_d.lens = 70
    frames = os.path.splitext(path)[0] + '_frames'
    os.makedirs(frames, exist_ok=True)
    total = build_frames + hold_frames
    for f in range(total):
        shown = len(order) if f >= build_frames else int(len(order) * (f + 1) / build_frames)
        for i, ob in enumerate(order):
            ob.hide_render = i >= shown
        az = -35 + 70 * f / build_frames if f < build_frames else 35 + 360 * (f - build_frames) / hold_frames
        a = math.radians(az - 90)
        cam.location = (15 * math.cos(a), 15 * math.sin(a), 2.6 + 15 * math.sin(math.radians(9)))
        cam.rotation_euler = (Vector((0, 0, 2.55)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(frames, f'frame_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print('FRAME', f + 1, '/', total, flush=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(frames, 'frame_%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', path], check=True)
    print('TIMELAPSE', path, flush=True)


CLOTH_RIGS = {
    # part: (bone name prefix, chain x positions, joint heights top -> tip)
    'Cape': ('Cape', (-0.75, 0.0, 0.75), (3.85, 2.95, 2.05, 1.15, 0.15)),
    'Tabard': ('Tabard', (0.0,), (2.08, 1.6, 1.15, 0.68)),
    'SkirtBack': ('SkirtBack', (-0.5, 0.5), (2.08, 1.55, 1.05, 0.5)),
}


def rig_cloth(ob, prefix, xs, zs):
    """give a cloth mesh an armature: a root bone pinned at the top, and one chain of bones per x in xs
    hanging down through the joint heights zs. Each vertex is weighted to at most two chains and two
    bones along them (four influences, Roblox's limit), blending smoothly so the cloth bends, not kinks."""
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]

    def y_at(x, z):   # how far back (or forward) the cloth hangs there, for placing the bones in it
        near = [v.y for v in vs if abs(v.z - z) < 0.2 and abs(v.x - x) < 0.3]
        return sum(near) / len(near) if near else 0.0
    ad = bpy.data.armatures.new('Rig_' + prefix)
    arm = bpy.data.objects.new('Rig_' + prefix, ad)
    bpy.context.scene.collection.objects.link(arm)
    names = {}
    with bpy.context.temp_override(active_object=arm, object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        root = ad.edit_bones.new(prefix + 'Root')
        y0 = y_at(0.0, zs[0])
        root.head, root.tail = (0, y0, zs[0] + 0.25), (0, y0, zs[0])
        for c, x in enumerate(xs):
            parent = root
            for r in range(len(zs) - 1):
                b = ad.edit_bones.new(f'{prefix}_{c}_{r}' if len(xs) > 1 else f'{prefix}_{r}')
                b.head = (x, y_at(x, zs[r]), zs[r])
                b.tail = (x, y_at(x, zs[r + 1]), zs[r + 1])
                b.parent = parent
                parent = b
                names[(c, r)] = b.name
        bpy.ops.object.mode_set(mode='OBJECT')
    groups = {n: ob.vertex_groups.new(name=n) for n in list(names.values()) + [prefix + 'Root']}
    spacing = (xs[-1] - xs[0]) / max(1, len(xs) - 1) if len(xs) > 1 else 1.0
    n = len(zs) - 1
    for i, v in enumerate(vs):
        # position down the chain: -0.5 is the pinned top, r + 0.5 the middle of bone r
        if v.z >= zs[0]:
            p = -0.5
        elif v.z <= zs[-1]:
            p = n - 0.5
        else:
            r = max(k for k in range(n) if zs[k] >= v.z)
            p = r + (zs[r] - v.z) / (zs[r] - zs[r + 1])
        p = min(max(p, -0.5), n - 0.5)
        roww = {r: max(0.0, 1 - abs(p - (r + 0.5))) for r in range(-1, n)}
        if len(xs) > 1:
            xc = min(max(v.x, xs[0]), xs[-1])
            colw = {c: max(0.0, 1 - abs(xc - x) / spacing) for c, x in enumerate(xs)}
        else:
            colw = {0: 1.0}
        w = {}
        for r, wr in roww.items():
            if wr <= 0:
                continue
            if r < 0:
                w[prefix + 'Root'] = w.get(prefix + 'Root', 0.0) + wr
                continue
            for c, wc in colw.items():
                if wc > 0:
                    w[names[(c, r)]] = w.get(names[(c, r)], 0.0) + wr * wc
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(x for _, x in top) or 1.0
        for name, x in top:
            groups[name].add([i], x / tot, 'REPLACE')
    ob.parent = arm
    md = ob.modifiers.new('rig', 'ARMATURE')
    md.object = arm
    return arm


def export(objs, refs):
    for o in bpy.data.objects:
        o.select_set(False)
    rigs = [rig_cloth(objs[part], *CLOTH_RIGS[part]) for part in CLOTH_RIGS if part in objs]
    for o in bpy.data.objects:
        o.select_set(False)
    for o in list(objs.values()) + list(refs.values()) + rigs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'ArmorKit.fbx'), use_selection=True,
                             object_types={'MESH', 'ARMATURE'}, apply_scale_options='FBX_SCALE_ALL',
                             mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP', add_leaf_bones=False,
                             armature_nodetype='NULL')
    print('EXPORTED', os.path.join(OUT, 'ArmorKit.fbx'), flush=True)


def main():
    if STAGE == 'live':   # in Blender's window: keep the UI, just empty the scene
        live()
        return
    reset()
    if STAGE == 'timelapse':
        os.makedirs(OUT, exist_ok=True)
        timelapse(os.path.join(OUT, 'build_timelapse.mp4'))
        return
    objs, highs = build(high=STAGE != 'stats')
    refs = load_rig()
    os.makedirs(OUT, exist_ok=True)
    for ob in list(objs.values()) + list(highs.values()):
        print(ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), flush=True)
    if STAGE == 'stats':
        return
    if STAGE == 'preview':   # the detailed pass with live materials
        for ob in objs.values():
            ob.hide_render = True
        preview(os.path.join(OUT, 'preview.png'), samples=32)
        return
    maps = bake(objs, highs, RES)
    baked_materials(objs, maps)
    preview(os.path.join(OUT, 'preview.png'))
    if not ONLY:
        export(objs, refs)


main()
