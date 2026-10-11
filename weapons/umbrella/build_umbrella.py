"""The bladed umbrella from Gachiakuta, rigged to open and close.

The model, from the reference:
    canopy   eight white cloth panels, maroon text running across them in two bands, faint seams radiating out
    ribs     one per seam, each carrying a long black blade with a yellow inlay that runs past the canopy's edge
             to a sharp point
    top      a leaf-shaped black spike with a yellow slot, bound with red cord where it meets the canopy
    shaft    dark grey, with a runner and eight stretchers underneath, and a black ribbed handle

The rig (one armature, two meshes):
    Root     the handle and shaft, the hub, the spike and the cord
    Runner   the sleeve on the shaft; it slides down as the umbrella closes
    Rib_1..8 hinge at the hub. Each carries its rib and blade; the cloth between two ribs follows both
    Every stretcher runs from the Runner to its rib and keeps its length the whole way.
Animation 'OpenClose' (baked, 60 frames at 30 fps): open (1), closing to shut (20), held, opening again (40-60).

    export/Umbrella.fbx           Umbrella (frame) + Umbrella_Canopy (cloth), skinned to UmbrellaRig, animation
    export/Umbrella_Color / _Normal (OpenGL) / _Roughness / _Metalness.png          the frame's maps
    export/Umbrella_Canopy_Color / _Normal / _Roughness / _Metalness.png            the cloth's maps (all eight
                                                                                    panels share one panel's space)
    export/Umbrella_rig.blend     the same, to pose or animate further in Blender

    python build_umbrella.py -- [--stage preview|stats|all] [--res 1024]
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'armor'))
import build_armor as A                         # noqa: E402
from build_armor import slab, lin, TAU          # noqa: E402

STAGE = A.STAGE
RES = A.RES
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
A.PARTS = {'Umbrella': ((0, 0, 0), None)}
MATS, HIGH = A.MATS, A.HIGH

N_RIBS = 8
R = 3.0               # canopy radius (along a rib, from the hub)
Z_HUB = 5.6           # where the ribs hinge (the umbrella's length to there)
R_HUB = 0.14
BLADE_END = 1.45      # blade tips, as a fraction of R
S_STRETCH = 0.95      # where a stretcher meets its rib (along the rib from the hub)
Z_RUNNER = Z_HUB - 0.95   # the runner, open
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def rib_dir(k):
    a = TAU * k / N_RIBS
    return Vector((math.cos(a), math.sin(a), 0.0))


def rib_profile(s):
    """a rib at distance s from the hub: (out, down) in its own vertical plane. A shallow cone, curving a little"""
    return s, -math.tan(math.radians(13)) * s - 0.08 * s * s / R


def rib_frame(k, s):
    """rib k at distance s: the point on the canopy, the direction across it, and the canopy's normal"""
    d = rib_dir(k)
    out, down = rib_profile(s)
    p = Vector((0, 0, Z_HUB)) + d * (R_HUB + out) + Vector((0, 0, down))
    o2, d2 = rib_profile(s + 1e-3)
    tangent = (d * (o2 - out) + Vector((0, 0, d2 - down))).normalized()
    side = Vector((0, 0, 1)).cross(d)
    return p, side, tangent.cross(side).normalized()   # the canopy's normal, pointing up and out


def rib_point(k, s, lift=0.0, across=0.0):
    """a point on rib k, s along it, lifted off the canopy (along its normal) and moved across it"""
    p, side, n = rib_frame(k, s)
    return p + n * lift + side * across


# ------------------------------------------------------------------ the pieces

def surface(mat, fn, us, vs, closed_u=False, closed_v=False, caps=(False, False), out=None, name='surface'):
    """a single-walled quad grid over fn(u, v), with rows and columns only at the given u and v positions (so they
    go where the shape bends, nowhere else). closed_u / closed_v wrap it round; caps close a tube's open ends with a
    fan; out(p) is a point it faces away from. UVs in studs: U along u, V along v"""
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
    if closed_u and not closed_v:
        for end, j in ((0, 0), (1, rows - 1)):
            if not caps[end]:
                continue
            ring = [V[i][j] for i in range(cols)]
            c = sum((v.co for v in ring), Vector()) / len(ring)
            if max((v.co - c).length for v in ring) < 1e-5:
                continue
            cv = bm.verts.new(c)
            for i in range(cols):
                f = bm.faces.new((cv, ring[(i + 1) % cols], ring[i]))
                f.smooth = True
                for loop in f.loops:
                    q = loop.vert.co - c
                    loop[uvl].uv = loop[dtl].uv = (q.x + q.y, q.z)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if out is not None:   # face away from out(p)
        bm.normal_update()
        score = sum(f.normal.dot(f.calc_center_median() - Vector(out(f.calc_center_median()))) for f in bm.faces)
        if score < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return A.finish('Umbrella', mat, bm, 0, name)


def tube(part, mat, path, radius, nu=12, ts=(0.0, 1.0), caps=(False, False), closed=False, name='tube', ref=None):
    """a round rod along path(t), radius(t), its rings only at the given t (a ring, if closed)"""
    def frame(t):
        a = Vector(path(clamp(t - 1e-3) if not closed else t - 1e-3))
        b = Vector(path(clamp(t + 1e-3) if not closed else t + 1e-3))
        tng = (b - a).normalized()
        r_ = Vector(ref) if ref else (Vector((0, 0, 1)) if abs(tng.z) < 0.9 else Vector((1, 0, 0)))
        x = tng.cross(r_).normalized()
        return tng, x, tng.cross(x)

    def fn(u, t):
        tng, x, y = frame(t)
        a = TAU * u
        r = radius(t) if callable(radius) else radius
        return tuple(Vector(path(t)) + (x * math.cos(a) + y * math.sin(a)) * r)
    us = [i / nu for i in range(nu + 1)]
    return surface(mat, fn, us, list(ts), closed_u=True, closed_v=closed, caps=caps,
                   out=lambda p: axis_point(path, p), name=name)


def axis_point(path, p, n=60):
    p = Vector(p)
    best, bd = None, 1e9
    for i in range(n + 1):
        q = Vector(path(i / n))
        d = (q - p).length
        if d < bd:
            best, bd = q, d
    return best


def lathe(part, mat, zr, nu=16, caps=(False, False), name='lathe'):
    """a turned piece round the shaft: zr = [(z, radius), ...] bottom to top, one ring per entry"""
    fn = lambda u, j: (zr[j][1] * math.cos(TAU * u), zr[j][1] * math.sin(TAU * u), zr[j][0])
    return surface(mat, fn, [i / nu for i in range(nu + 1)], list(range(len(zr))), closed_u=True, caps=caps,
                   out=lambda p: (0, 0, p[2]), name=name)


def edged(mat, frame, width, thick, nu, name, inlay=None, section=None, us=None):
    """a forged blade: a diamond cross-section (two cutting edges, a ridge down each face) swept along
    frame(u) -> (centre, across, normal), u in [0, 1], half-width width(u) and half-thickness thick(u). Where both
    reach zero it closes to a point. Every lengthwise edge is hard, so each facet catches the light on its own.
    inlay(u) = half-width: instead, a strip laid over the middle of that blade's faces, both sides, parallel to them
    and just proud of them"""
    bm = bmesh.new()
    uvl, dtl = bm.loops.layers.uv.new('UVMap'), bm.loops.layers.uv.new('Detail')
    rows, along, acc, prev = [], [], 0.0, None
    us = us or [i / nu for i in range(nu + 1)]
    nu = len(us) - 1
    for i in range(nu + 1):
        u = us[i]
        c, a, n = frame(u)
        w, t = (width(u), thick(u)) if section is None else (0.0, 0.0)
        if section is not None:
            sec = section(u)
        elif inlay is None:
            sec = [(-w, 0.0), (0.0, t), (w, 0.0), (0.0, -t)]
        else:
            wi, e = inlay(u), 0.006
            h = t * (1 - wi / w) + e if w > 1e-6 else 0.0
            sec = [(-wi, h), (0.0, t + e), (wi, h), (wi, -h), (0.0, -t - e), (-wi, -h)]
        rows.append([bm.verts.new(c + a * x + n * y) for x, y in sec])
        acc += (c - prev).length if prev is not None else 0.0
        along.append(acc)
        prev = c
    m = len(rows[0])
    for i in range(nu):
        for f in range(m):
            a0, b0 = rows[i][f], rows[i][(f + 1) % m]
            a1, b1 = rows[i + 1][f], rows[i + 1][(f + 1) % m]
            face = bm.faces.new((a0, a1, b1, b0))
            face.smooth = True
            for loop in face.loops:
                ii = i if loop.vert in (a0, b0) else i + 1
                acr = 0.0 if loop.vert in (a0, a1) else ((rows[ii][f].co - rows[ii][(f + 1) % m].co).length)
                loop[uvl].uv = loop[dtl].uv = (along[ii], acr)
    cap = bm.faces.new(rows[0])
    for loop in cap.loops:
        q = loop.vert.co - rows[0][1].co
        loop[uvl].uv = loop[dtl].uv = (q.length, 0.0)
    end = bm.faces.new(list(reversed(rows[-1]))) if inlay is not None and len(set(v.co.to_tuple(5) for v in rows[-1])) > 2 \
        else None
    if end:
        for loop in end.loops:
            loop[uvl].uv = loop[dtl].uv = ((loop.vert.co - rows[-1][1].co).length, 0.0)
    for f in range(m):   # the ridges and the cutting edges stay hard
        for i in range(nu):
            e = bm.edges.get((rows[i][f], rows[i + 1][f]))
            if e:
                e.smooth = False
    for v in rows[0]:
        for e in v.link_edges:
            e.smooth = False
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return A.finish('Umbrella', mat, bm, 0, name)


FIN_S0, FIN_S1 = 0.55, 1.38                     # a fin's inner end and its point, as fractions of R
FIN_UE = (1.0 - FIN_S0) / (FIN_S1 - FIN_S0)    # where it passes the canopy's edge
FIN_H, FIN_D, FIN_T, FIN_C = 0.5, 0.3, 0.02, 0.035   # height at the point, drop below the cloth, half-thickness, bevel


def fin_top(u):
    """the fin's top edge: one straight line from its inner point up to its outer point"""
    return FIN_H * u


def fin_bottom(u):
    """its lower edge: along the cloth, then past the canopy's edge a drop, and a long diagonal back up to the point"""
    if u <= FIN_UE:
        return -0.005 if u > 0 else 0.0
    low = FIN_UE + 0.07
    if u <= low:
        return -0.005 - (FIN_D - 0.005) * (u - FIN_UE) / (low - FIN_UE)
    return -FIN_D + (FIN_H + FIN_D) * (u - low) / (1 - low)


def rib_blade(k):
    """the blade on rib k: a thin fin standing straight up off the rib (the shape from the anime), its edges bevelled
    to a knife edge, with a yellow band along each side"""
    s0, s1 = FIN_S0 * R, FIN_S1 * R
    _, side, _ = rib_frame(k, R)

    def frame(u):
        p, side_, n = rib_frame(k, s0 + (s1 - s0) * u)
        return p, side_, n

    def section(u):
        h, b = fin_top(u), fin_bottom(u)
        c = min(FIN_C, max(h - b, 0.0) / 2)
        t = FIN_T * clamp((h - b) / 0.06)
        return [(-t, b + c), (-t, h - c), (0.0, h), (t, h - c), (t, b + c), (0.0, b)]
    low = FIN_UE + 0.07
    # rows: at its points, where its thickness and bevel stop growing, at the canopy's edge and the drop, and under
    # each of the cloth's rows (so its foot follows the rib's curve with the cloth)
    knots = {0.0, 1.0, FIN_UE, low, 0.07 / 0.5}
    tip = 1 - 0.07 / ((FIN_H + FIN_D) / (1 - low) - FIN_H)
    knots.add(tip)
    for s_ in CANOPY_S:
        u = (s_ - s0) / (s1 - s0)
        if 0 < u < FIN_UE:
            knots.add(u)
    us = sorted(knots)
    edged('Black', frame, None, None, 0, 'blade', section=section, us=us)
    # the yellow band, both sides: below a black band along the top, its outer end cut parallel to the diagonal
    def band_lo(u):
        return max(0.035, fin_bottom(u) + 0.09)

    def band_hi(u):
        return fin_top(u) - FIN_C - 0.07 * min(1.0, u / 0.3)
    bus = sorted({u for u in us if 0.06 <= u <= 0.98} | {0.06, 0.3, FIN_UE + 0.07 * 0.05 / 0.295, 0.98})
    for sgn in (1, -1):
        def band(uu, v, sgn=sgn):
            p, side_, n = frame(uu)
            lo, hi = band_lo(uu), band_hi(uu)
            y = lo + max(hi - lo, 0.0) * v
            return tuple(p + side_ * sgn * (FIN_T + 0.003) + n * y)
        surface('Yellow', band, bus, [0.0, 1.0], out=lambda q, sgn=sgn: tuple(Vector(q) - side * sgn), name='blade_inlay')


def frame_pieces():
    # handle: a crook, wrapped in cream tape, then the shaft
    RH = 0.3

    def crook(t):
        # straight down from the shaft, then a half turn up the other side
        L1 = 0.95
        L2 = math.pi * RH
        L3 = 0.18
        s_ = t * (L1 + L2 + L3)
        if s_ <= L1:
            return (0.0, 0.0, 1.05 - s_)
        if s_ <= L1 + L2:
            a = (s_ - L1) / RH
            return (-RH + RH * math.cos(a), 0.0, 1.05 - L1 - RH * math.sin(a))
        return (-2 * RH, 0.0, 1.05 - L1 + (s_ - L1 - L2))
    L_ = 0.95 + math.pi * RH + 0.18
    t1, t2 = 0.95 / L_, (0.95 + math.pi * RH) / L_
    tube('Umbrella', 'Tape', crook, 0.075, nu=10, ts=[0.0, t1 / 2, t1] + [t1 + (t2 - t1) * i / 8 for i in range(1, 9)] + [1.0],
         name='handle', ref=(0, 1, 0))   # the crook lies in the XZ plane: keep its rings square to it
    # a domed cap closing the crook's end
    zc = 1.05 - 0.95 + 0.18 - 0.03
    tube('Umbrella', 'Black', lambda t: (-2 * RH, 0.0, zc + 0.09 * math.sin(t * math.pi / 2)),
         lambda t: 0.085 * math.cos(t * math.pi / 2), nu=10, ts=[0.0, 0.35, 0.7, 1.0], name='handle_cap')
    lathe('Umbrella', 'Black', [(1.0, 0.07), (1.05, 0.085), (1.12, 0.085), (1.17, 0.06)], nu=12, name='ferrule')
    lathe('Umbrella', 'Steel', [(1.15, 0.055), (Z_HUB, 0.055)], nu=10, name='shaft')
    # the hub the ribs hinge on, and a collar under it
    lathe('Umbrella', 'Black', [(Z_HUB - 0.16, 0.07), (Z_HUB - 0.1, 0.16), (Z_HUB + 0.06, 0.17), (Z_HUB + 0.12, 0.12),
                                (Z_HUB + 0.16, 0.09)], nu=16, caps=(True, True), name='hub')
    # the top: red cord bound round the foot of a leaf-shaped spike with a yellow slot
    for j in range(3):
        zc = Z_HUB + 0.17 + j * 0.055
        tube('Umbrella', 'Cord', lambda t, zc=zc: (0.1 * math.cos(TAU * t), 0.1 * math.sin(TAU * t), zc + 0.01 * math.sin(TAU * t)),
             0.026, nu=6, ts=[i / 12 for i in range(13)], closed=True, name='cord')
    z0 = Z_HUB + 0.12

    def spike_w(u):
        return 0.075 + 0.17 * math.sin(math.pi * min(u / 0.42, 1.0) / 2) if u < 0.42 else 0.245 * max(0.0, 1 - (u - 0.42) / 0.58) ** 1.1

    # the spike: a forged leaf blade, ridged down both faces, with a yellow slot set through it
    spike_t = lambda u: 0.065 * clamp(spike_w(u) / 0.245) ** 0.7
    sframe = lambda u: (Vector((0, 0, z0 + 1.15 * u)), Vector((1, 0, 0)), Vector((0, 1, 0)))
    edged('Black', sframe, spike_w, spike_t, 10, 'spike')
    sw = lambda q: math.sin(math.pi * q) ** 0.6
    edged('Yellow', lambda q: sframe(0.28 + 0.4 * q), lambda q: spike_w(0.28 + 0.4 * q),
          lambda q: spike_t(0.28 + 0.4 * q), 6, 'spike_slot', inlay=lambda q: 0.42 * spike_w(0.28 + 0.4 * q) * sw(q))
    # the runner on the shaft
    lathe('Umbrella', 'Black', [(Z_RUNNER - 0.14, 0.07), (Z_RUNNER - 0.1, 0.095), (Z_RUNNER + 0.1, 0.095),
                                (Z_RUNNER + 0.14, 0.07)], nu=12, caps=(True, True), name='runner')
    for k in range(N_RIBS):
        # the rib itself, a thin rod under the cloth, and a stretcher up to it from the runner
        tube('Umbrella', 'Steel', lambda t, k=k: tuple(rib_point(k, t * R, -0.03)), 0.022, nu=6, ts=[0.0, 0.5, 1.0],
             caps=(False, True), name='rib')
        top = rib_point(k, S_STRETCH, -0.03)
        bot = Vector((0, 0, Z_RUNNER)) + rib_dir(k) * 0.1
        tube('Umbrella', 'Steel', lambda t, top=top, bot=bot: tuple(bot.lerp(top, t)), 0.018, nu=6, name='stretcher')
        # the blade over the rib, and its yellow inlay (on top, and underneath where it runs past the cloth)
        rib_blade(k)


CANOPY_S = [0.04 + (R - 0.04) * (j / 6) ** 0.9 for j in range(7)]   # its rows, out along the ribs (the first under the hub)


def canopy_mesh():
    """the eight cloth panels as one sheet (set DoubleSided in Roblox so its underside shows). Each panel is the
    straight line between its two ribs at every distance out, bellied a touch upward: three columns across, six
    rows out, starting under the hub's lip so nothing pinches at the centre. When the ribs fold, the cloth between
    them folds in. UVs: every panel laid flat in the same square (they're printed alike)"""
    nu = 3
    half = math.pi / N_RIBS
    hw = (R_HUB + R) * math.sin(half)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    wl = bm.verts.layers.float.new('u')      # across the panel: 0 at rib k, 1 at rib k + 1
    kl = bm.verts.layers.int.new('k')
    for k in range(N_RIBS):
        mid = rib_dir(k + 0.5)
        tang = Vector((0, 0, 1)).cross(mid)
        g = []
        for i in range(nu + 1):
            col = []
            for j, s_ in enumerate(CANOPY_S):
                u = i / nu
                a, b = rib_point(k, s_), rib_point(k + 1, s_)
                v = bm.verts.new(a.lerp(b, u) + Vector((0, 0, 0.05 * math.sin(math.pi * u) * s_ / R)))
                v[wl], v[kl] = u, k
                col.append(v)
            g.append(col)

        def uv(p):
            q = p - Vector((0, 0, Z_HUB))
            return (0.5 + q.dot(tang) / (2 * hw * 1.04), clamp(q.dot(mid) / ((R_HUB + R) * math.cos(half) * 1.02)))
        for i in range(nu):
            for j in range(len(CANOPY_S) - 1):
                f = bm.faces.new((g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]))
                f.smooth = True
                for loop in f.loops:
                    loop[uvl].uv = uv(loop.vert.co)
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Umbrella_Canopy')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('Umbrella_Canopy', me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ the canopy's print

def canopy_textures(res):
    """paint the panel directly: off-white cloth, faint seams fanning from the hub, two bands of maroon lettering
    across it (with rules above and below), a hem along its edge. Returns Color / Normal / Roughness / Metalness"""
    from PIL import Image, ImageDraw, ImageFont
    H = W = res
    yy, xx = np.mgrid[0:H, 0:W]
    x = (xx + 0.5) / W               # across: 0.5 is the panel's middle
    y = 1 - (yy + 0.5) / H           # out from the hub: 0 .. 1 (image rows run top-down)
    rng = np.random.default_rng(4)
    base = np.array([0.93, 0.915, 0.875])
    col = np.ones((H, W, 3)) * base
    # soft cloth mottling
    from scipy import ndimage as ndi
    n = ndi.gaussian_filter(rng.standard_normal((H, W)), 18)
    n /= np.abs(n).max()
    col *= (1 + 0.006 * n)[..., None]
    height = 0.03 * n
    # seams: faint grey lines fanning out from the hub (the middle, and two either side)
    for f in (-0.36, 0.0, 0.36):
        xl = 0.5 + f * 0.5 * y
        d = np.abs(x - xl) * W
        line = np.clip(1 - d / 1.6, 0, 1) * (y > 0.08)
        col = col * (1 - 0.12 * line[..., None]) + np.array([0.6, 0.6, 0.61]) * 0.12 * line[..., None]
        height -= 0.25 * line
    # the hem along the outer edge
    hem = np.clip((y - 0.965) / 0.004, 0, 1)
    col = col * (1 - 0.05 * hem[..., None])
    height += 0.15 * hem
    stitch = hem * (np.sin(x * W / 5.0) > 0.3) * (np.abs(y - 0.975) < 0.002)
    col = col * (1 - 0.12 * stitch[..., None])
    # lettering: two bands of bold maroon glyphs, squeezed tall, ruled above and below
    ink = np.zeros((H, W))
    img = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(img)
    for yc, text, size in ((0.84, 'ЛЮЩАШОИ!!', 0.062), (0.6, 'АШЛЮОИ!', 0.05)):
        width = yc * 0.92                 # the panel's width there, in UV (it narrows toward the hub)
        fs = int(size * H)
        font = ImageFont.truetype(FONT, fs)
        tw, th_ = dr.textbbox((0, 0), text, font=font)[2:]
        glyphs = Image.new('L', (tw + 8, th_ + 8), 0)
        ImageDraw.Draw(glyphs).text((4, 0), text, fill=255, font=font)
        gw = int(width * 0.86 * W)
        glyphs = glyphs.resize((gw, int(size * 1.15 * H))).transpose(Image.FLIP_TOP_BOTTOM)   # read from outside, tops toward the hub
        cy = int((1 - yc) * H)
        img.paste(glyphs, (int(0.5 * W - gw / 2), cy - glyphs.size[1] // 2), glyphs)
        for off in (-0.62, 0.62):        # the rules
            ry = cy + int(off * size * H * 1.15)
            dr.rectangle((int(0.5 * W - gw / 2), ry - 2, int(0.5 * W + gw / 2), ry + 2), fill=255)
    ink = np.asarray(img, dtype=np.float64) / 255.0
    ink = ndi.gaussian_filter(ink, 0.7)
    maroon = np.array([0.42, 0.09, 0.11])
    col = col * (1 - ink[..., None]) + maroon * ink[..., None]
    height += 0.05 * ink
    # outside the panel's triangle: keep the cloth colour (margins)
    weave = 0.5 + 0.5 * np.sin(xx * 1.9) * np.sin(yy * 1.9)
    height += 0.0 * weave
    gy, gx = np.gradient(ndi.gaussian_filter(height, 1.0))
    nrm = np.dstack([-gx * 2.5, gy * 2.5, np.ones_like(gx)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    rough = 0.75 - 0.05 * ink
    out = {}
    lin_ = lambda c: np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    for name, arr, srgb in (('Color', np.clip(col, 0, 1), True), ('Normal', nrm * 0.5 + 0.5, False),
                            ('Roughness', np.dstack([rough] * 3), False), ('Metalness', np.zeros((H, W, 3)), False)):
        im = bpy.data.images.new(f'Umbrella_Canopy_{name}', W, H, alpha=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        px = np.ones((H, W, 4))
        px[..., :3] = lin_(arr) if srgb else arr
        im.pixels = px[::-1].astype(np.float32).ravel()   # Blender's rows run bottom-up
        im.filepath_raw = os.path.join(OUT, f'Umbrella_Canopy_{name}.png')
        im.file_format = 'PNG'
        im.save()
        out[name] = im
    return out


def maps_material(name, imgs):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    t = {}
    for ch, img in imgs.items():
        t[ch] = nt.nodes.new('ShaderNodeTexImage')
        t[ch].image = img
    nt.links.new(t['Color'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(t['Roughness'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(t['Metalness'].outputs[0], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(t['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    return m


# ------------------------------------------------------------------ the frame's materials

def material(name, base, edge_col, rough, metal, stripes=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(bsdf.outputs[0], out.inputs['Surface'])
    geo = N.new('ShaderNodeNewGeometry')
    tc = N.new('ShaderNodeTexCoord')

    def rng(x, a, b, c=0.0, d=1.0):
        n = N.new('ShaderNodeMapRange')
        n.clamp = True
        L.new(x, n.inputs['Value'])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = c, d
        return n.outputs[0]

    def mix(f, a, b):
        n = N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        L.new(f, n.inputs['Factor'])
        for sock, c in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(c, tuple):
                sock.default_value = c
            else:
                L.new(c, sock)
        return n.outputs[2]
    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.01
    bev.samples = 16
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.995, 0.92)
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.04
    ao.samples = 16
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    col = mix(rng(nz.outputs['Fac'], 0.3, 0.7, 0.0, 0.04), lin(base), lin(edge_col))
    col = mix(rng(edge, 0, 1, 0, 0.35), col, lin(edge_col))
    col = mix(rng(ao.outputs['AO'], 0.3, 1.0, 0.2, 0.0), col, (0.01, 0.01, 0.012, 1))
    if stripes:   # wrapped tape: a darker line where each turn overlaps the last
        uvn = N.new('ShaderNodeUVMap')
        uvn.uv_map = 'Detail'
        sep = N.new('ShaderNodeSeparateXYZ')
        L.new(uvn.outputs['UV'], sep.inputs[0])
        sk = N.new('ShaderNodeMath')
        sk.operation = 'MULTIPLY_ADD'
        L.new(sep.outputs['X'], sk.inputs[0])
        sk.inputs[1].default_value = 0.18
        L.new(sep.outputs['Y'], sk.inputs[2])
        fr = N.new('ShaderNodeMath')
        fr.operation = 'FRACT'
        dv = N.new('ShaderNodeMath')
        dv.operation = 'DIVIDE'
        L.new(sk.outputs[0], dv.inputs[0])
        dv.inputs[1].default_value = stripes[0]
        L.new(dv.outputs[0], fr.inputs[0])
        line = rng(fr.outputs[0], 0.0, 0.12, 0.6, 0.0)
        col = mix(line, col, lin(stripes[1]))
    rgh = rng(nz.outputs['Fac'], 0.3, 0.7, rough - 0.01, rough + 0.01)
    nrm = N.new('ShaderNodeBevel')
    nrm.inputs['Radius'].default_value = 0.005
    nrm.samples = 16
    tags = {}
    for tag, sock in (('COL', col), ('ROUGH', rgh), ('NRM', nrm.outputs['Normal'])):
        r = N.new('NodeReroute')
        r.name = 'OUT_' + tag
        L.new(sock, r.inputs[0])
        tags[tag] = r
    v = N.new('ShaderNodeValue')
    v.name = 'OUT_METAL'
    v.outputs[0].default_value = metal
    tags['METAL'] = v
    L.new(tags['COL'].outputs[0], bsdf.inputs['Base Color'])
    L.new(tags['ROUGH'].outputs[0], bsdf.inputs['Roughness'])
    L.new(tags['METAL'].outputs[0], bsdf.inputs['Metallic'])
    L.new(tags['NRM'].outputs[0], bsdf.inputs['Normal'])
    MATS[name] = m
    return m


def materials():
    material('Black', '#17171b', '#5a5b63', 0.4, 0.5)      # the blades: blackened steel, light edges
    material('Yellow', '#e6b422', '#ffe27a', 0.3, 0.2)      # their inlays: lacquered yellow
    material('Steel', '#3a3c42', '#6e7179', 0.4, 0.6)      # shaft, ribs, stretchers
    material('Tape', '#cfc6a2', '#ece5c8', 0.62, 0.0, stripes=(0.09, '#6e6a58'))   # the crook's tape wrap
    material('Cord', '#9c1e26', '#d0525a', 0.65, 0.0)       # the red binding


# ------------------------------------------------------------------ build, bake

def build_frame():
    out = {}
    for high, prefix in ((False, ''), (True, 'High_')):
        HIGH[0] = high
        A.PIECES.clear()
        frame_pieces()
        dg = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()
        mats = []
        tag = bm.verts.layers.int.new('rib')          # which rib a vertex rides on (-1: none)
        kind = bm.verts.layers.int.new('kind')        # 0 fixed, 1 runner, 2 rib, 3 stretcher
        for part, ob in A.PIECES:
            m = ob.data.materials[0]
            if m not in mats:
                mats.append(m)
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            for p in me.polygons:
                p.material_index = mats.index(m)
            A.smooth(me, 35)
            nm = ob.name.split('.')[0]
            k_kind = {'runner': 1, 'rib': 2, 'blade': 2, 'blade_inlay': 2, 'stretcher': 3}.get(nm, 0)
            first = len(bm.verts)
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            if k_kind in (2, 3):
                # which rib: the nearest rib direction to the piece's far end
                far = max((v.co for v in me.vertices), key=lambda c: Vector((c.x, c.y, 0)).length)
                ang = math.atan2(far.y, far.x) % TAU
                rib = int(round(ang / (TAU / N_RIBS))) % N_RIBS
            else:
                rib = -1
            for v in bm.verts[first:]:
                v[tag], v[kind] = rib, k_kind
            bpy.data.meshes.remove(me)
            bpy.data.objects.remove(ob)
        me = bpy.data.meshes.new(prefix + 'Umbrella')
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(prefix + 'Umbrella', me)
        bpy.context.scene.collection.objects.link(ob)
        out[prefix] = ob
    HIGH[0] = False
    return out[''], out['High_']


def bake(ob, hi, res):
    sc = bpy.context.scene
    bk = sc.render.bake
    bk.margin = 12
    bk.use_clear = True
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.02
    bk.max_ray_distance = 0.05
    A.unwrap(ob)
    imgs = {}
    for ch in ('Color', 'Normal', 'Roughness', 'Metalness'):
        img = bpy.data.images.new(f'Umbrella_{ch}', res, res, alpha=False)
        img.colorspace_settings.name = 'sRGB' if ch == 'Color' else 'Non-Color'
        imgs[ch] = img
    tm = bpy.data.materials.new('Umbrella_Target')
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
                nt.links.new(nt.nodes['OUT_' + {'Color': 'COL', 'Roughness': 'ROUGH', 'Metalness': 'METAL'}[ch]].outputs[0],
                             em.inputs['Color'])
                nt.links.new(em.outputs[0], out.inputs['Surface'])
                restore.append((nt, old, out))
            sc.cycles.samples = 24 if ch == 'Color' else 8
            bpy.ops.object.bake(type='EMIT', margin=12, use_selected_to_active=True)
        else:
            sc.cycles.samples = 16
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=12, use_selected_to_active=True)
        for nt, old, out in restore:
            nt.links.new(old, out.inputs['Surface'])
        img.filepath_raw = os.path.join(OUT, f'Umbrella_{ch}.png')
        img.file_format = 'PNG'
        img.save()
        print('BAKED', ch, flush=True)
    hi.hide_render = True
    hi.select_set(False)
    ob.select_set(False)
    ob.data.materials.clear()
    ob.data.materials.append(maps_material('Umbrella_Baked', imgs))


# ------------------------------------------------------------------ the rig

def closed_angle():
    """how far each rib swings down to close: until the canopy's edge sits just outside the shaft"""
    lo, hi = 0.0, math.radians(89)
    pivot = Vector((R_HUB, 0, 0))
    for _ in range(40):
        a = (lo + hi) / 2
        out, down = rib_profile(R)
        v = Vector((out, 0, down))
        r = Quaternion((0, 1, 0), a) @ v      # +a about +Y tips +X down
        if R_HUB + r.x > 0.36:
            lo = a
        else:
            hi = a
    return lo


def runner_z(a):
    """where the runner sits when the ribs are swung down by a, so every stretcher keeps its length"""
    def attach(a_):
        out, down = rib_profile(S_STRETCH)
        q = Quaternion((0, 1, 0), a_) @ Vector((out, 0, down - 0.03))
        return Vector((R_HUB + q.x, 0, Z_HUB + q.z))
    p0 = attach(0.0)
    L = (p0 - Vector((0.1, 0, Z_RUNNER))).length
    p = attach(a)
    dx = p.x - 0.1
    return p.z - math.sqrt(max(L * L - dx * dx, 0.0))


def rig(frame_ob, canopy):
    ad = bpy.data.armatures.new('UmbrellaRig')
    arm = bpy.data.objects.new('UmbrellaRig', ad)
    bpy.context.scene.collection.objects.link(arm)
    with bpy.context.temp_override(active_object=arm, object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        root = ad.edit_bones.new('Root')
        root.head, root.tail = (0, 0, 0), (0, 0, 1.0)
        run = ad.edit_bones.new('Runner')
        run.head, run.tail = (0, 0, Z_RUNNER), (0, 0, Z_RUNNER + 0.3)
        run.parent = root
        for k in range(N_RIBS):
            b = ad.edit_bones.new(f'Rib_{k + 1}')
            b.head = Vector((0, 0, Z_HUB)) + rib_dir(k) * R_HUB
            b.tail = rib_point(k, R)
            b.parent = root
            b.align_roll(Vector((0, 0, 1)))
        bpy.ops.object.mode_set(mode='OBJECT')
    names = [f'Rib_{k + 1}' for k in range(N_RIBS)]
    # the frame: fixed parts on Root, the runner on Runner, each rib and blade on its rib, each stretcher blended
    # from the runner (bottom) to its rib (top)
    g = {n: frame_ob.vertex_groups.new(name=n) for n in ['Root', 'Runner'] + names}
    me = frame_ob.data
    ribs = me.attributes['rib'].data
    kinds = me.attributes['kind'].data
    for v in me.vertices:
        kd, rb = kinds[v.index].value, ribs[v.index].value
        if kd == 0:
            g['Root'].add([v.index], 1.0, 'REPLACE')
        elif kd == 1:
            g['Runner'].add([v.index], 1.0, 'REPLACE')
        elif kd == 2:
            g[names[rb]].add([v.index], 1.0, 'REPLACE')
        else:
            top = rib_point(rb, S_STRETCH, -0.03).z
            f = clamp((v.co.z - Z_RUNNER) / (top - Z_RUNNER))
            g['Runner'].add([v.index], 1 - f, 'REPLACE')
            g[names[rb]].add([v.index], f, 'REPLACE')
    # the cloth: each panel shared between its two ribs, by how far across it lies
    gc = {n: canopy.vertex_groups.new(name=n) for n in names}
    us = canopy.data.attributes['u'].data
    ks = canopy.data.attributes['k'].data
    for v in canopy.data.vertices:
        u, k = us[v.index].value, ks[v.index].value
        if u < 1:
            gc[names[k]].add([v.index], 1 - u, 'REPLACE')
        if u > 0:
            gc[names[(k + 1) % N_RIBS]].add([v.index], u, 'REPLACE')
    for ob in (frame_ob, canopy):
        ob.parent = arm
        md = ob.modifiers.new('rig', 'ARMATURE')
        md.object = arm
    return arm


def pose(arm, t):
    """t = 0 open, 1 shut"""
    a = closed_angle() * t
    for k in range(N_RIBS):
        pb = arm.pose.bones[f'Rib_{k + 1}']
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (SIGN[0] * a, 0, 0)
    arm.pose.bones['Runner'].location = (0, runner_z(a) - Z_RUNNER, 0)


SIGN = [1.0]


def find_sign(arm):
    """which way about each rib's own X swings it down"""
    pb = arm.pose.bones['Rib_1']
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.5, 0, 0)
    bpy.context.view_layer.update()
    down = (arm.matrix_world @ pb.tail).z < (arm.matrix_world @ arm.data.bones['Rib_1'].tail_local).z
    pb.rotation_euler = (0, 0, 0)
    SIGN[0] = 1.0 if down else -1.0


def animate(arm):
    """OpenClose: open at 1, shut by 20, held to 40, open again by 60 (eased)"""
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 60
    arm.animation_data_create()
    act = bpy.data.actions.new('OpenClose')
    arm.animation_data.action = act
    ease = lambda x: x * x * (3 - 2 * x)
    for f in range(1, 61):
        if f <= 20:
            t = ease((f - 1) / 19)
        elif f <= 40:
            t = 1.0
        else:
            t = 1 - ease((f - 40) / 20)
        pose(arm, t)
        for k in range(N_RIBS):
            arm.pose.bones[f'Rib_{k + 1}'].keyframe_insert('rotation_euler', frame=f)
        arm.pose.bones['Runner'].keyframe_insert('location', frame=f)
    sc.frame_set(1)
    return act


# ------------------------------------------------------------------ preview, export

def preview(path, arm, samples):
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 720, 720
    shots = []
    for i, (frame, loc, tgt, lens) in enumerate(((1, (9.0, -11.0, 9.5), (0, 0, 4.3), 50),
                                                (1, (8.5, -10.0, 0.5), (0, 0, 3.6), 45),
                                                (20, (6.5, -11.5, 4.0), (0, 0, 3.4), 50))):
        sc.frame_set(frame)
        cam_d.lens = lens
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        f = path.replace('.png', f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    ims = [bpy.data.images.load(f) for f in shots]
    W, H = ims[0].size
    strip = np.zeros((H, W * 3, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        strip[:, k * W:(k + 1) * W] = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
    out = bpy.data.images.new('preview', W * 3, H, alpha=False)
    out.pixels = strip.ravel()
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()
    for f in shots:
        os.remove(f)
    # a close-up of one fin from the side, a little above, like the reference
    sc.frame_set(1)
    sc.render.resolution_x, sc.render.resolution_y = 900, 500
    tgt = rib_point(0, 1.0 * R, 0.1)
    cam.location = tgt + Vector((-0.6, -3.2, 1.3))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = 45
    sc.render.filepath = path.replace('.png', '_fin.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def main():
    A.reset()
    os.makedirs(OUT, exist_ok=True)
    materials()
    low, high = build_frame()
    canopy = canopy_mesh()
    for o in (low, high, canopy):
        print(o.name, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), flush=True)
    if STAGE == 'stats':
        return
    canopy.data.materials.append(maps_material('Umbrella_Canopy', canopy_textures(RES)))
    if STAGE == 'preview':
        low.hide_render = True
        high.hide_render = False
        arm = rig(high, canopy)
    else:
        bake(low, high, RES)
        arm = rig(low, canopy)
    find_sign(arm)
    animate(arm)
    preview(os.path.join(OUT, 'preview.png'), arm, int(A.opt('--samples', '24' if STAGE == 'preview' else '48')))
    if STAGE == 'preview':
        return
    for o in bpy.data.objects:
        o.select_set(o in (low, canopy, arm))
    fbx = os.path.join(OUT, 'Umbrella.fbx')
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH', 'ARMATURE'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True,
                             path_mode='STRIP', add_leaf_bones=False, armature_nodetype='NULL', bake_anim=True,
                             bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_simplify_factor=0.0)
    print('EXPORTED', fbx, flush=True)
    for o in (high,):
        bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Umbrella_rig.blend'))


if __name__ == '__main__':
    main()
