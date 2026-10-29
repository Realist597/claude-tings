"""The Brute: an original hulking barbarian, built on the user's own muscle body (source/muscle_body.obj with its
normal maps), for the Roblox R6 rig.

Steps (each writes a viewport snapshot to export/steps/):
    body      the body, its normal maps, and a dark grey-brown skin colour map painted from them (creases darker,
              ridges catching the light)

    python build_brute.py -- --stage body
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as A                 # noqa: E402
from build_armor import lin, TAU        # noqa: E402

STAGE = A.STAGE
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
SRC = os.path.join(HERE, 'source')
STEPS = os.path.join(OUT, 'steps')
MATS = A.MATS

# the body's parts as exported from Studio, and the normal map each uses (matched by UV layout)
PARTS = {'Torso1': ('Torso', 'normal_torso'), 'ArmL1': ('LeftArm', 'normal_a'), 'ArmR1': ('RightArm', 'normal_a'),
         'LegL1': ('LeftLeg', 'normal_b'), 'LegR1': ('RightLeg', 'normal_b')}
SKIN = dict(base='#5d514c', crease='#231c1a', ridge='#86776f', warm='#6a4e44')


# ------------------------------------------------------------------ the body

def import_body():
    """the user's body, centred on the origin (feet at z 0) and turned to face -Y like everything else here"""
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(SRC, 'muscle_body.obj'), use_split_groups=True)
    obs = [o for o in bpy.data.objects if o not in before]
    pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    z0 = min(p.z for p in pts)
    m = Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation((-cx, -cy, -z0))
    body = {}
    for o in obs:
        o.data.transform(m @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        part, nmap = PARTS[o.name.split('.')[0]]
        o.name = o.data.name = 'Brute_' + part
        for p in o.data.polygons:
            p.use_smooth = True
        body[part] = (o, nmap)
    return body


def skin_maps(nmap):
    """from a part's normal map: a colour map (dark grey-brown skin, its creases deepened and its ridges lit, mottled)
    and a roughness map (a slight sheen on the ridges). Returns the two as Blender images"""
    from scipy import ndimage as ndi
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(SRC, nmap + '.png')).convert('RGB'), dtype=np.float64) / 255.0
    nx, ny = a[..., 0] * 2 - 1, -(a[..., 1] * 2 - 1)       # image rows run down; OpenGL green runs up
    curv = ndi.gaussian_filter(np.gradient(nx, axis=1) + np.gradient(ny, axis=0), 1.5)
    curv /= np.percentile(np.abs(curv), 99) + 1e-6
    broad = ndi.gaussian_filter(curv, 6)
    H, W = curv.shape
    rng = np.random.default_rng(11)
    mott = ndi.gaussian_filter(rng.standard_normal((H, W)), 9)
    mott /= np.abs(mott).max()
    fine = ndi.gaussian_filter(rng.standard_normal((H, W)), 1.2)
    fine /= np.abs(fine).max()
    c = lambda h: np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    col = np.ones((H, W, 3)) * c(SKIN['base'])
    crease = np.clip(-curv * 1.4 - broad * 0.6, 0, 1)[..., None]
    ridge = np.clip(curv * 1.1, 0, 1)[..., None]
    col = col * (1 - 0.55 * crease) + c(SKIN['crease']) * 0.55 * crease
    col = col * (1 - 0.35 * ridge) + c(SKIN['ridge']) * 0.35 * ridge
    m = np.clip(mott, 0, 1)[..., None]
    col = col * (1 - 0.18 * m) + c(SKIN['warm']) * 0.18 * m
    col *= (1 + 0.04 * fine)[..., None]
    # skin texture: pores and grain, a few old scars (lighter, raised), all kept inside the UV islands
    island = ndi.binary_erosion(np.abs(a - np.array([0.5, 0.5, 1.0])).sum(2) > 0.02, iterations=6)
    pores = ndi.gaussian_filter(rng.standard_normal((H, W)), 0.7)
    pores = np.clip(-pores / (np.abs(pores).max() + 1e-6) * 3, 0, 1) ** 1.5
    grain = ndi.gaussian_filter(rng.standard_normal((H, W)), 2.5)
    grain /= np.abs(grain).max()
    scar = np.zeros((H, W))
    ys, xs = np.nonzero(island)
    for k in range(5 if nmap == 'normal_torso' else 3):
        i = rng.integers(len(xs))
        x0, y0 = xs[i], ys[i]
        ang, length = rng.uniform(0, math.pi), rng.uniform(40, 110)
        bend = rng.uniform(-0.4, 0.4)
        for t in np.linspace(-0.5, 0.5, 200):
            a_ = ang + bend * t
            x, y = int(x0 + math.cos(a_) * length * t), int(y0 + math.sin(a_) * length * t)
            if 0 <= x < W and 0 <= y < H and island[y, x]:
                scar[y, x] = 1.0
        # a few stitch marks across the longest ones
    scar = np.clip(ndi.gaussian_filter(scar, 1.6) * 5, 0, 1)
    col = col * (1 - 0.06 * pores[..., None])
    col = col * (1 - 0.35 * scar[..., None]) + c('#8c776f') * 0.35 * scar[..., None]
    rough = np.clip(0.58 + 0.12 * crease[..., 0] - 0.1 * ridge[..., 0] + 0.03 * fine + 0.06 * pores - 0.12 * scar, 0, 1)
    # the detail's normals (pores and grain dimple in, scars stand proud), laid over the body's own normal map
    height = -0.6 * pores + 0.25 * grain + 1.8 * scar
    gy, gx = np.gradient(ndi.gaussian_filter(height, 0.8))
    d = np.dstack([-gx * 0.9, gy * 0.9, np.ones_like(gx)])
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    base = a * 2 - 1
    t_ = base + np.array([0, 0, 1.0])            # reoriented normal blending: the detail follows the muscles' slopes
    u_ = d * np.array([-1, -1, 1.0])
    nrm = t_ * (t_ * u_).sum(2, keepdims=True) / t_[..., 2:3] - u_
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = np.where(island[..., None], nrm, base)
    out = []
    for name, arr, srgb in ((nmap + '_skin', np.clip(col, 0, 1), True), (nmap + '_rough', np.dstack([rough] * 3), False),
                            (nmap + '_detail', nrm * 0.5 + 0.5, False)):
        im = bpy.data.images.new(name, W, H, alpha=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        px = np.ones((H, W, 4))
        px[..., :3] = np.where(arr > 0.04045, ((arr + 0.055) / 1.055) ** 2.4, arr / 12.92) if srgb else arr
        im.pixels = px[::-1].astype(np.float32).ravel()
        os.makedirs(os.path.join(OUT, 'textures'), exist_ok=True)
        im.filepath_raw = os.path.join(OUT, 'textures', name + '.png')
        im.file_format = 'PNG'
        im.save()
        out.append(im)
    return out


def skin_material(nmap):
    if 'Skin_' + nmap in MATS:
        return MATS['Skin_' + nmap]
    col, rough, nrm = skin_maps(nmap)
    m = bpy.data.materials.new('Skin_' + nmap)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage')
    tc.image = col
    tr = nt.nodes.new('ShaderNodeTexImage')
    tr.image = rough
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = nrm
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tc.outputs[0], b.inputs['Base Color'])
    nt.links.new(tr.outputs[0], b.inputs['Roughness'])
    nt.links.new(tn.outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], b.inputs['Normal'])
    MATS['Skin_' + nmap] = m
    return m


# ------------------------------------------------------------------ fitting gear to the body

BVH = {}


def body_bvh(body):
    from mathutils.bvhtree import BVHTree
    for part, (o, _) in body.items():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        BVH[part] = BVHTree.FromBMesh(bm)
        bm.free()


def surf(parts, c, theta, z):
    """how far out the body's skin is from the vertical axis through c, looking out at angle theta (0 = +X, -90 deg
    = front) at height z: a ray fired in from outside, so it finds the outermost skin"""
    d = Vector((math.cos(theta), math.sin(theta), 0))
    best = 0.0
    for part in parts:
        hit = BVH[part].ray_cast(Vector((c[0], c[1], z)) + d * 8, -d, 16)
        if hit[0] is not None:
            best = max(best, (Vector((hit[0].x - c[0], hit[0].y - c[1], 0))).length)
    return best


def girth(parts, c, z0, z1, nu, offset, smooth=4):
    """a ring's radius round the axis through c at nu angles: the widest the skin gets between z0 and z1, plus
    offset, smoothed round the ring so a rigid band doesn't follow every muscle"""
    zs = [z0 + (z1 - z0) * k / 4 for k in range(5)]
    r = [max(surf(parts, c, TAU * i / nu, z) for z in zs) + offset for i in range(nu)]
    out = []
    for i in range(nu):
        w = [r[(i + k) % nu] for k in range(-smooth, smooth + 1)]
        out.append(max(max(w) * 0.6 + sum(w) / len(w) * 0.4, r[i]))
    return out


def surface(part, mat, fn, us, vs, closed_u=False, closed_v=False, out=None, name='surface', sharp=None):
    """a single-walled quad grid over fn(u, v) at the given u and v; closed in either direction; out(p) a point it
    faces away from. UVs in studs. sharp(j): rows whose edges round the loop stay hard"""
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
        score = sum(f.normal.dot(f.calc_center_median() - Vector(out(f.calc_center_median()))) * f.calc_area()
                    for f in bm.faces)
        if score < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    return A.finish(part, mat, bm, 0, name)


def rrect(w, h, r, n=4):
    """a rounded rectangle's outline (width w across, height h), as a loop of (x, y), r its corner radius"""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def wobble(seed, u, v=0.0, n=4, amp=1.0):
    """smooth irregularity round a loop (u in 0..1, periodic) and across it: a few sine waves with random phases"""
    import random
    rnd = random.Random(seed)
    s_ = 0.0
    for k in range(n):
        f = rnd.randint(2, 9 + 4 * k)
        s_ += math.sin(TAU * f * u + rnd.uniform(0, TAU)) * math.cos(v * rnd.uniform(1, 4) + rnd.uniform(0, TAU)) / (k + 1)
    return s_ * amp


def ring(part, mat, c, zc, radii, profile, name='ring', nu=None, dent=0.0, wave=0.0, seed=0):
    """a band swept round the axis through c: its cross-section the loop `profile` of (out, up) offsets, laid on
    the radius at each angle (radii, from girth) at height zc. Smooth all round: rounded rims, bevelled edges"""
    nr = len(radii)
    nu = nu or nr * 2
    n = len(profile)

    def fn(u, j):
        t = TAU * u
        x = u * nr
        k = int(x) % nr
        f = x - int(x)
        r = radii[k] * (1 - f) + radii[(k + 1) % nr] * f
        dr, dz = profile[j % n]
        if dent:     # hammered dents in its face, more on the outside than the inside
            dr += wobble(seed, u, dz * 20, 5, dent) * clamp(dr / 0.05)
        if wave:     # its edges wander up and down
            dz += wobble(seed + 7, u, 0, 3, wave) * (1 if dz > 0 else -1) * clamp(abs(dz) / 0.05)
        return (c[0] + (r + dr) * math.cos(t), c[1] + (r + dr) * math.sin(t), zc + dz)
    return surface(part, mat, fn, [i / nu for i in range(nu + 1)], list(range(n + 1)), closed_u=True, closed_v=True,
                   out=lambda p: (c[0], c[1], p[2]), name=name)


def boss(part, c, n, name='boss'):
    """the belt's turned bronze boss: a domed centre, a raised ring, a stepped rim"""
    n = Vector(n).normalized()
    s1 = n.cross(Vector((0, 0, 1))).normalized()
    s2 = n.cross(s1)
    c = Vector(c)
    prof = [(0.0, 0.17), (0.05, 0.168), (0.1, 0.16), (0.14, 0.14), (0.17, 0.115), (0.19, 0.1), (0.205, 0.115),
            (0.225, 0.13), (0.245, 0.115), (0.26, 0.09), (0.29, 0.085), (0.33, 0.08), (0.355, 0.065), (0.37, 0.035),
            (0.37, 0.0), (0.3, -0.01)]

    def fn(u, j):
        a = TAU * u
        r, hgt = prof[j]
        return tuple(c + (s1 * math.cos(a) + s2 * math.sin(a)) * r + n * hgt)
    return surface(part, 'Bronze', fn, [i / 48 for i in range(49)], list(range(len(prof))), closed_u=True,
                   out=lambda p: tuple(c - n * 5), name=name)


def stud(part, mat, c, radii, z, theta_deg, r=0.06, lift=0.0):
    nu = len(radii)
    t = math.radians(theta_deg)
    i = (t % TAU) / TAU * nu
    rr = radii[int(i) % nu] + lift
    p = (c[0] + rr * math.cos(t), c[1] + rr * math.sin(t), z)
    domed_stud(part, mat, p, (math.cos(t), math.sin(t), 0), r)


def domed_stud(part, mat, p, n, r):
    """a domed rivet head on a thin washer"""
    n = Vector(n).normalized()
    s1 = n.cross(Vector((0, 0, 1)))
    s1 = s1.normalized() if s1.length > 1e-6 else Vector((1, 0, 0))
    s2 = n.cross(s1)
    p = Vector(p)
    prof = [(0.0, 0.62), (0.35, 0.58), (0.65, 0.46), (0.85, 0.3), (0.95, 0.16), (1.0, 0.08), (1.25, 0.08), (1.3, 0.0),
            (1.3, -0.15)]

    def fn(u, j):
        a = TAU * u
        rr, hh = prof[j]
        return tuple(p + (s1 * math.cos(a) + s2 * math.sin(a)) * rr * r + n * hh * r)
    return surface(part, mat, fn, [i / 16 for i in range(17)], list(range(len(prof))), closed_u=True,
                   out=lambda q: tuple(p - n * 5), name='stud')


# ------------------------------------------------------------------ the gear (an original design)

ARM_C = (2.705, 0.0)      # the left arm's and leg's axes (the right are mirrored)
LEG_C = (0.94, 0.0)


def cuff(part, parts, c, z0, z1):
    """an iron cuff between two rounded bronze rims, a ring of domed bronze studs round its middle"""
    r = girth(parts, c, z0, z1, 48, 0.05)
    H = z1 - z0
    band = [(x + 0.035, y) for x, y in rrect(0.07, H - 0.16, 0.025)]
    seed = int(c[0] * 100 + z0 * 10)
    ring(part, 'Iron', c, (z0 + z1) / 2, r, band, name='cuff', nu=128, dent=0.012, wave=0.01, seed=seed)
    for k, zz in enumerate((z0 + 0.065, z1 - 0.065)):
        ring(part, 'Bronze', c, zz, r, [(x + 0.07, y) for x, y in rrect(0.13, 0.13, 0.05)], name='cuff_rim', nu=128,
             dent=0.008, wave=0.012, seed=seed + 3 + k)
    import random
    rnd = random.Random(seed)
    for k in range(12):
        stud(part, 'Bronze', c, r, (z0 + z1) / 2 + rnd.uniform(-0.02, 0.02), k * 30 + 15 + rnd.uniform(-4, 4),
             r=0.055 * rnd.uniform(0.85, 1.1), lift=0.07)


ELBOW_Z = 5.25             # the elbow's point, on the back of the arm (from the muscle normal map)


def elbow_spike(part, parts, c, zc):
    """a forged iron guard cupped over the back of the elbow, strapped on, and a long edged spike swept back and down
    off it out of a domed collar"""
    import random
    rnd = random.Random(int(zc * 100))
    r = girth(parts, c, zc - 0.36, zc + 0.36, 72, 0.015, smooth=1)
    nr = len(r)

    def rad(t):
        x = (t % TAU) / TAU * nr
        k = int(x) % nr
        f = x - int(x)
        return r[k] * (1 - f) + r[(k + 1) % nr] * f

    a0, a1 = math.radians(38), math.radians(142)       # round the back of the arm (90 = straight back)
    H, T = 0.4, 0.05                                    # the plate's half height and thickness
    prof = [(x + T / 2, y / H) for x, y in rrect(T, 2 * H, 0.022, 3)]

    def cup(u, v):
        """how far the plate bulges out over the point of the elbow (u round it, v up it, both 0 at the middle)"""
        return 0.07 * math.cos(min(abs(u), 1) * math.pi / 2) ** 1.5 * math.cos(min(abs(v), 1) * math.pi / 2)

    def plate(u, j):
        t = a0 + (a1 - a0) * u
        uu = 2 * u - 1
        dr, dz = prof[j % len(prof)]
        cr = 0.3                                        # its corners rounded off
        e = math.sqrt(max(0.0, 1 - ((abs(uu) - (1 - cr)) / cr) ** 2)) if abs(uu) > 1 - cr else 1.0
        hz = dz * H * e
        rr = rad(t) + dr * (0.35 + 0.65 * e) + cup(uu, hz / H) + wobble(7, u, hz * 6, 4, 0.006)
        return (c[0] + rr * math.cos(t), c[1] + rr * math.sin(t), zc + hz)
    surface(part, 'Iron', plate, [0.5 - 0.5 * math.cos(math.pi * i / 48) for i in range(49)],
            list(range(len(prof) + 1)), closed_v=True,
            out=lambda q: (c[0], c[1], q[2]), name='elbow_guard')

    def on_plate(u, v):
        t = a0 + (a1 - a0) * u
        uu = 2 * u - 1
        rr = rad(t) + T + cup(uu, v)
        n = Vector((math.cos(t), math.sin(t), 0))
        return Vector((c[0], c[1], zc + v * H)) + n * rr, n

    # the straps that hold it on, round the arm above and below the cup
    for k, v in enumerate((0.62, -0.62)):
        zz = zc + v * H
        rs = []
        for i in range(nr):
            t = TAU * i / nr
            on = a0 + 0.08 < t < a1 - 0.08
            rs.append(r[i] + 0.01 + ((T + cup(2 * (t - a0) / (a1 - a0) - 1, v)) if on else 0.0))
        ring(part, 'Leather', c, zz, rs, [(x + 0.03, y) for x, y in rrect(0.06, 0.13, 0.025)], name='elbow_strap',
             nu=96, dent=0.004, wave=0.008, seed=40 + k)
    for u, v in ((0.12, 0.3), (0.88, 0.3), (0.12, -0.3), (0.88, -0.3)):
        q, n = on_plate(u, v)
        domed_stud(part, 'Bronze', q, n, 0.05)

    # the spike: a diamond section with bevelled edges, tall and narrow like a blade on edge, tapering to a point
    root, n = on_plate(0.38, 0.0)
    d = Vector((0.6, 1.0, -0.32)).normalized()
    L = 2.6

    def axis(t):     # swept back and down, the tip curling up again like a horn
        return root - d * 0.08 + d * (L * t) + Vector((0.06, 0, -0.42)) * t * t + Vector((0, 0, 0.36)) * t ** 3

    def tangent(t):
        return (axis(min(t + 0.01, 1)) - axis(max(t - 0.01, 0))).normalized()

    corners = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    sec = []
    for k, (a, b) in enumerate(corners):
        pa, pb = corners[k - 1], corners[(k + 1) % 4]
        sec.append((a + (pa[0] - a) * 0.1, b + (pa[1] - b) * 0.1))
        sec.append((a + (pb[0] - a) * 0.1, b + (pb[1] - b) * 0.1))

    def spike(u, j):
        tg = tangent(u)
        up = (Vector((0, 0, 1)) - tg * tg.z).normalized()
        side = tg.cross(up)
        w = (1 - u) ** 0.6 * (1 + 0.25 * (1 - u) ** 6)
        a, b = sec[j % len(sec)]
        return tuple(axis(u) + up * (a * 0.22 * w) + side * (b * 0.115 * w))
    us = [(i / 36) ** 1.15 for i in range(37)]
    surface(part, 'Iron', spike, us, list(range(len(sec) + 1)), closed_v=True,
            out=lambda q: tuple(axis(0.5)), name='elbow_spike')
    domed_stud(part, 'Iron', root - d * 0.02, d, 0.27)    # the collar it comes out of


def belt():
    nu = 64
    c = (0.0, 0.0)
    for z0, z1, name in ((3.6, 3.96, 'belt'), (3.93, 4.29, 'belt_upper')):
        r = girth(['Torso'], c, z0, z1, nu, 0.03)
        ring('Torso', 'Leather', c, (z0 + z1) / 2, r, [(x + 0.045, y) for x, y in rrect(0.09, z1 - z0, 0.03)], name=name,
             nu=160, dent=0.006, wave=0.02, seed=int(z0 * 100))
        if name == 'belt':
            for k in range(16):
                stud('Torso', 'Bronze', c, r, 3.78, k * 22.5 + 11.25, r=0.06, lift=0.09)
            fy = -max(r[nu * 3 // 4 - 2: nu * 3 // 4 + 3]) - 0.09
    boss('Torso', (0.0, fy, 3.95), (0, -1, 0))


def loincloth():
    """front and back flaps of heavy oxblood cloth from under the belt to the knees: pleated, torn at the hem"""
    import random
    for side, w, zb in ((-1, 0.82, 1.55), (1, 1.05, 1.75)):
        rnd = random.Random(3 if side < 0 else 8)
        NU, NV = 32, 26
        jag = [0.0] * (NU + 1)
        for i in range(1, NU, 2):
            jag[i] = rnd.uniform(0.05, 0.28)
        for i in range(2, NU, 4):
            jag[i] = rnd.uniform(0.0, 0.08)
        for i in rnd.sample(range(3, NU - 3, 2), 3):       # a few long rips
            jag[i] = -rnd.uniform(0.25, 0.45)

        def y_at(x, z):
            ys = [surf(['Torso'], (x, 0), math.pi / 2 * side, min(z, 4.2))] if z > 3.6 else []
            for leg in ('LeftLeg', 'RightLeg'):
                ys.append(surf([leg], (x, 0), math.pi / 2 * side, z))
            return max(ys + [0.9])
        top = 3.95
        cache = {}

        def fn(u, v, side=side, w=w, zb=zb, jag=jag):
            x = (2 * u - 1) * w
            i = u * NU
            k = min(int(i), NU - 1)
            jj = jag[k] + (jag[k + 1] - jag[k]) * (i - k)
            bot = zb + 0.12 * abs(2 * u - 1) - jj
            z = bot + (top - bot) * v
            key = (round(x, 2), round(z, 2))
            if key not in cache:
                cache[key] = y_at(x, z)
            fall = 0.05 + 0.07 * (top - z) / 2.4
            pleat = 0.035 * math.sin(x * 9.0 + side) * (1 - v) ** 0.7
            return (x, side * (cache[key] + fall + pleat), z)
        A.slab('Loin', 'Cloth', fn, NU, NV, 0.03, lambda p, side=side: (p[0], 0, p[2]), bevel=0.006,
               name='loin_front' if side < 0 else 'loin_back')


def hip_strips():
    """thick leather strips hanging from under the belt over each thigh's outside, rounded at their edges and
    curving with the thigh, each tipped with a bronze cap and stud"""
    for k, deg in enumerate((-75, -45, -15, 15, 45)):
        t = math.radians(deg)
        dirn = Vector((math.cos(t), math.sin(t), 0))
        side = Vector((0, 0, 1)).cross(dirn)
        z1, z0 = 3.95, 2.62 - 0.08 * (k % 2)
        lift = 0.07 + 0.02 * (k % 2)
        zs = [z0 + (z1 - z0) * q / 10 for q in range(11)]
        rr = [surf(['LeftLeg'], LEG_C, t, z) + lift for z in zs]
        for q in range(1, len(rr)):      # hang straight down past any dips, never into the thigh
            rr[q] = max(rr[q], rr[q - 1] - 0.02)
        sec = rrect(0.38, 0.05, 0.02, 3)

        def fn(u, j, dirn=dirn, side=side, zs=zs, rr=rr, z0=z0, z1=z1):
            v = u * (len(zs) - 1)
            q = min(int(v), len(zs) - 2)
            f = v - q
            z = zs[q] + (zs[q + 1] - zs[q]) * f
            r = rr[q] + (rr[q + 1] - rr[q]) * f
            x, y = sec[j % len(sec)]
            tip = clamp((z - z0) / 0.2)
            x *= 0.55 + 0.45 * math.sqrt(tip)               # the strip rounds off at its tip
            twist = 0.04 * math.sin(u * 5 + k) * x / 0.19       # worn leather doesn't hang flat
            ragged = 0.035 * math.sin(x * 60 + k) * (1 - tip)    # a chewed, ragged tip
            base = Vector((LEG_C[0], LEG_C[1], 0)) + dirn * (r + y + twist)
            return tuple(base + side * x + Vector((0, 0, z - 0.06 * (1 - tip) + ragged)))
        surface('LeftLeg', 'Leather', fn, [i / 24 for i in range(25)], list(range(len(sec) + 1)), closed_v=True,
                out=lambda p: (LEG_C[0], LEG_C[1], p[2]), name='strip')
        tip_r = surf(['LeftLeg'], LEG_C, t, z0 + 0.15) + lift + 0.03
        domed_stud('LeftLeg', 'Bronze', tuple(Vector((LEG_C[0], LEG_C[1], z0 + 0.16)) + dirn * tip_r), tuple(dirn), 0.06)


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


# ------------------------------------------------------------------ the hair: a wild mane, rigged for Smart Bones

K = 1.835                       # this body is about 1.835x the R6 rig
HEAD = Vector((0.0, 0.0, 7.33 + 0.5 * K))   # the head's centre (the R6 head, scaled to this body)
HEAD_R = 0.6 * K + 0.02
CHAINS = (-35, 15, 55, 90, 125, 165, 215)   # the hair's bone chains: angles round the head (90 = straight back)


def head_dir(theta_deg, el_deg):
    t, e = math.radians(theta_deg), math.radians(el_deg)
    return Vector((math.cos(t) * math.cos(e), math.sin(t) * math.cos(e), math.sin(e)))


def clump_path(theta, el, length, flare, seed_off=Vector()):
    """a clump of hair from its root on the scalp: out and up a little for volume, then swept back and down, its tip
    kicking outward"""
    root = HEAD + head_dir(theta, el) * HEAD_R * Vector((1, 1, 0.95))
    out = Vector((math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0))
    backish = (Vector((0, 1, 0)) * 0.75 + out * 0.6).normalized()
    up = Vector((0, 0, 1))
    p1 = root + head_dir(theta, el) * 0.32 + backish * 0.25 + up * 0.18 * (el / 60)
    p2 = p1 + backish * 0.45 * length + out * 0.15 - up * 0.75 * length
    p3 = p2 + backish * 0.25 * length + out * (0.25 + flare) - up * 0.75 * length + seed_off
    # stay clear of the back and shoulders on the way down
    for p in (p2, p3):
        if p.z < 7.6:
            p.y = max(p.y, 1.45 + 0.15 * (7.6 - p.z)) if theta > 30 and theta < 150 else p.y
            rad = math.hypot(p.x, p.y)
            if p.z < 7.5 and rad < 1.4:
                s_ = 1.4 / max(rad, 1e-3)
                p.x, p.y = p.x * s_, p.y * s_
    return [root, p1, p2, p3]


def catmull(pts, t):
    n = len(pts) - 1
    x = clamp(t) * n
    i = min(int(x), n - 1)
    f = x - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)


def hair_clump(pts, width, rows=12, name='clump', tag=None):
    """a clump: a lens-shaped section, widest a third of the way along, swept along the path to a point. Its
    vertices remember how far along they are (for the rig)"""
    sec = [(math.cos(TAU * k / 6), 0.35 * math.sin(TAU * k / 6)) for k in range(6)]

    def frame(t):
        p = catmull(pts, t)
        tg = (catmull(pts, min(1, t + 1e-3)) - catmull(pts, max(0, t - 1e-3))).normalized()
        radial = Vector((p.x - HEAD.x, p.y - HEAD.y, (p.z - HEAD.z) * 0.3)).normalized()
        w = tg.cross(radial).normalized()
        n = w.cross(tg).normalized()
        return p, w, n

    def fn(u, j):
        t = u
        p, w, n = frame(t)
        wd = width * (0.55 + 0.45 * math.sin(math.pi * min(t / 0.35, 1.0) / 2)) * (1 - t) ** 0.85
        x, y = sec[j % 6]
        return tuple(p + w * x * wd + n * y * wd)
    ob = surface('Hair', 'Hair', fn, [i / rows for i in range(rows + 1)], list(range(7)), closed_v=True,
                 out=lambda q: tuple(HEAD), name=name)
    ob['hair_kind'], ob['hair_theta'] = tag[0], float(tag[1])
    return ob


def scalp():
    """the cap of hair on the head: down to a hairline across the brow, over the ears, low at the nape"""
    def hairline(t):     # elevation (deg) of the hairline at angle t (front = -90)
        f = math.cos(math.radians(t + 90))       # 1 at the front, -1 at the back
        return 18 + 22 * max(f, 0) ** 2 - 40 * max(-f, 0)
    nu, nv = 48, 10

    def fn(u, v):
        t = -90 + 360 * u
        el = hairline(t) + (90 - hairline(t)) * v
        return tuple(HEAD + head_dir(t, el) * (HEAD_R + 0.05) * Vector((1, 1, 0.95)))
    ob = surface('Hair', 'Hair', fn, [i / nu for i in range(nu + 1)], [j / nv for j in range(nv + 1)], closed_u=True,
                 out=lambda q: tuple(HEAD), name='scalp')
    ob['hair_kind'], ob['hair_theta'] = 'scalp', 0.0
    return ob


def hair():
    import random
    rnd = random.Random(17)
    rows = [(68, list(range(-150, 211, 22)), 1.0), (42, list(range(-40, 221, 18)), 1.15), (16, list(range(-10, 191, 16)), 1.2)]
    scalp()
    for el, thetas, ln in rows:
        for th in thetas:
            th_ = th + rnd.uniform(-6, 6)
            if el < 50 and -135 < th_ < -45:
                continue                       # leave the face clear
            length = ln * rnd.uniform(0.75, 1.25) * (0.55 if -150 < th_ < -30 else 1.0)
            pts = clump_path(th_, el + rnd.uniform(-5, 5), length, rnd.uniform(0.0, 0.35),
                             Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.1, 0.2), rnd.uniform(-0.15, 0.15))))
            hair_clump(pts, rnd.uniform(0.28, 0.4), tag=('clump', th_))
    # strands framing the face, either side
    for th in (-128, -52):
        pts = clump_path(th, 30, 0.7, 0.1)
        hair_clump(pts, 0.22, tag=('clump', th))


def hair_rig(ob):
    """bones for the mane: a root in the head and a chain of four down each of seven paths round the back and
    sides. Every vertex blends between the two nearest chains (by the angle its clump grows from) and the two
    nearest bones down them (by how far along its clump it is)"""
    ad = bpy.data.armatures.new('HairRig')
    arm = bpy.data.objects.new('HairRig', ad)
    bpy.context.scene.collection.objects.link(arm)
    knots = (0.0, 0.25, 0.5, 0.75, 1.0)
    paths = {c: clump_path(c, 40, 1.15, 0.15) for c in CHAINS}
    with bpy.context.temp_override(active_object=arm, object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        root = ad.edit_bones.new('HairRoot')
        root.head, root.tail = HEAD, HEAD + Vector((0, 0, 0.6))
        for c, pts in paths.items():
            parent = root
            for k in range(4):
                b = ad.edit_bones.new(f'Hair_{CHAINS.index(c)}_{k}')
                b.head, b.tail = catmull(pts, knots[k]), catmull(pts, knots[k + 1])
                b.parent = parent
                b.use_connect = k > 0
                parent = b
        bpy.ops.object.mode_set(mode='OBJECT')
    names = ['HairRoot'] + [f'Hair_{i}_{k}' for i in range(len(CHAINS)) for k in range(4)]
    g = {n: ob.vertex_groups.new(name=n) for n in names}
    tl = ob.data.attributes['hair_t'].data
    al = ob.data.attributes['hair_theta'].data
    for v in ob.data.vertices:
        t, th = tl[v.index].value, al[v.index].value
        if t < 0:
            g['HairRoot'].add([v.index], 1.0, 'REPLACE')
            continue
        # the two nearest chains by angle
        cs = sorted(range(len(CHAINS)), key=lambda i: abs(CHAINS[i] - th))[:2]
        d0, d1 = abs(CHAINS[cs[0]] - th), abs(CHAINS[cs[1]] - th)
        wc = {cs[0]: d1 / max(d0 + d1, 1e-6), cs[1]: d0 / max(d0 + d1, 1e-6)}
        # down the chain: the root holds the first bit, then the bones in turn
        pos = t * 4 - 0.5
        w = {}
        if pos < 0:
            w['HairRoot'] = -pos * 2 if pos > -0.5 else 1.0
            pos = 0
        k = min(int(pos), 3)
        f = pos - k
        for c, wcc in wc.items():
            for kk, wk in ((k, 1 - f), (min(k + 1, 3), f)):
                n_ = f'Hair_{c}_{kk}'
                w[n_] = w.get(n_, 0) + wcc * wk
        best = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(x for _, x in best) or 1
        for n_, x in best:
            g[n_].add([v.index], x / tot, 'REPLACE')
    ob.parent = arm
    md = ob.modifiers.new('rig', 'ARMATURE')
    md.object = arm
    return arm


def join_hair():
    """the hair pieces into one mesh, each vertex tagged with how far along its clump it is and which angle the
    clump grows from"""
    obs = [o for p, o in A.PIECES if p == 'Hair']
    bm = bmesh.new()
    tl = bm.verts.layers.float.new('hair_t')
    al = bm.verts.layers.float.new('hair_theta')
    for o in obs:
        kind, th = o['hair_kind'], o['hair_theta']
        first = len(bm.verts)
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        new = bm.verts[first:]
        if kind == 'scalp':
            for v in new:
                v[tl], v[al] = -1.0, 90.0
        else:
            ends = sorted(new, key=lambda v: (v.co - HEAD).length)
            root = ends[0].co
            far = max((v.co - root).length for v in new) or 1
            for v in new:
                v[tl], v[al] = (v.co - root).length / far, float(th)
        bpy.data.objects.remove(o)
    me = bpy.data.meshes.new('Brute_Hair')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS['Hair'])
    ob = bpy.data.objects.new('Brute_Hair', me)
    bpy.context.scene.collection.objects.link(ob)
    A.PIECES[:] = [(p, o) for p, o in A.PIECES if p != 'Hair']
    return ob


def ref_head():
    """the R6 head scaled to this body, for the snapshots (the player's own head is used in game)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=A.RIG)
    new = [o for o in bpy.data.objects if o not in before]
    head = max(new, key=lambda o: (o.matrix_world @ Vector(o.bound_box[1])).z)
    for o in new:
        if o is not head:
            bpy.data.objects.remove(o)
    head.data.transform(head.matrix_world)
    head.matrix_world = Matrix.Identity(4)
    c = sum((v.co for v in head.data.vertices), Vector()) / len(head.data.vertices)
    head.data.transform(Matrix.Translation(HEAD) @ Matrix.Scale(K, 4) @ Matrix.Translation(-c))
    head.data.materials.clear()
    head.data.materials.append(MATS['Skin_normal_torso'])
    return head


def gear():
    A.PIECES.clear()
    cuff('LeftArm', ['LeftArm'], ARM_C, 4.12, 4.78)
    elbow_spike('LeftArm', ['LeftArm'], ARM_C, ELBOW_Z)
    cuff('LeftLeg', ['LeftLeg'], LEG_C, 0.55, 1.15)
    hip_strips()
    A.mirror_left_to_right()
    belt()
    loincloth()


def glow_material():
    """the eyes: a flat glowing red (Neon in Studio)"""
    m = bpy.data.materials.new('Glow')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.05, 0.02, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.04, 0.01, 1)
    b.inputs['Emission Strength'].default_value = 6.0
    return m


def gear_materials():
    """worn, battle-used materials: pitted and rusting iron, bronze dark with patina and green in its grooves,
    scuffed and cracked leather, stained cloth. Each exposes OUT_COL / OUT_ROUGH / OUT_METAL for baking"""
    for name, kind in (('Iron', 'iron'), ('Bronze', 'bronze'), ('Leather', 'leather'), ('Cloth', 'cloth'),
                       ('Hair', 'hair')):
        worn_material(name, kind)
    MATS['Steel'] = MATS['Bronze']


def worn_material(name, kind):
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

    def noise(scale, detail=4.0, rough=0.55, vec=None):
        n = N.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        L.new(vec or tc.outputs['Object'], n.inputs['Vector'])
        return n.outputs['Fac']

    def vor(scale, feat='F1', out_='Distance'):
        n = N.new('ShaderNodeTexVoronoi')
        n.feature = feat
        n.inputs['Scale'].default_value = scale
        L.new(tc.outputs['Object'], n.inputs['Vector'])
        return n.outputs[out_]

    def rng(x, a, b, c=0.0, d=1.0):
        n = N.new('ShaderNodeMapRange')
        n.clamp = True
        L.new(x, n.inputs['Value'])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = c, d
        return n.outputs[0]

    def op(o, a, b=None):
        n = N.new('ShaderNodeMath')
        n.operation = o
        n.use_clamp = o in ('MULTIPLY', 'ADD', 'SUBTRACT')
        for k, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[k].default_value = x
            else:
                L.new(x, n.inputs[k])
        return n.outputs[0]

    def mix(f, a, b):
        n = N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
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
    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.02
    bev.samples = 8
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.995, 0.93)                   # the worn high edges
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.08
    ao.samples = 16
    crev = rng(ao.outputs['AO'], 0.95, 0.4)                         # the grooves and crevices
    blot = rng(noise(2.5, 6, 0.65), 0.45, 0.7)                      # patches of wear and grime
    if kind == 'iron':
        rust = op('MAXIMUM', op('MULTIPLY', crev, 0.9), op('MULTIPLY', rng(noise(4.0, 8, 0.7), 0.55, 0.72), 0.8))
        pits = rng(vor(90), 0.0, 0.25, 1.0, 0.0)
        col = mix(rng(noise(12, 4), 0.3, 0.7, 0, 0.3), lin('#262628'), lin('#3a393c'))
        col = mix(rust, col, mix(rng(noise(30, 3), 0.4, 0.6), lin('#4a2412'), lin('#7a3c18')))
        col = mix(op('MULTIPLY', edge, 0.85), col, lin('#9a9894'))
        col = mix(op('MULTIPLY', pits, 0.5), col, lin('#141212'))
        rough = op('ADD', 0.38, op('ADD', op('MULTIPLY', rust, 0.5), op('MULTIPLY', edge, -0.15)))
        metal = op('SUBTRACT', 1.0, op('MULTIPLY', rust, 0.8))
        height = op('ADD', op('MULTIPLY', pits, -0.6), op('MULTIPLY', noise(25, 6), 0.3))
    elif kind == 'bronze':
        patina = op('MAXIMUM', op('MULTIPLY', crev, 0.95), op('MULTIPLY', blot, 0.55))
        verd = op('MULTIPLY', rng(ao.outputs['AO'], 0.7, 0.35), rng(noise(6, 5), 0.5, 0.65))
        col = mix(rng(noise(10, 4), 0.3, 0.7, 0, 0.4), lin('#7a5226'), lin('#93652f'))
        col = mix(patina, col, lin('#2e2012'))
        col = mix(verd, col, lin('#3d6656'))
        col = mix(op('MULTIPLY', edge, 0.9), col, lin('#d19a52'))
        rough = op('ADD', 0.3, op('ADD', op('MULTIPLY', patina, 0.45), op('MULTIPLY', edge, -0.12)))
        metal = op('SUBTRACT', 1.0, op('MULTIPLY', op('MAXIMUM', patina, verd), 0.7))
        height = op('ADD', op('MULTIPLY', noise(30, 6), 0.4), op('MULTIPLY', rng(vor(60), 0.0, 0.2, 1.0, 0.0), -0.3))
    elif kind == 'leather':
        cracks = rng(vor(28, 'DISTANCE_TO_EDGE'), 0.0, 0.03, 1.0, 0.0)
        grain = noise(80, 6, 0.7)
        col = mix(rng(noise(5, 5), 0.3, 0.7, 0, 0.5), lin('#24160e'), lin('#3a2416'))
        col = mix(op('MULTIPLY', blot, 0.6), col, lin('#4f3a2a'))                 # scuffed and faded
        col = mix(op('MULTIPLY', edge, 0.8), col, lin('#6b5240'))
        col = mix(op('MULTIPLY', op('MAXIMUM', crev, cracks), 0.7), col, lin('#0e0806'))
        rough = op('ADD', 0.6, op('ADD', op('MULTIPLY', blot, 0.15), op('MULTIPLY', edge, -0.1)))
        metal = 0.0
        height = op('ADD', op('MULTIPLY', grain, 0.4), op('MULTIPLY', cracks, -0.8))
    elif kind == 'cloth':
        low = N.new('ShaderNodeSeparateXYZ')
        L.new(geo.outputs['Position'], low.inputs[0])
        grime = op('MAXIMUM', rng(low.outputs['Z'], 2.6, 1.5), op('MULTIPLY', crev, 0.6))
        weave = N.new('ShaderNodeTexWave')
        weave.inputs['Scale'].default_value = 120
        L.new(tc.outputs['Object'], weave.inputs['Vector'])
        col = mix(rng(noise(3, 5), 0.3, 0.7, 0, 0.5), lin('#3f1514'), lin('#5a1f1c'))
        col = mix(op('MULTIPLY', blot, 0.45), col, lin('#6e3a33'))                 # faded patches
        col = mix(op('MULTIPLY', grime, 0.85), col, lin('#241a14'))                # dirt up from the hem
        col = mix(op('MULTIPLY', weave.outputs['Fac'], 0.12), col, lin('#1a0c0b'))
        rough = op('ADD', 0.82, op('MULTIPLY', grime, 0.1))
        metal = 0.0
        height = op('ADD', op('MULTIPLY', weave.outputs['Fac'], 0.5), op('MULTIPLY', noise(8, 6), 0.4))
    else:   # hair: near-black, with a sheen running along the strands
        sep = N.new('ShaderNodeUVMap')
        sep.uv_map = 'Detail'
        sx = N.new('ShaderNodeSeparateXYZ')
        L.new(sep.outputs['UV'], sx.inputs[0])
        strands = N.new('ShaderNodeTexWave')
        strands.inputs['Scale'].default_value = 1.0
        mp = N.new('ShaderNodeCombineXYZ')
        L.new(op('MULTIPLY', sx.outputs['Y'], 60.0), mp.inputs[0])
        L.new(mp.outputs[0], strands.inputs['Vector'])
        col = mix(op('MULTIPLY', strands.outputs['Fac'], 0.35), lin('#120d0b'), lin('#2b211c'))
        col = mix(op('MULTIPLY', crev, 0.7), col, lin('#060403'))
        rough = op('ADD', 0.42, op('MULTIPLY', strands.outputs['Fac'], 0.15))
        metal = 0.0
        height = strands.outputs['Fac']
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.004
    L.new(height, bump.inputs['Height'])
    tags = {}
    for tag, sock in (('COL', col), ('ROUGH', rough), ('NRM', bump.outputs['Normal'])):
        r = N.new('NodeReroute')
        r.name = 'OUT_' + tag
        L.new(sock, r.inputs[0])
        tags[tag] = r
    mv = N.new('ShaderNodeValue') if isinstance(metal, float) else None
    if mv:
        mv.outputs[0].default_value = metal
        metal = mv.outputs[0]
    r = N.new('NodeReroute')
    r.name = 'OUT_METAL'
    L.new(metal, r.inputs[0])
    tags['METAL'] = r
    L.new(tags['COL'].outputs[0], bsdf.inputs['Base Color'])
    L.new(tags['ROUGH'].outputs[0], bsdf.inputs['Roughness'])
    L.new(tags['METAL'].outputs[0], bsdf.inputs['Metallic'])
    L.new(tags['NRM'].outputs[0], bsdf.inputs['Normal'])
    MATS[name] = m
    return m


# ------------------------------------------------------------------ step snapshots

def snapshot(name, objs, wire=True, target=(0, 0, 4.2), dist=27):
    """a viewport-style shot of the build so far from the front three-quarter and the back: the model with its
    materials, and (wire=True) its wireframe drawn over it"""
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = 20
    for o in sc.objects:     # the studio is set up for an R6-sized figure: move its lights out to suit this one
        if o.type == 'LIGHT':
            o.location = Vector(o.location) * 2.2
            o.data.energy *= 4.0
            o.data.size *= 2.0
            o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
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
            md.thickness = 0.008
            md.use_replace = True
            w.data.materials.clear()
            w.data.materials.append(black)
            extra.append(w)
    os.makedirs(STEPS, exist_ok=True)
    shots = []
    for i, az in enumerate((-25, 155)):
        a = math.radians(az - 90)
        cam_d.lens = 60
        cam.location = (dist * math.cos(a), dist * math.sin(a), target[2] + 2.0)
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = 700, 860
        f = os.path.join(STEPS, f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
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
    for w in extra:
        bpy.data.objects.remove(w)
    print('STEP', out.filepath_raw, flush=True)


HEAD_DIR = None


def head_snap(name, label):
    """one layer of the sculpt: the head from the front and three-quarter, side by side, its name along the top"""
    global HEAD_DIR
    sc = bpy.context.scene
    if not sc.camera:
        sc, cam, cam_d = A.studio()
        for o in sc.objects:
            if o.type == 'LIGHT':
                o.location = Vector(o.location) * 1.6 + Vector((0, 0, 4))
                o.data.energy *= 2.5
                o.rotation_euler = (HEAD - o.location).to_track_quat('-Z', 'Y').to_euler()
    cam = sc.camera
    sc.cycles.samples = 16
    sc.render.resolution_x = sc.render.resolution_y = 560
    cam.data.lens = 85
    HEAD_DIR = os.path.join(STEPS, 'head')
    os.makedirs(HEAD_DIR, exist_ok=True)
    shots = []
    for i, az in enumerate((0, -35)):
        a = math.radians(az - 90)
        cam.location = HEAD + Vector((math.cos(a), math.sin(a), 0.06)) * 9.0
        cam.rotation_euler = (HEAD - cam.location).to_track_quat('-Z', 'Y').to_euler()
        f = os.path.join(HEAD_DIR, f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f).convert('RGB') for f in shots]
    W, H = ims[0].size
    out = Image.new('RGB', (W * 2, H + 44), (34, 34, 38))
    for k, im in enumerate(ims):
        out.paste(im, (k * W, 44))
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    ImageDraw.Draw(out).text((14, 11), label, fill=(235, 235, 235), font=font)
    path = os.path.join(HEAD_DIR, name + '.png')
    out.save(path)
    for f in shots:
        os.remove(f)
    return path


def contact(frames, name):
    """every layer of the sculpt on one sheet, and as a short video"""
    import subprocess
    from PIL import Image
    ims = [Image.open(f) for f in frames]
    W, H = ims[0].size
    cols = 3
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (W * cols // 2, H * rows // 2), (34, 34, 38))
    for k, im in enumerate(ims):
        sheet.paste(im.resize((W // 2, H // 2)), ((k % cols) * W // 2, (k // cols) * H // 2))
    sheet.save(os.path.join(STEPS, name + '.png'))
    seq = os.path.join(HEAD_DIR, 'seq')
    os.makedirs(seq, exist_ok=True)
    n = 0
    for f in frames:
        for _ in range(18):            # hold each layer for 0.75 s
            Image.open(f).save(os.path.join(seq, f'{n:04d}.png'))
            n += 1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(seq, '%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', os.path.join(STEPS, name + '.mp4')], check=True)
    import shutil
    shutil.rmtree(seq)
    print('STEP', os.path.join(STEPS, name + '.png'), flush=True)


def main():
    A.reset()
    body = import_body()
    for part, (o, nmap) in body.items():
        o.data.materials.clear()
        o.data.materials.append(skin_material(nmap))
        print(part, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), [round(x, 2) for x in o.dimensions])
    if STAGE == 'body':
        snapshot('step_01_body', [o for o, _ in body.values()], wire=False)
        return
    if STAGE == 'head':
        import head as HD
        G = HD.grid(320, 240)
        hi = HD.build(G, K, tuple(HEAD), 'Brute_Head_High', upto=1)
        clay = bpy.data.materials.new('Clay')
        clay.use_nodes = True
        cb = clay.node_tree.nodes['Principled BSDF']
        cb.inputs['Base Color'].default_value = (0.42, 0.4, 0.39, 1)
        cb.inputs['Roughness'].default_value = 0.6
        hi.data.materials.append(clay)
        eyes = HD.eyes(K, tuple(HEAD))
        eyes.data.materials.append(glow_material())
        eye_step = 1 + next(i for i, (name, _) in enumerate(HD.FORMS) if name.startswith('the eyes'))
        for o, _ in body.values():
            o.hide_render = True
        frames = []
        for k in range(1, HD.STEPS + 1):
            HD.update(hi, G, K, tuple(HEAD), upto=k)
            eyes.hide_render = k < eye_step
            frames.append(head_snap(f'head_{k:02d}', HD.step_name(k)))
            print('STEP', k, HD.step_name(k), flush=True)
        contact(frames, 'step_04_head')
        print('tris', sum(len(p.vertices) - 2 for p in hi.data.polygons), flush=True)
        return
    body_bvh(body)
    gear_materials()
    gear()
    if STAGE == 'gear':
        snapshot('step_02_gear', [], wire=False)
        return
    hair()
    hob = join_hair()
    rig = hair_rig(hob)
    head = ref_head()
    print('hair tris', sum(len(p.vertices) - 2 for p in hob.data.polygons), 'bones', len(rig.data.bones))
    if STAGE == 'hair':
        snapshot('step_03_hair', [hob], wire=False, target=(0, 0.3, 5.0), dist=31)
        return


if __name__ == '__main__':
    main()
