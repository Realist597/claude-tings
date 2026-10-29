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


def ring(part, mat, c, zc, radii, profile, name='ring', nu=None):
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
    ring(part, 'Iron', c, (z0 + z1) / 2, r, band, name='cuff')
    for zz in (z0 + 0.065, z1 - 0.065):
        ring(part, 'Bronze', c, zz, r, [(x + 0.07, y) for x, y in rrect(0.13, 0.13, 0.05)], name='cuff_rim')
    for k in range(12):
        stud(part, 'Bronze', c, r, (z0 + z1) / 2, k * 30 + 15, r=0.055, lift=0.07)


def belt():
    nu = 64
    c = (0.0, 0.0)
    for z0, z1, name in ((3.6, 3.96, 'belt'), (3.93, 4.29, 'belt_upper')):
        r = girth(['Torso'], c, z0, z1, nu, 0.03)
        ring('Torso', 'Leather', c, (z0 + z1) / 2, r, [(x + 0.045, y) for x, y in rrect(0.09, z1 - z0, 0.03)], name=name)
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
            jag[i] = rnd.uniform(0.05, 0.2)
        for i in range(2, NU, 4):
            jag[i] = rnd.uniform(0.0, 0.06)

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
            base = Vector((LEG_C[0], LEG_C[1], 0)) + dirn * (r + y)
            return tuple(base + side * x + Vector((0, 0, z - 0.06 * (1 - tip))))
        surface('LeftLeg', 'Leather', fn, [i / 24 for i in range(25)], list(range(len(sec) + 1)), closed_v=True,
                out=lambda p: (LEG_C[0], LEG_C[1], p[2]), name='strip')
        tip_r = surf(['LeftLeg'], LEG_C, t, z0 + 0.15) + lift + 0.03
        domed_stud('LeftLeg', 'Bronze', tuple(Vector((LEG_C[0], LEG_C[1], z0 + 0.16)) + dirn * tip_r), tuple(dirn), 0.06)


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def gear():
    A.PIECES.clear()
    cuff('LeftArm', ['LeftArm'], ARM_C, 4.12, 4.78)
    cuff('LeftLeg', ['LeftLeg'], LEG_C, 0.55, 1.15)
    hip_strips()
    A.mirror_left_to_right()
    belt()
    loincloth()


def gear_materials():
    """the gear's live materials (baked down later)"""
    def pbr(name, base, rough, metal):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = lin(base)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        MATS[name] = m
    pbr('Iron', '#2d2c2e', 0.45, 1.0)
    pbr('Bronze', '#8a5f2c', 0.32, 1.0)
    pbr('Leather', '#2b1c14', 0.6, 0.0)
    pbr('Cloth', '#4a1a19', 0.85, 0.0)
    MATS['Steel'] = MATS['Bronze']


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
    body_bvh(body)
    gear_materials()
    gear()
    if STAGE == 'gear':
        snapshot('step_02_gear', [], wire=False)
        return


if __name__ == '__main__':
    main()
