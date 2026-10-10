"""A quiver for the new bow, slung on the back of the R6 rig on a bandolier, with five of the bow's own arrows.

It matches the bow's look: stylised black metal with light steel edges and glowing deep-purple inlays, plus
black leather for the body and strap. The bandolier runs over the right shoulder, across the chest and under the
left arm. It lies on the R6 torso all the way round, because its path is a slice through a rounded box just
outside the torso. The quiver rides along its back stretch, mouth behind the right shoulder, tied on with two
leather bands. Everything is a clean quad grid with hard edges kept by auto smooth.

Built with the Dark Knight armour's plate and bake tools (1 unit = 1 stud, Z up, the character faces -Y):
    export/QuiverKit.fbx  Quiver (the quiver and bandolier, welded to the torso)
                          Quiver_Arrows (five arrows from ../new_bow/export/NewBow.fbx, 6x that file's size, using
                          its NewBow_Arrow_* textures, copied here as Quiver_Arrows_*)
                          Ref_Torso (the R6 torso it was fitted to)
    export/Quiver_Color / _Normal (OpenGL) / _Roughness / _Metalness / _Emissive.png

    python build_quiver.py -- [--stage preview|stats|all] [--res 1024]
"""
import bpy, bmesh, math, os, sys, random, shutil
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'armor'))
import build_armor as A                         # noqa: E402
from build_armor import slab, se, lin, TAU      # noqa: E402

STAGE = A.STAGE
RES = A.RES
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
BOW = os.path.join(HERE, '..', 'new_bow', 'export')
BODY = A.PARTS
A.PARTS = PARTS = {'Quiver': ((0, 0, 3), None)}
MATS, HIGH = A.MATS, A.HIGH
S = 6.0   # the arrows, at 6x NewBow.fbx's size (about 2.8 studs long)


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def tri(x):
    """a triangle wave, 0 .. 1 .. 0 over each unit"""
    f = x % 1.0
    return 1 - abs(2 * f - 1)


# ------------------------------------------------------------------ the bandolier's path

C_T = Vector((0, 0, 3))                     # torso centre
H_S = Vector((1.035, 0.535, 1.035))         # the rounded box the strap lies on: the torso plus a little
R_S = 0.08
P1 = Vector((-0.72, 0.0, 4.0))              # over the right shoulder, clear of the head
E_S = Vector((1.47, 0, -1.65)).normalized()  # down from there to the left hip, front and back
E_Y = Vector((0, 1, 0))
N_P = E_S.cross(E_Y).normalized()          # the strap's plane
ORIGIN = P1 + E_S * (-P1.x / E_S.x)         # the point of that plane over the torso's middle


def sdf(p):
    q = Vector([abs(p[i] - C_T[i]) - (H_S[i] - R_S) for i in range(3)])
    out = Vector([max(c, 0.0) for c in q])
    return out.length + min(max(q), 0.0) - R_S


def hit(o, d):
    """where the ray from o (inside) along d leaves the rounded box"""
    lo, hi = 0.0, 3.0
    for _ in range(48):
        m = (lo + hi) / 2
        if sdf(o + d * m) < 0:
            lo = m
        else:
            hi = m
    return o + d * lo


def strap_dir(phi):
    return E_S * math.cos(phi) + E_Y * math.sin(phi)


def strap_param(n=1440):
    """arc length round the strap's centre line -> angle, so its quads come out evenly spaced"""
    pts = [hit(ORIGIN, strap_dir(TAU * i / n)) for i in range(n + 1)]
    L = [0.0]
    for i in range(1, n + 1):
        L.append(L[-1] + (pts[i] - pts[i - 1]).length)

    def phi(u):
        s = u * L[-1]
        lo, hi = 0, n
        while hi - lo > 1:
            m = (lo + hi) // 2
            if L[m] < s:
                lo = m
            else:
                hi = m
        f = (s - L[lo]) / max(L[hi] - L[lo], 1e-9)
        return TAU * (lo + f) / n
    return phi


PHI = strap_param()
W_STRAP = 0.17


def strap_point(u, v):
    return hit(ORIGIN + N_P * (v - 0.5) * W_STRAP, strap_dir(PHI(u)))


# ------------------------------------------------------------------ the quiver's frame

L_Q = 2.1                                   # base to mouth
AX = -E_S                                   # base -> mouth: up toward the right shoulder
E2 = Vector((0, 1, 0))                      # out from the back
E1 = E2.cross(AX).normalized()              # across the back
BACK = Vector((0, 0.535 + 0.03 + 0.008, 0)) + Vector((0, 0, ORIGIN.z))   # its back edge, lying on the strap
CEN_T = L_Q / 2


def qw(t):
    return 0.23 + 0.07 * clamp(t / L_Q)      # half-width across


def qd(t):
    return 0.8 * qw(t)                       # half-depth out from the back


def qpoint(t, theta, extra=0.0, ex=2.6):
    """a point on the quiver's surface: t along it from the base, theta round it (90 deg = facing out), extra
    pushed further out"""
    sx, sy = se(theta, ex)
    c = BACK + AX * (t - CEN_T) + E2 * qd(t)
    return c + E1 * sx * (qw(t) + extra) + E2 * sy * (qd(t) + extra)


def axis_in(p):
    """the point on the quiver's axis level with p (for growing plates outward)"""
    p = Vector(p)
    t = (p - BACK).dot(AX) + CEN_T
    return BACK + AX * (t - CEN_T) + E2 * qd(t)


def ring(t0, t1, extra, mat, th, nu=40, top=None, ex=2.6, name='ring', bevel=0.006, start=-90):
    """a closed tube round the quiver from t0 to t1 (top(theta) can replace t1), seam at the back"""
    T0 = math.radians(start)

    def fn(u, v):
        th_ = T0 + TAU * u
        hi = top(th_) if top else t1
        t = t0 + (hi - t0) * v
        return tuple(qpoint(t, th_, extra(th_, t) if callable(extra) else extra, ex))
    return slab('Quiver', mat, fn, nu, 2, th, lambda p: tuple(axis_in(p)), closed_u=True, bevel=bevel, name=name)


def spike(mat, p, n, up, h, l, w, lean=0.0, name='gem'):
    """a four-sided pyramid standing on a surface (a cut gem, a setting)"""
    n, up = Vector(n).normalized(), Vector(up)
    t = (up - n * up.dot(n)).normalized()
    s = n.cross(t)
    p = Vector(p)
    bm = bmesh.new()
    b = [bm.verts.new(p + t * l - n * 0.01), bm.verts.new(p + s * w - n * 0.01), bm.verts.new(p - t * l - n * 0.01),
         bm.verts.new(p - s * w - n * 0.01)]
    top = bm.verts.new(p + n * h + t * lean)
    for k in range(4):
        bm.faces.new((b[k], b[(k + 1) % 4], top))
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl, dtl = bm.loops.layers.uv.new('UVMap'), bm.loops.layers.uv.new('Detail')
    bm.normal_update()
    for f in bm.faces:
        ax = (f.loops[0].vert.co - f.loops[1].vert.co).normalized()
        ay = f.normal.cross(ax)
        o = f.loops[0].vert.co
        for loop in f.loops:
            d = loop.vert.co - o
            loop[uvl].uv = loop[dtl].uv = (d.dot(ax), d.dot(ay))
    return A.finish('Quiver', mat, bm, 0, name)


def frame(mat, c, nrm, across, hw, hh, bar, th, r=0.03, nu=28, name='buckle'):
    """a rounded-rectangle frame (a buckle) in the plane through c facing nrm"""
    nrm, acr = Vector(nrm).normalized(), Vector(across).normalized()
    upv = nrm.cross(acr)
    c = Vector(c)

    def fn(u, v):
        q = []
        for hw_, hh_ in ((hw - bar, hh - bar), (hw, hh)):
            r_ = min(r, hw_ - 1e-3, hh_ - 1e-3)
            half = 2 * (hw_ - r_) + 2 * (hh_ - r_) + math.pi * r_
            x, y = A.rr_point(-half + 2 * half * u, hw_, hh_, r_)
            q.append(Vector((x, y)))
        p = q[0].lerp(q[1], v)
        return tuple(c + acr * p.x + upv * p.y)
    return slab('Quiver', mat, fn, nu, 1, th, lambda p: tuple(Vector(p) - nrm * 5), closed_u=True, bevel=0.005, name=name)


# ------------------------------------------------------------------ the pieces

def bandolier():
    slab('Quiver', 'Leather', strap_point, 160, 2, 0.03, lambda p: tuple(C_T), closed_u=True, bevel=0.006, name='strap')
    # a buckle on the chest, with a purple gem in a black setting beside it
    p = hit(ORIGIN, strap_dir(-math.pi / 2)) + Vector((0, -0.03, 0))
    along = (hit(ORIGIN, strap_dir(-math.pi / 2 + 0.05)) - hit(ORIGIN, strap_dir(-math.pi / 2 - 0.05))).normalized()
    frame('Black', p + Vector((0, -0.004, 0)), (0, -1, 0), along, 0.1, 0.13, 0.03, 0.025, name='buckle')
    g = p - along * 0.32
    spike('Black', g, (0, -1, 0), along, 0.035, 0.12, 0.085, name='setting')
    spike('Gem', g + Vector((0, -0.03, 0)), (0, -1, 0), along, 0.05, 0.08, 0.055, name='gem')
    # studs down the front stretch
    for k in (-3, -2, 2, 3):
        q = p + along * 0.16 * k
        A.rivet('Quiver', 'Black', tuple(q), (0, -1, 0), 0.025, flat=0.6)


def quiver():
    # the leather body
    ring(0.16, 1.84, 0.0, 'Leather', 0.03, nu=40, name='body')
    # the mouth: a flared black collar crowned with six points, a glowing purple band round it
    flare = lambda th_, t: 0.035 + 0.06 * clamp((t - 1.8) / 0.28) ** 2
    ring(1.8, None, flare, 'Black', 0.035, nu=48, top=lambda th_: 2.02 + 0.1 * tri(th_ / TAU * 6 + 0.5) ** 1.3,
         name='collar')
    ring(1.87, 1.91, lambda th_, t: flare(th_, t) + 0.034, 'Purple', 0.012, nu=48, name='collar_glow')
    # the base: an eight-faceted point, ringed in purple
    def cap(u, v):
        th_ = math.radians(-90 + 22.5) + TAU * u
        t = 0.28 - 0.48 * v
        k = 1.0 if t >= 0.02 else max(0.0, (t + 0.2) / 0.22)
        sx, sy = se(th_, 2.0)
        c = BACK + AX * (t - CEN_T) + E2 * qd(max(t, 0.0))
        return tuple(c + (E1 * sx * (qw(0.0) + 0.045) + E2 * sy * (qd(0.0) + 0.045)) * k)
    slab('Quiver', 'Black', cap, 8, 6, 0.035, lambda p: tuple(axis_in(p)), closed_u=True, bevel=0.006, name='cap')
    ring(0.24, 0.27, 0.09, 'Purple', 0.012, nu=8, ex=2.0, start=-90 + 22.5, name='cap_glow')
    # the spine down the front: a black plate with pointed ends and a glowing line, a purple gem in its middle
    def spine(w, lift, t0, t1, point):
        def fn(u, v):
            x = 2 * v - 1
            a, b = t0 + point * abs(x), t1 - point * abs(x)
            t = a + (b - a) * u
            return tuple(qpoint(t, math.radians(90 + x * w), lift))
        return fn
    slab('Quiver', 'Black', spine(16, 0.03, 0.3, 1.76, 0.1), 24, 4, 0.025, lambda p: tuple(axis_in(p)), bevel=0.005,
         name='spine')
    slab('Quiver', 'Purple', spine(3.5, 0.056, 0.44, 1.62, 0.04), 24, 1, 0.01, lambda p: tuple(axis_in(p)), bevel=0.003,
         name='spine_glow')
    g = qpoint(1.03, math.radians(90), 0.066)
    spike('Black', g, E2, AX, 0.04, 0.15, 0.1, name='setting')
    spike('Gem', g + E2 * 0.03, E2, AX, 0.06, 0.1, 0.066, name='gem')
    # two black bands with purple inlays, over the spine
    for t in (0.72, 1.32):
        ring(t - 0.04, t + 0.04, 0.075, 'Black', 0.03, nu=40, name='band')
        ring(t - 0.01, t + 0.01, 0.103, 'Purple', 0.008, nu=40, name='band_glow')
    # blade fins sweeping back from the mouth, one each side, like the bow's limbs
    for side in (0, 180):
        th_ = math.radians(side)
        out = E1 * (1 if side == 0 else -1)

        def fin(u, v, th_=th_, out=out):
            t = 1.3 + 0.62 * u
            h = 0.19 * (u / 0.82 if u <= 0.82 else (1 - u) / 0.18) ** 0.9
            p = qpoint(t, th_, 0.02) + out * h * v - AX * 0.12 * v * u
            return tuple(p - E2 * 0.015)
        slab('Quiver', 'Black', fin, 14, 2, 0.03, lambda p: tuple(Vector(p) - E2), bevel=0.005, name='fin')
    # leather ties binding it to the bandolier behind it
    for t in (0.45, 1.6):
        ring(t - 0.035, t + 0.035, lambda th_, t_: 0.04 + 0.085 * max(0.0, -math.sin(th_)) ** 4, 'Leather', 0.02, nu=40,
             name='tie')


def pieces():
    bandolier()
    quiver()


def arrows():
    """five of the bow's arrows standing in the quiver, nocks up, fanned a little"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(BOW, 'NewBow.fbx'))
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.name.startswith('arrow'))
    for o in new:
        if o is not src:
            bpy.data.objects.remove(o)
    src.parent = None
    src.data.transform(src.matrix_world)
    src.matrix_world = Matrix.Identity(4)
    rnd = random.Random(3)
    bm = bmesh.new()
    mouth = L_Q
    for ox, oy in ((-0.5, 0.25), (0.05, 0.42), (0.55, 0.2), (-0.25, -0.3), (0.32, -0.32)):
        me = src.data.copy()
        tip = AX + E1 * ox * 0.12 + E2 * oy * 0.1                       # fanned outward a touch
        tip.normalize()
        sd = E1.cross(tip).normalized()
        spin = Matrix.Rotation(rnd.uniform(0, TAU), 4, 'X')
        # arrow space: +X toward the nock, Y across the fletching
        basis = Matrix((tuple(tip) + (0,), tuple(sd) + (0,), tuple(tip.cross(sd)) + (0,), (0, 0, 0, 1))).transposed()
        nock = BACK + AX * (mouth + 1.15 + rnd.uniform(-0.08, 0.08) - CEN_T) + E2 * qd(mouth) \
            + E1 * ox * qw(mouth) * 0.6 + E2 * oy * qd(mouth) * 0.6
        m = Matrix.Translation(nock - tip * 0.235 * S) @ basis @ Matrix.Scale(S, 4) @ spin
        me.transform(m)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new('Quiver_Arrows')
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new('Quiver_Arrows')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    imgs = {}
    for ch in ('Color', 'Normal', 'Roughness', 'Metalness', 'Emissive'):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(os.path.join(BOW, f'NewBow_Arrow_{ch}.png'))
        if ch != 'Color':
            t.image.colorspace_settings.name = 'Non-Color'
        imgs[ch] = t
    nt.links.new(imgs['Color'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(imgs['Roughness'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(imgs['Metalness'].outputs[0], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(imgs['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    em = nt.nodes.new('ShaderNodeMix')
    em.data_type = 'RGBA'
    em.blend_type = 'MULTIPLY'
    em.inputs['Factor'].default_value = 1.0
    nt.links.new(imgs['Color'].outputs[0], em.inputs[6])
    nt.links.new(imgs['Emissive'].outputs[0], em.inputs[7])
    nt.links.new(em.outputs[2], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 0.9
    me.materials.append(mat)
    ob = bpy.data.objects.new('Quiver_Arrows', me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.data.objects.remove(src)
    for p in me.polygons:
        p.use_smooth = False
    return ob


# ------------------------------------------------------------------ materials (the new bow's look)

def material(name, kind):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(bsdf.outputs[0], out.inputs['Surface'])
    tc = N.new('ShaderNodeTexCoord')
    geo = N.new('ShaderNodeNewGeometry')
    det = N.new('ShaderNodeUVMap')
    det.uv_map = 'Detail'

    def op(o, a, b=None, clamp_=False):
        n = N.new('ShaderNodeMath')
        n.operation = o
        n.use_clamp = clamp_
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
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = c, d
        return n.outputs[0]

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

    def noise(scale, detail=2.0, vec=None):
        nz = N.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = detail
        L.new(vec or tc.outputs['Object'], nz.inputs['Vector'])
        return nz.outputs['Fac']

    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.012
    bev.samples = 16
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.995, 0.9)
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.04
    ao.samples = 16
    cav = rng(ao.outputs['AO'], 0.2, 1.0)
    # how far along the quiver: 0 at the base, 1 at the mouth
    dv = N.new('ShaderNodeVectorMath')
    dv.operation = 'DOT_PRODUCT'
    L.new(geo.outputs['Position'], dv.inputs[0])
    dv.inputs[1].default_value = tuple(AX)
    base_d = (BACK + AX * (-CEN_T)).dot(AX)
    along = rng(dv.outputs['Value'], base_d, base_d + L_Q)
    soft = rng(noise(6.0), 0.35, 0.65)
    emit = 0.0
    bump = None
    if kind == 'black':      # the bow's stylised black metal
        base = mix(along, lin('#121117'), lin('#1f1d27'))
        base = mix(op('MULTIPLY', soft, 0.35), base, lin('#2a2734'))
        edge_col = mix(0.35, lin('#8f8aa3'), lin('#7a55c8'))
        col = mix(op('MULTIPLY', edge, 0.85), base, edge_col)
        col = mix(op('SUBTRACT', 1.0, cav), col, lin('#07060a'))
        rough = op('SUBTRACT', rng(soft, 0, 1, 0.3, 0.38), op('MULTIPLY', edge, 0.1))
        metal = 0.85
    elif kind == 'leather':  # matte black leather, a purple-grey stitch along its edges
        cells = N.new('ShaderNodeTexVoronoi')
        cells.inputs['Scale'].default_value = 60
        L.new(tc.outputs['Object'], cells.inputs['Vector'])
        wrinkle = noise(8.0, 5.0)
        base = mix(op('MULTIPLY', soft, 0.5), lin('#0f0d12'), lin('#17141b'))
        col = mix(op('MULTIPLY', edge, 0.4), base, lin('#3a3344'))
        col = mix(op('SUBTRACT', 1.0, cav), col, lin('#050407'))
        sep = N.new('ShaderNodeSeparateXYZ')
        L.new(det.outputs['UV'], sep.inputs[0])
        fr = N.new('ShaderNodeMath')
        fr.operation = 'FRACT'
        L.new(op('DIVIDE', sep.outputs['X'], 0.035), fr.inputs[0])
        dash = op('MULTIPLY', rng(fr.outputs[0], 0.1, 0.2), rng(fr.outputs[0], 0.7, 0.6))
        band = lambda a, b: op('MULTIPLY', rng(sep.outputs['Y'], a - 0.003, a), rng(sep.outputs['Y'], b + 0.003, b))
        stitch = op('MULTIPLY', dash, band(0.018, 0.026))
        col = mix(op('MULTIPLY', stitch, 0.9), col, lin('#4b3a66'))
        rough = rng(wrinkle, 0.3, 0.7, 0.5, 0.72)
        metal = 0.0
        bump = op('ADD', op('MULTIPLY', cells.outputs['Distance'], 0.4), op('ADD', op('MULTIPLY', wrinkle, 0.5),
                                                                          op('MULTIPLY', stitch, 0.5)))
    else:                    # the bow's glowing purple (a cut gem glows brighter)
        base = mix(rng(along, 0.0, 0.55), lin('#1c043f'), lin('#3c0d8c'))
        base = mix(rng(along, 0.55, 1.0), base, lin('#5e1fbd'))
        if kind == 'gem':
            base = mix(0.5, base, lin('#6a2bd0'))
        col = mix(op('MULTIPLY', edge, 0.45), base, lin('#8a55d4'))
        col = mix(op('MULTIPLY', op('SUBTRACT', 1.0, cav), 0.6), col, lin('#1a0636'))
        rough = rng(soft, 0, 1, 0.12 if kind == 'gem' else 0.22, 0.2 if kind == 'gem' else 0.3)
        metal, emit = 0.35, 0.7
    nrm = N.new('ShaderNodeBevel')
    nrm.inputs['Radius'].default_value = 0.004
    nrm.samples = 16
    nrm_out = nrm.outputs['Normal']
    if bump is not None:
        bn = N.new('ShaderNodeBump')
        bn.inputs['Strength'].default_value = 0.3
        bn.inputs['Distance'].default_value = 0.003
        L.new(bump, bn.inputs['Height'])
        L.new(nrm.outputs['Normal'], bn.inputs['Normal'])
        nrm_out = bn.outputs['Normal']
    tags = {}
    for tag, sock in (('COL', col), ('ROUGH', rough), ('NRM', nrm_out)):
        r = N.new('NodeReroute')
        r.name = 'OUT_' + tag
        L.new(sock, r.inputs[0])
        tags[tag] = r
    for tag, v in (('METAL', metal), ('EMIT', emit)):
        n = N.new('ShaderNodeValue')
        n.name = 'OUT_' + tag
        n.outputs[0].default_value = v
        tags[tag] = n
    L.new(tags['COL'].outputs[0], bsdf.inputs['Base Color'])
    L.new(tags['ROUGH'].outputs[0], bsdf.inputs['Roughness'])
    L.new(tags['METAL'].outputs[0], bsdf.inputs['Metallic'])
    L.new(tags['NRM'].outputs[0], bsdf.inputs['Normal'])
    if emit:
        L.new(tags['COL'].outputs[0], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 0.9
    MATS[name] = m
    return m


def materials():
    material('Black', 'black')
    material('Leather', 'leather')
    material('Purple', 'purple')
    material('Gem', 'gem')
    MATS['Steel'] = MATS['Black']   # (the armour tools' trims would use it)


# ------------------------------------------------------------------ build, bake, export

def build():
    materials()
    out = {}
    for high, prefix in ((False, ''), (True, 'High_')):
        HIGH[0] = high
        A.PIECES.clear()
        pieces()
        dg = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()
        mats = []
        for part, ob in A.PIECES:
            m = ob.data.materials[0]
            if m not in mats:
                mats.append(m)
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            for p in me.polygons:
                p.material_index = mats.index(m)
            A.smooth(me, 60 if m.name == 'Leather' else 35)
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
            bpy.data.objects.remove(ob)
        me = bpy.data.meshes.new(prefix + 'Quiver')
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(prefix + 'Quiver', me)
        bpy.context.scene.collection.objects.link(ob)
        out[prefix] = ob
    HIGH[0] = False
    return out[''], out['High_']


def bake(ob, hi, res):
    """the detailed quiver onto the game mesh: colour, normal, roughness, metalness and the emissive mask"""
    sc = bpy.context.scene
    bk = sc.render.bake
    bk.margin = 12
    bk.use_clear = True
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.02
    bk.max_ray_distance = 0.05
    os.makedirs(OUT, exist_ok=True)
    A.unwrap(ob)
    imgs = {}
    for ch in ('Color', 'Normal', 'Roughness', 'Metalness', 'Emissive'):
        img = bpy.data.images.new(f'Quiver_{ch}', res, res, alpha=False)
        img.colorspace_settings.name = 'sRGB' if ch == 'Color' else 'Non-Color'
        imgs[ch] = img
    tm = bpy.data.materials.new('Quiver_Target')
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
    src = {'Color': 'COL', 'Roughness': 'ROUGH', 'Metalness': 'METAL', 'Emissive': 'EMIT'}
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
                s = nt.nodes['OUT_' + src[ch]].outputs[0]
                if ch == 'Emissive':   # the mask: white where it glows
                    gt = nt.nodes.get('BAKE_GT') or nt.nodes.new('ShaderNodeMath')
                    gt.name = 'BAKE_GT'
                    gt.operation = 'GREATER_THAN'
                    gt.inputs[1].default_value = 0.0
                    nt.links.new(s, gt.inputs[0])
                    s = gt.outputs[0]
                nt.links.new(s, em.inputs['Color'])
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
        img.filepath_raw = os.path.join(OUT, f'Quiver_{ch}.png')
        img.file_format = 'PNG'
        img.save()
        print('BAKED', ch, flush=True)
    hi.hide_render = True
    hi.select_set(False)
    ob.select_set(False)
    m = bpy.data.materials.new('Quiver_Baked')
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
    em = nt.nodes.new('ShaderNodeMix')
    em.data_type = 'RGBA'
    em.blend_type = 'MULTIPLY'
    em.inputs['Factor'].default_value = 1.0
    nt.links.new(t['Color'].outputs[0], em.inputs[6])
    nt.links.new(t['Emissive'].outputs[0], em.inputs[7])
    nt.links.new(em.outputs[2], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 0.9
    ob.data.materials.clear()
    ob.data.materials.append(m)


def preview(path, samples):
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 640, 760
    shots = []
    for i, (az, el) in enumerate(((0, 8), (150, 10), (215, 12))):
        a = math.radians(az - 90)
        d = 15.0
        cam.location = (d * math.cos(a) * math.cos(math.radians(el)), d * math.sin(a) * math.cos(math.radians(el)),
                        3.0 + d * math.sin(math.radians(el)))
        cam.rotation_euler = (Vector((0, 0, 3.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        f = path.replace('.png', f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    import numpy as np
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
    sc.render.resolution_x, sc.render.resolution_y = 900, 900
    cam.location = (4.5, 7.5, 5.2)
    cam.rotation_euler = (Vector((0.0, 0.6, 3.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path.replace('.png', '_closeup.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def load_rig():
    A.PARTS = BODY
    refs = A.load_rig()
    A.PARTS = PARTS
    return refs


def main():
    A.reset()
    low, high = build()
    arw = arrows()
    refs = load_rig()
    for o in (low, high, arw):
        print(o.name, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), flush=True)
    if STAGE == 'stats':
        return
    os.makedirs(OUT, exist_ok=True)
    if STAGE == 'preview':
        low.hide_render = True
        preview(os.path.join(OUT, 'preview.png'), int(A.opt('--samples', '32')))
        return
    bake(low, high, RES)
    preview(os.path.join(OUT, 'preview.png'), 48)
    for ch in ('Color', 'Normal', 'Roughness', 'Metalness', 'Emissive'):
        shutil.copy(os.path.join(BOW, f'NewBow_Arrow_{ch}.png'), os.path.join(OUT, f'Quiver_Arrows_{ch}.png'))
    for o in bpy.data.objects:
        o.select_set(o in (low, arw, refs.get('Torso')))
    fbx = os.path.join(OUT, 'QuiverKit.fbx')
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_ALL',
                             mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
    print('EXPORTED', fbx, flush=True)


if __name__ == '__main__':
    main()
