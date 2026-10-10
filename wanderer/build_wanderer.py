"""The Wanderer: a cowboy-hatted ranger outfit for a Roblox R6 character, in black cloth and leather
with deep purple and silver accents.

Built procedurally like the Dark Knight armour (it borrows that script's plate, bake and rig tools),
fitted to the same R6 body (1 unit = 1 stud, Z up, the character faces -Y). One mesh per body part,
so each welds to a single part in Roblox:
    Wanderer_Hat (welds to the head)   Wanderer_Torso   Wanderer_LeftArm   Wanderer_RightArm
    Wanderer_LeftLeg   Wanderer_RightLeg
    Wanderer_Cape, Wanderer_Scarf (cloth with bones, both welded to the torso)

Every surface is a clean quad grid (cloth, leather, felt) or a small hard-surface piece (buckles,
spikes, studs), with hard edges kept by auto smooth. Procedural Cycles materials are baked down to
PBR maps per mesh for Roblox SurfaceAppearance:
    <Mesh>_Color.png  <Mesh>_Normal.png (OpenGL / +Y)  <Mesh>_Roughness.png  <Mesh>_Metalness.png

    python build_wanderer.py -- [--stage preview|stats|all] [--res 1024] [--out DIR]
    (or: blender -b --factory-startup --python build_wanderer.py -- ...)

    preview  build the detailed meshes and render preview.png with the live materials (fast)
    stats    print triangle counts per piece and per mesh
    all      build, UV, bake, render preview.png with the baked maps, export WandererOutfit.fbx
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as A                                    # noqa: E402
from build_armor import slab, wrap, bwrap, sheet, rivet, se, val, lin, rr_point, T, TAU   # noqa: E402

STAGE = A.STAGE
RES = A.RES
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
PREFIX = 'Wanderer_'

BODY = A.PARTS          # the armour's own table of R6 parts, for naming the reference body
A.PARTS = PARTS = {
    'Hat': ((0, 0, 4.5), None),
    'Torso': ((0, 0, 3), None),
    'LeftArm': ((1.5, 0, 3), None),
    'RightArm': ((-1.5, 0, 3), None),
    'LeftLeg': ((0.5, 0, 1), None),
    'RightLeg': ((-0.5, 0, 1), None),
    'Cape': ((0, 0, 3), None),    # cloth with bones, welded to the torso
    'Scarf': ((0, 0, 3), None),   # likewise
}
MATS = A.MATS
HIGH = A.HIGH


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def smoothstep(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ shape helpers

def tatter(nu, seed, depth, slits=(), slit_h=0.0, wmin=2, wmax=4, jitter=0.25, closed=False):
    """a torn hem as a function of u in [0, 1]: how far below the clean hem it hangs. Its knots sit on
    the grid's columns (nu of them), so each tooth is a crisp point between two straight edges.
    slits: columns where the cloth is ripped upward by slit_h"""
    rnd = random.Random(seed)
    D = [0.0] * (nu + 1)
    D[0] = depth * rnd.uniform(0, jitter)
    i = 0
    while i < nu:
        j = min(nu, i + rnd.randint(wmin, wmax))
        if nu - j < wmin:
            j = nu
        tip = rnd.randint(i + 1, j - 1)
        d = depth * rnd.uniform(0.35, 1.0)
        for k in range(i + 1, j):
            D[k] = d * ((k - i) / (tip - i) if k <= tip else (j - k) / (j - tip))
        D[j] = depth * rnd.uniform(0, jitter)
        i = j
    for k in slits:
        D[k] = -slit_h
    if closed:
        D[nu] = D[0]

    def f(u):
        x = clamp(u) * nu
        k = min(int(x), nu - 1)
        return D[k] + (D[k + 1] - D[k]) * (x - k)
    return f


def shell(part, mat, c, hem, zs, hd, a, b, t0, t1, ex=2.6, th=0.04, nu=40, nv=12, vw=0.5, closed=False, extra=None,
          inside_z=None, bevel=0.008, name='shell', trim=None):
    """a cap over a body part: a wall round the vertical axis through c, from hem(theta deg) up to zs,
    then a dome of height hd closing over the top. a, b: half-widths in X and Y (numbers or functions of
    z, taken at the wall). theta 0 = +X, -90 = front."""
    T0 = math.radians(t0)
    T1 = T0 + TAU if closed else math.radians(t1)

    def fn(u, v):
        t = T0 + (T1 - T0) * u
        d = math.degrees(t)
        if v <= vw:
            lo = val(hem, d)
            z, k = lo + (zs - lo) * v / vw, 1.0
        else:
            ph = (v - vw) / (1 - vw) * math.pi / 2
            z, k = zs + hd * math.sin(ph), math.cos(ph)
        zz = min(z, zs)
        e = extra(d, z) if extra else 0.0
        x, y = se(t, ex)
        return (c[0] + x * (val(a, zz) + e) * k, c[1] + y * (val(b, zz) + e) * k, z)
    iz = zs - 0.5 if inside_z is None else inside_z
    return slab(part, mat, fn, nu, nv, th, lambda p: (c[0], c[1], iz), closed_u=closed, bevel=bevel, name=name, trim=trim)


def dens(n, k=2):
    """grid size: the detailed pass is k times denser, to carry the fine creases into the normal map"""
    return n * k if HIGH[0] else n


def fine():
    """1 on the detailed pass: fine creases exist only there and bake into the normal map"""
    return 1.0 if HIGH[0] else 0.0


def env(z, a, b, soft=0.08):
    """1 between heights a and b, easing out over soft at either end"""
    return smoothstep((z - a) / soft) * smoothstep((b - z) / soft)


def puff(t, p=1.4):
    """a fold that only bulges outward: rounded ridges, flat between them"""
    return max(0.0, math.sin(t)) ** p


def rows(z0, z1, n, focus=()):
    """n + 1 row heights from z0 to z1, packed closer where the folds bunch: focus = ((z, width, weight), ...)"""
    m = 400
    zs = [z0 + (z1 - z0) * i / m for i in range(m + 1)]
    w = [1 + sum(wt * math.exp(-((z - zc) / wd) ** 2) for zc, wd, wt in focus) for z in zs]
    cdf = [0.0]
    for i in range(1, m + 1):
        cdf.append(cdf[-1] + (w[i] + w[i - 1]) / 2)
    out, i = [], 0
    for j in range(n + 1):
        target = cdf[-1] * j / n
        while i < m - 1 and cdf[i + 1] < target:
            i += 1
        f = (target - cdf[i]) / max(cdf[i + 1] - cdf[i], 1e-12)
        out.append(zs[i] + (zs[i + 1] - zs[i]) * clamp(f))
    return out


def tube(part, mat, c, zr, a, b, t0, ex, th, nu, extra=None, bevel=0.004, name='tube'):
    """a closed sleeve of cloth round the vertical axis through c, its rows at the heights zr (from rows()),
    theta starting at t0 degrees. extra(theta_deg, z) pushes it out: the folds"""
    n = len(zr) - 1
    T0 = math.radians(t0)

    def fn(u, v):
        t = T0 + TAU * u
        x = v * n
        j = min(int(x), n - 1)
        z = zr[j] + (zr[j + 1] - zr[j]) * (x - j)
        e = extra(math.degrees(t), z) if extra else 0.0
        X, Y = se(t, ex)
        return (c[0] + X * (val(a, z) + e), c[1] + Y * (val(b, z) + e), z)
    return slab(part, mat, fn, nu, n, th, lambda p: (c[0], c[1], p[2]), closed_u=True, bevel=bevel, name=name)


def flat_uvs(bm):
    """each face its own island, laid flat in studs (for small hard-surface pieces)"""
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    dtl = bm.loops.layers.uv.get('Detail') or bm.loops.layers.uv.new('Detail')
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        ax = (f.loops[0].vert.co - f.loops[1].vert.co).normalized()
        ay = n.cross(ax)
        o = f.loops[0].vert.co
        for loop in f.loops:
            d = loop.vert.co - o
            loop[uvl].uv = loop[dtl].uv = (d.dot(ax), d.dot(ay))


def spike(part, mat, p, n, up, h=0.12, l=0.075, w=0.042, lean=0.05, name='spike'):
    """a four-sided blade-pyramid standing on a surface at p (normal n), its point leaning toward up"""
    n, up = Vector(n).normalized(), Vector(up)
    t = (up - n * up.dot(n)).normalized()
    s = n.cross(t)
    p = Vector(p)
    bm = bmesh.new()
    b = [bm.verts.new(p + t * l - n * 0.01), bm.verts.new(p + s * w - n * 0.01), bm.verts.new(p - t * l * 0.7 - n * 0.01),
         bm.verts.new(p - s * w - n * 0.01)]
    tip = bm.verts.new(p + n * h + t * lean)
    for k in range(4):
        bm.faces.new((b[k], b[(k + 1) % 4], tip))
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    flat_uvs(bm)
    return A.finish(part, mat, bm, 0, name)


def ring(part, mat, center, nrm, across, hw, hh, bar=0.022, th=0.022, r=0.025, nu=28, name='buckle'):
    """a rounded-rectangle frame (a buckle) lying in the plane through center facing nrm"""
    nrm, acr = Vector(nrm).normalized(), Vector(across).normalized()
    upv = nrm.cross(acr)
    if upv.z < 0:
        upv = -upv
    c = Vector(center)

    def per(hw_, hh_):
        r_ = min(r, hw_ - 1e-3, hh_ - 1e-3)
        a, b_, q = hw_ - r_, hh_ - r_, math.pi * r_ / 2
        return 2 * a + 2 * b_ + 2 * q, r_

    def fn(u, v):
        pts = []
        for hw_, hh_ in ((hw - bar, hh - bar), (hw, hh)):
            half, r_ = per(hw_, hh_)
            x, y = rr_point(-half + 2 * half * u, hw_, hh_, r_)
            pts.append(Vector((x, y)))
        q = pts[0].lerp(pts[1], v)
        return tuple(c + acr * q.x + upv * q.y)
    return slab(part, mat, fn, nu, 1, th, lambda p: tuple(Vector(p) - nrm * 5), closed_u=True, bevel=0.005, name=name)


def disc_frame(ax):
    ax = Vector(ax).normalized()
    s1 = ax.cross(Vector((0, 0, 1)))
    s1 = s1.normalized() if s1.length > 1e-6 else Vector((1, 0, 0))
    return ax, s1, ax.cross(s1)


def cup(part, mat, o, ax, r0, r1, depth, th, nu=24, nv=2, name='cup', bevel=0.005):
    """a short tube from o along ax, radius r0 at its back to r1 at its front"""
    ax, s1, s2 = disc_frame(ax)
    o = Vector(o)

    def fn(u, v):
        a = TAU * u
        return tuple(o + ax * depth * v + (s1 * math.cos(a) + s2 * math.sin(a)) * (r0 + (r1 - r0) * v))
    return slab(part, mat, fn, nu, nv, th, lambda p: tuple(o + ax * (Vector(p) - o).dot(ax)), closed_u=True, bevel=bevel,
                name=name)


def washer(part, mat, o, ax, ri, ro, th, nu=24, name='washer', bevel=0.004):
    """a flat ring facing ax"""
    ax, s1, s2 = disc_frame(ax)
    o = Vector(o)

    def fn(u, v):
        a = TAU * u
        return tuple(o + (s1 * math.cos(a) + s2 * math.sin(a)) * (ri + (ro - ri) * v))
    return slab(part, mat, fn, nu, 1, th, lambda p: tuple(Vector(p) - ax * 5), closed_u=True, bevel=bevel, name=name)


def lens(part, mat, o, ax, R_, h, th=0.01, nu=24, nv=4, name='lens'):
    """a shallow dome facing ax"""
    ax, s1, s2 = disc_frame(ax)
    o = Vector(o)

    def fn(u, v):
        a, ph = TAU * u, v * math.pi / 2
        return tuple(o + ax * h * math.sin(ph) + (s1 * math.cos(a) + s2 * math.sin(a)) * R_ * math.cos(ph))
    return slab(part, mat, fn, nu, nv, th, lambda p: tuple(o - ax), closed_u=True, bevel=0, name=name)


def catmull(pts, t):
    """point t in [0, 1] along a Catmull-Rom spline through pts"""
    pts = [Vector(p) for p in pts]
    n = len(pts) - 1
    x = clamp(t) * n
    i = min(int(x), n - 1)
    f = x - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)


def ribbon(part, mat, path, width, nu, nv, th, twist=lambda s: 0.0, wave=lambda s: 0.0, fork=0.0, ridge=None,
           up=(0, 0, 1), name='ribbon', bevel=0.004):
    """a flat strip along path(s), s in [0, 1]: width(s) across, turned twist(s) radians about the path,
    pushed off its own plane by wave(s). fork: the end is cut into a swallowtail that deep (a fraction of
    the length). ridge(s, x): a raised spine (x in -1..1 across)"""
    up = Vector(up)

    def frame(s):
        s = clamp(s)
        p = path(s)
        t = (path(min(1.0, s + 1e-3)) - path(max(0.0, s - 1e-3))).normalized()
        wd = (up - t * up.dot(t)).normalized()
        a = twist(s)
        wd = wd * math.cos(a) + t.cross(wd) * math.sin(a)
        return p, wd, t.cross(wd)

    def fn(u, v):
        x = 2 * v - 1
        s = u * (1 - fork * (1 - abs(x)))
        p, wd, nm = frame(s)
        lift = wave(s) + (ridge(s, x) if ridge else 0.0)
        return tuple(p + wd * x * width(s) / 2 + nm * lift)
    # the strip has no inside: grow it along its own normal (looked up from the nearest grid point)
    kd, nrms = KDTree((nu + 1) * (nv + 1)), []
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            du = Vector(fn(min(1, u + 1e-4), v)) - Vector(fn(max(0, u - 1e-4), v))
            p, wd, nm = frame(u * (1 - fork * (1 - abs(2 * v - 1))))
            n = du.cross(wd)
            n = n.normalized() if n.length > 1e-9 else nm
            if n.dot(nm) < 0:
                n = -n
            kd.insert(fn(u, v), len(nrms))
            nrms.append(n)
    kd.balance()
    return slab(part, mat, fn, nu, nv, th, lambda P: tuple(Vector(P) - nrms[kd.find(P)[1]]), bevel=bevel, name=name)


# ------------------------------------------------------------------ the outfit

def hat():
    """a black felt cowboy hat: a cattleman crown (a crease down the middle, pinched at the front) on an
    oval brim curled up at the sides, a purple band with a silver concho and studs, and a feather"""
    Z0, Zc = 4.8, 5.42                          # crown base, mean top of its wall
    A0, B0 = 0.645, 0.705                       # crown base half-widths

    def ca(z):
        return A0 - 0.085 * (z - Z0) / 0.6

    def cb(z):
        return B0 - 0.065 * (z - Z0) / 0.6

    def zwall(t):
        c, s = math.cos(t), math.sin(t)
        return Zc + 0.05 * c * c - 0.05 * s * s - 0.03 * max(0.0, -s)   # sides high, the front lowest

    def pinch(t, z):   # the two dents either side of the front
        d = math.degrees(t)
        g = sum(math.exp(-((d - m) / 20) ** 2) for m in (-125, -55))
        return -0.09 * g * smoothstep((z - Z0 - 0.15) / 0.45)
    vw = 0.6

    def crown(u, v):
        t = math.radians(90) + TAU * u    # the seam at the back
        x, y = se(t, 2.2)
        if v <= vw:
            z = Z0 + (zwall(t) - Z0) * v / vw
            k, e = 1.0, pinch(t, z)
            return (x * (ca(z) + e), y * (cb(z) + e), z)
        k = 1 - (v - vw) / (1 - vw)      # 1 at the rim of the top, 0 at the middle
        zw = zwall(t)
        zt = zw * k + (Zc - 0.03) * (1 - k)
        xh = k * abs(math.cos(t))         # across the crown: 0 on the crease, 1 at the sides
        z = zt + 0.11 * math.sqrt(max(0.0, 1 - k ** 2)) - 0.15 * (1 - xh) ** 1.6 * (1 - k ** 3)
        e = pinch(t, zw) * k
        return (x * (ca(zw) + e) * k, y * (cb(zw) + e) * k, z)
    slab('Hat', 'Felt', crown, 48, 20, 0.035, lambda p: (0, 0, Z0 + 0.07), closed_u=True, bevel=0.006, name='crown')

    def brim(u, v, lift=0.0):
        t = math.radians(90) + TAU * u
        c, s = math.cos(t), math.sin(t)
        x, y = se(t, 2.15)
        ra = A0 + 0.005 + (1.2 - A0) * v
        rb = B0 + 0.005 + (1.36 - B0) * v
        z = Z0 + 0.02 + 0.27 * abs(c) ** 2.4 * v ** 2.2 - 0.07 * s * s * v ** 1.6 - 0.05 * max(0.0, -s) * v
        return (x * ra, y * rb, z + lift)
    slab('Hat', 'Felt', brim, 64, 9, 0.032, lambda p: (p[0] * 0.9, p[1] * 0.9, p[2] - 1), closed_u=True, bevel=0.006,
         name='brim')
    # a satin binding round the brim's edge
    slab('Hat', 'Binding', lambda u, v: brim(u, 0.93 + 0.07 * v, 0.03), 64, 1, 0.008,
         lambda p: (p[0] * 0.9, p[1] * 0.9, p[2] - 1), closed_u=True, bevel=0.003, name='binding')
    # the band: purple silk round the crown's foot, with silver studs and a concho on the left
    zb0, zb1 = Z0 + 0.04, Z0 + 0.17

    def band(u, v):
        t = math.radians(90) + TAU * u
        z = zb0 + (zb1 - zb0) * v
        x, y = se(t, 2.2)
        return (x * (ca(z) + pinch(t, z) + 0.035), y * (cb(z) + pinch(t, z) + 0.035), z)
    slab('Hat', 'Silk', band, 48, 2, 0.022, lambda p: (0, 0, p[2]), closed_u=True, bevel=0.004, name='hatband')
    zm = (zb0 + zb1) / 2
    for deg in range(-150, 181, 30):
        if deg in (0, 30):
            continue
        t = math.radians(deg)
        x, y = se(t, 2.2)
        p = Vector((x * (ca(zm) + 0.06), y * (cb(zm) + 0.06), zm))
        rivet('Hat', 'Silver', tuple(p), (x, y, 0), 0.026, flat=0.6)
    # the concho: a domed silver disc with a purple heart and a ring of beads
    t = math.radians(12)
    x, y = se(t, 2.2)
    cn = Vector((x * (ca(zm) + 0.06), y * (cb(zm) + 0.06), zm))
    nn = Vector((x, y, 0)).normalized()
    rivet('Hat', 'Silver', tuple(cn), tuple(nn), 0.11, flat=0.3)
    rivet('Hat', 'Silk', tuple(cn + nn * 0.03), tuple(nn), 0.045, flat=0.5)
    if HIGH[0]:
        side = nn.cross(Vector((0, 0, 1)))
        for k in range(10):
            a = TAU * k / 10
            q = cn + nn * 0.02 + (side * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * 0.088
            rivet('Hat', 'Silver', tuple(q), tuple(nn), 0.012, flat=0.7)
    # a black feather tipped in purple, tucked into the band behind the concho
    base = Vector((x * (ca(zm) + 0.05), y * (cb(zm) + 0.05), zm)) + Vector((0, 0.16, -0.02))
    P = [base, base + Vector((0.08, 0.16, 0.24)), base + Vector((0.12, 0.38, 0.46)), base + Vector((0.1, 0.62, 0.6))]
    rnd = random.Random(7)
    nicks = {k: rnd.uniform(0.25, 0.6) for k in (9, 15, 22)}

    def fw(s):
        w = 0.16 * math.sin(math.pi * min(1.0, s ** 0.8 * 1.02)) ** 0.7 + 0.012
        k = int(s * 28 + 0.5)
        return w * (1 - nicks.get(k, 0.0) * 0.5) if k in nicks and abs(s * 28 - k) < 0.02 else w
    ribbon('Hat', 'Feather', lambda s: catmull(P, s), fw, 28, 4, 0.01,
           ridge=lambda s, xx: 0.012 * (1 - abs(xx)) * (1 - s), up=(1, -0.2, 0), name='feather')
    # goggles pushed up onto the crown: leather gaskets, black-purple cups, silver bezels, purple lenses,
    # a silver bridge, and a leather strap round the crown buckled at the back
    zg = Z0 + 0.31
    eyes = []
    for deg in (-113, -67):
        t = math.radians(deg)
        x, y = se(t, 2.2)
        e = pinch(t, zg)
        o = Vector((x * (ca(zg) + e + 0.035), y * (cb(zg) + e + 0.035), zg))
        n = Vector((x / ca(zg), y / cb(zg), 0)).normalized()
        ax = (n * math.cos(math.radians(22)) + Vector((0, 0, 1)) * math.sin(math.radians(22))).normalized()
        o = o - n * 0.01
        cup('Hat', 'Leather', o, ax, 0.174, 0.168, 0.045, 0.02, name='gasket')
        c0 = o + ax * 0.04
        cup('Hat', 'DarkMetal', c0, ax, 0.156, 0.144, 0.09, 0.02, nv=dens(2), name='goggle_cup')
        f = c0 + ax * 0.09
        washer('Hat', 'Silver', f, ax, 0.112, 0.172, 0.024, name='bezel')
        lens('Hat', 'Lens', f + ax * 0.004, ax, 0.118, 0.028, name='lens')
        _, s1, s2 = disc_frame(ax)
        if HIGH[0]:   # screws round each bezel
            for k in range(6):
                a = TAU * (k + 0.5) / 6
                rivet('Hat', 'Steel', tuple(f + ax * 0.022 + (s1 * math.cos(a) + s2 * math.sin(a)) * 0.143), tuple(ax), 0.01,
                      flat=0.6)
        eyes.append((c0, ax, s1))
    (cl, al, sl), (cr, ar, sr) = eyes
    pl = cl + al * 0.05 + (cr - cl).normalized() * 0.15
    pr = cr + ar * 0.05 - (cr - cl).normalized() * 0.15
    mid = (pl + pr) / 2 + (al + ar).normalized() * 0.03
    ribbon('Hat', 'Silver', lambda q: catmull([pl, mid, pr], q), lambda q: 0.045, 8, 1, 0.022, name='bridge')
    zs0, zs1 = zg - 0.05, zg + 0.05

    def strap(u, v):
        t = math.radians(90) + TAU * u
        z = zs0 + (zs1 - zs0) * v
        x, y = se(t, 2.2)
        return (x * (ca(z) + pinch(t, z) + 0.037), y * (cb(z) + pinch(t, z) + 0.037), z)
    slab('Hat', 'Strap', strap, 48, 1, 0.018, lambda p: (0, 0, p[2]), closed_u=True, bevel=0.004, name='goggle_strap')
    ring('Hat', 'Silver', (0, cb(zg) + 0.037 + 0.018 + 0.004, zg), (0, 1, 0), (1, 0, 0), 0.055, 0.06, bar=0.018, th=0.02,
         name='strap_buckle')
    # tilt the whole hat a touch forward, for attitude
    rot = Matrix.Translation((0, 0, Z0)) @ Matrix.Rotation(math.radians(6), 4, 'X') @ Matrix.Translation((0, 0, -Z0))
    for part, ob in A.PIECES:
        if part == 'Hat':
            ob.data.transform(rot)


def collar():
    """a tall stand-up collar, turned up over the mouth at the front, lined in purple and folded over at
    the top to show it"""
    c = (0, 0.03)
    a = lambda z: 0.665 + 0.15 * clamp((z - 3.98) / 0.62) ** 1.7
    b = lambda z: a(z) * 0.97
    top = lambda d: 4.6 + 0.17 * math.sin(math.radians(d)) - 0.09 * max(0.0, 1 - abs(d + 90) / 28)
    def folds(d, z):
        t = math.radians(d)
        k = 0.45 + 1.1 * clamp((z - 3.98) / 0.7)
        return k * (0.018 * math.sin(t * 7 + 1.4 * math.sin(t * 3)) + 0.007 * math.sin(t * 17 + 0.5)) \
            + fine() * 0.003 * math.sin(t * 31 + z * 40)
    wrap('Torso', 'Cloak', c, 3.98, top, a, b, 90, 450, ex=2.4, th=0.035, nu=dens(56), nv=dens(8), closed=True, extra=folds,
         bevel=0.006, name='collar')
    wrap('Torso', 'Silk', c, 3.98, lambda d: top(d) - 0.004, lambda z: a(z) - 0.014, lambda z: b(z) - 0.014, 90, 450, ex=2.4,
         th=0.012, nu=44, nv=6, closed=True, extra=folds, bevel=0, name='collar_lining')
    # the turned-over top: a band of lining folded down the outside
    wrap('Torso', 'Silk', c, lambda d: top(d) - 0.11 - 0.02 * math.sin(math.radians(d) * 5), lambda d: top(d) + 0.012,
         lambda z: a(z) + 0.037, lambda z: b(z) + 0.037, 90, 450, ex=2.4, th=0.02, nu=56, nv=2, closed=True,
         extra=lambda d, z: folds(d, z) + 0.02 * (top(d) - z), bevel=0.005, name='collar_fold')


def shirt_and_belts():
    # the black shirt
    def shirt_folds(d, z):
        t = math.radians(d)
        side = abs(math.cos(t))
        bunch = 0.02 * env(z, 2.22, 2.8, 0.1) * puff(z * 26 + 1.8 * math.sin(t * 3 + 0.7) + 0.6 * math.sin(t * 7))
        pull = 0.011 * env(z, 3.0, 3.85, 0.2) * side ** 2 * puff((z + 0.9 * side) * 17 + 1.0)
        return bunch + pull + fine() * 0.003 * math.sin(z * 90 + t * 13)
    tube('Torso', 'Shirt', (0, 0), rows(1.97, 4.0, dens(14), ((2.5, 0.3, 3.5),)), 1.006, 0.506, -90, 14, 0.02, dens(40),
         extra=shirt_folds, name='shirt')
    slab('Torso', 'Shirt', lambda u, v: (-1.0 + 2.0 * u, -0.5 + 1.0 * v, 1.97), 8, 4, 0.02, lambda p: (p[0], p[1], p[2] + 1),
         bevel=0, name='shirt_hem')
    slab('Torso', 'Shirt', lambda u, v: (-1.0 + 2.0 * u, -0.5 + 1.0 * v, 4.0), 8, 4, 0.02, lambda p: (p[0], p[1], p[2] - 1),
         bevel=0, name='shirt_top')
    # two belts: one round the waist, a second slung across it, dropping to the right hip for the pouch
    zA = lambda d: 2.12 + 0.05 * math.cos(math.radians(d))
    zB = lambda d: 1.995 + 0.13 * math.cos(math.radians(d))
    BA, BB = 0.13, 0.12
    over = lambda d: 0.042 * clamp(1 - abs((zB(d) + BB / 2) - (zA(d) + BA / 2)) / 0.17)   # B rides over A where they cross
    wrap('Torso', 'Leather', (0, 0), zA, lambda d: zA(d) + BA, 1.04, 0.56, -90, 270, ex=10, th=0.035, nu=52, nv=2, closed=True,
         bevel=0.006, name='belt')
    wrap('Torso', 'Leather', (0, 0), zB, lambda d: zB(d) + BB, 1.045, 0.565, -90, 270, ex=10, th=0.035, nu=52, nv=2,
         closed=True, extra=lambda d, z: over(d), bevel=0.006, name='belt2')
    front = (0, -1, 0)
    # buckles: frames with a prong, the belt's tongue running on past them
    for bx, zf, lift, w in ((0.3, zA(-90) + BA / 2, 0.0, BA), (-0.38, zB(-90) + BB / 2, over(-90), BB)):
        y = -(0.56 + lift + 0.035 + 0.004)
        ring('Torso', 'Silver', (bx, y, zf), front, (1, 0, 0), 0.105, w / 2 + 0.035, bar=0.026, th=0.024, name='buckle')
        slab('Torso', 'Silver', lambda u, v, bx=bx, zf=zf, y=y: (bx - 0.08 + 0.1 * u, y - 0.004, zf - 0.01 + 0.02 * v), 2, 1,
             0.016, lambda p: (p[0], p[1] + 1, p[2]), bevel=0.003, name='prong')
        # the tongue: past the buckle, pointed, with a silver tip
        x0, x1 = bx + 0.1, bx + 0.3
        slab('Torso', 'Leather', lambda u, v, x0=x0, x1=x1, zf=zf, y=y, w=w: (
            x0 + (x1 - x0) * u, y + 0.006, zf - (w / 2 - 0.012) * (1 - 2 * v) * (1 - max(0.0, u - 0.7) / 0.3 * 0.85)),
            6, 2, 0.022, lambda p: (p[0], p[1] + 1, p[2]), bevel=0.004, name='tongue')
    # keepers: short loops over the belt
    for bx in (0.62, -0.8):
        sheet('Torso', 'Leather', 'front', (0.56 + 0.035, 0), bx - 0.03, bx + 0.03, zA(-90) - 0.015, zA(-90) + BA + 0.015,
              lambda x, z: 0.008, th=0.018, nu=2, nv=2, bevel=0.003, name='keeper')
    if HIGH[0]:   # studs along the slung belt
        for d in (-150, -120, -40, -20):
            t = math.radians(d)
            x, y = se(t, 10)
            p = (x * (1.045 + over(d) + 0.04), y * (0.565 + over(d) + 0.04), zB(d) + BB / 2)
            rivet('Torso', 'Steel', p, (x, y, 0), 0.022, flat=0.6)


def capelet():
    """the short shoulder cape over the chest and back, ending in a torn V at the front"""
    X = 0.97
    NU, NV = dens(44), dens(34)
    tf = tatter(44, 11, 0.13, slits=(15, 30), slit_h=0.12)
    tb = tatter(44, 23, 0.12, slits=(8, 26), slit_h=0.1)
    ztop = lambda x: 4.07 - 0.15 * smoothstep((abs(x) - 0.62) / 0.35)

    def fold(x, z, ph, amp):
        k = clamp((3.95 - z) / 1.0)
        xs = x / (0.55 + 0.45 * k)             # the folds spread as they fall
        f = math.sin(xs * 5.5 + ph) + 0.4 * math.sin(xs * 11 + 2 * ph + 1)
        return amp * k ** 1.2 * f + fine() * 0.003 * math.sin(x * 60 + z * 25 + ph)
    yf = lambda x, z: 0.552 + 0.11 * clamp((4.0 - z) / 1.1) ** 1.5 + fold(x, z, 0.4, 0.042)
    yb = lambda x, z: 0.632 + 0.08 * clamp((3.95 - z) / 0.95) ** 1.5 + fold(x, z, 1.7, 0.03)
    hemf = lambda u, x: 2.92 + 0.52 * clamp(abs(x - 0.1) / 1.07) ** 1.15 - tf(u)
    hemb = lambda u, x: 3.08 + 0.38 * (abs(x) / X) ** 1.2 - tb(u)
    rc = 0.11

    def profile(u):
        """the cape's cross-section at u: up the front, over the shoulder, down the back"""
        x = -X + 2 * X * u
        zt = ztop(x)
        pts = []
        z0 = hemf(u, x)
        for i in range(25):
            z = z0 + (zt - rc - z0) * i / 24
            pts.append((-yf(x, z), z))
        yft, ybt = yf(x, zt - rc), yb(x, zt - rc)
        for i in range(1, 9):
            a = i / 8 * math.pi / 2
            pts.append((-yft + rc * (1 - math.cos(a)), zt - rc + rc * math.sin(a)))
        for i in range(1, 13):
            pts.append((-yft + rc + (ybt - rc - (-yft + rc)) * i / 12, zt))
        for i in range(1, 9):
            a = i / 8 * math.pi / 2
            pts.append((ybt - rc + rc * math.sin(a), zt - rc + rc * math.cos(a)))
        z1 = hemb(u, x)
        for i in range(1, 25):
            z = zt - rc + (z1 - (zt - rc)) * i / 24
            pts.append((yb(x, z), z))
        L = [0.0]
        for i in range(1, len(pts)):
            L.append(L[-1] + math.dist(pts[i], pts[i - 1]))
        return x, pts, L
    cache = {}

    def fn(u, v):
        key = round(u, 9)
        if key not in cache:
            cache[key] = profile(u)
        x, pts, L = cache[key]
        s = v * L[-1]
        i = max(1, min(len(L) - 1, next((k for k in range(1, len(L)) if L[k] >= s), len(L) - 1)))
        f = (s - L[i - 1]) / max(L[i] - L[i - 1], 1e-9)
        y = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f
        z = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f
        return (x, y, z)
    slab('Torso', 'Cloak', fn, NU, NV, 0.025, lambda p: (p[0], 0, 3.4), bevel=0.006, name='capelet')


def cape():
    """the long cape, from under the capelet to the ankles, torn at the hem (longest on the left), lined
    in deep purple"""
    TOP, NU, NV = 3.9, dens(44), dens(28)
    tc = tatter(44, 5, 0.3, slits=(12, 29, 37), slit_h=0.42, wmin=2, wmax=4)
    hem = lambda u: 0.27 + 0.29 * (1 - (2 * u - 1)) - tc(u)
    k_ = lambda z: clamp((TOP - z) / 3.4)

    def cape_y(x, z):
        k = k_(z)
        hug, free = 0.53, 0.5 + 0.6 * k ** 1.25
        y = (hug + free + math.sqrt((hug - free) ** 2 + 0.06 ** 2)) / 2
        xn = x / width(z)
        f = math.sin(xn * math.pi * 4.5 + 0.6) + 0.35 * math.sin(xn * math.pi * 9 + 1.3)
        gather = 0.012 * math.sin(xn * math.pi * 14) * (1 - k) ** 3 * smoothstep(k * 8)
        return y + 0.11 * k ** 0.9 * f + gather + fine() * 0.004 * math.sin(xn * 70 + z * 9)
    width = lambda z: 0.93 + 0.45 * k_(z)

    def layer(off):
        def fn(u, v):
            xn = 2 * u - 1
            zb = hem(u)
            z = zb + (TOP - zb) * v
            x = xn * width(z)
            return (x, cape_y(x, z) + off, z)
        return fn
    slab('Cape', 'Lining', layer(0.0), NU, NV, 0.012, lambda p: (p[0], p[1] - 1, p[2]), bevel=0.004, name='cape_lining')
    slab('Cape', 'Cloak', layer(0.014), NU, NV, 0.018, lambda p: (p[0], p[1] - 1, p[2]), bevel=0.005, name='cape')


SCARF = [(0.3, 0.5, 4.36), (0.66, 0.86, 4.3), (1.1, 1.18, 4.12), (1.6, 1.42, 4.02), (2.1, 1.66, 3.86), (2.55, 1.86, 3.74),
         (2.95, 2.0, 3.58)]


def scarf_path(s):
    return catmull(SCARF, s)


def scarf():
    """a long purple scarf tail streaming from the collar, ending in a swallowtail"""
    ribbon('Scarf', 'Silk', scarf_path, lambda s: 0.3 - 0.07 * s, dens(60), dens(4), 0.014,
           twist=lambda s: 0.5 * math.sin(s * 5.2 + 0.4),
           wave=lambda s: 0.07 * s * math.sin(s * 14) + 0.015 * math.sin(s * 41 + 1), fork=0.13,
           name='scarf')


def arm():
    """the left arm (+X); the right one is its mirror"""
    cx = 1.5
    # the shirt sleeve
    def sleeve_folds(d, z):
        t = math.radians(d)
        bunch = 0.024 * env(z, 2.92, 3.5, 0.12) * puff(z * 30 + 1.6 * math.sin(t * 2 + 0.5) + 0.8 * math.sin(t * 5))
        return bunch + 0.008 * math.sin(t * 4 + z * 3) + fine() * 0.003 * math.sin(z * 85 + t * 9)
    tube('LeftArm', 'Shirt', (cx, 0), rows(2.2, 3.98, dens(14), ((3.18, 0.28, 4.0),)), 0.532, 0.542, 180, 8, 0.025, dens(36),
         extra=sleeve_folds, name='sleeve')
    # the capelet's drape over the shoulder, torn at the hem, longest on the outside
    ta = tatter(40, 31, 0.12, slits=(7, 24), slit_h=0.1, closed=True)
    hem = lambda d: 3.5 - 0.3 * math.cos(math.radians(d)) - ta((d - 180) / 360)
    shell('LeftArm', 'Cloak', (cx + 0.02, 0), hem, 3.94, 0.16, lambda z: 0.625 + 0.09 * (3.94 - z) / 0.7,
          lambda z: 0.64 + 0.09 * (3.94 - z) / 0.7, 180, 540, ex=4, th=0.025, nu=dens(40), nv=dens(16), vw=0.45, closed=True,
          extra=lambda d, z: clamp((3.92 - z) / 0.6) * (0.03 * math.sin(math.radians(d) * 6) + 0.012 * math.sin(math.radians(d) * 13 + 1))
          + fine() * 0.003 * math.sin(math.radians(d) * 40 + z * 30), inside_z=3.5, bevel=0.006,
          name='drape')
    # the bracer: purple-black lacquered plate, ridged down the outside, rimmed in silver
    B = lambda z: 0.552 + 0.055 * (z - 2.22) / 0.76
    ridge = lambda d, z: 0.05 * max(0.0, math.cos(math.radians(d))) ** 6
    top = lambda d: 2.9 + 0.1 * max(0.0, math.cos(math.radians(d))) ** 2
    wrap('LeftArm', 'DarkMetal', (cx + 0.01, 0), 2.22, top, B, lambda z: B(z) + 0.01, -155, 155, ex=4, th=0.045, nu=36, nv=6,
         extra=ridge, name='bracer', trim=T('t', mat='Silver', w=0.035, th=0.02))
    for zs in (2.28, 2.66):   # straps over it, buckled at the front
        wrap('LeftArm', 'Strap', (cx + 0.01, 0), zs, zs + 0.065, lambda z: B(z) + 0.045, lambda z: B(z) + 0.055, -158, 158, ex=4,
             th=0.018, nu=36, nv=1, extra=ridge, bevel=0.004, name='bracer_strap')
        yb = -(B(zs) + 0.055 + 0.02 + 0.004)
        ring('LeftArm', 'Silver', (cx + 0.12, yb, zs + 0.0325), (0, -1, 0), (1, 0, 0), 0.05, 0.058, bar=0.018, th=0.02,
             name='bracer_buckle')
    # silver spikes: two up the outer ridge, one on the front
    for zs in (2.48, 2.84):
        x0 = cx + 0.01 + B(zs) + 0.05 + 0.045
        spike('LeftArm', 'Silver', (x0, 0, zs), (1, 0, 0.25), (0, 0, 1), h=0.2, l=0.1, w=0.055, lean=0.1)
    for deg, zs in ((-52, 2.48), (52, 2.84)):
        t = math.radians(deg)
        sx, sy = se(t, 4)
        p = Vector((cx + 0.01 + sx * (B(zs) + 0.045), sy * (B(zs) + 0.055), zs))
        spike('LeftArm', 'Silver', tuple(p), (sx, sy, 0.25), (0, 0, 1), h=0.15, l=0.08, w=0.045, lean=0.08)
    # the fingerless glove and its palm
    wrap('LeftArm', 'Leather', (cx + 0.005, 0), 1.975, 2.27, 0.528, 0.535, 180, 540, ex=6, th=0.032, nu=32, nv=3, closed=True,
         bevel=0.005, name='glove')
    slab('LeftArm', 'Leather', lambda u, v: (1.0 + 1.0 * u, -0.535 + 1.07 * v,
                                             1.975 - 0.02 * math.sin(math.pi * u) * math.sin(math.pi * v)),
         6, 6, 0.03, lambda p: (p[0], p[1], p[2] + 1), bevel=0.005, name='palm')
    for y in (-0.2, 0.0, 0.2):   # studs over the knuckles
        rivet('LeftArm', 'Silver', (cx + 0.005 + 0.528 + 0.03, y, 2.08), (1, 0, 0), 0.028, flat=0.6)


def pauldron():
    """on the left shoulder only: a leather cap and two lames, edged and riveted in silver"""
    cx = 1.5
    shell('LeftArm', 'Leather', (cx + 0.06, 0), lambda d: 3.74 + 0.18 * (abs(d) / 118) ** 2, 3.98, 0.25, 0.72, 0.7, -118, 118,
          ex=2.6, th=0.05, nu=30, nv=12, vw=0.32, inside_z=3.6, name='pauldron', trim=T('b', mat='Silver', w=0.04, th=0.022))
    for k, zb in ((1, 3.52), (2, 3.3)):
        R = lambda z, zb=zb, k=k: 0.76 + 0.05 * k - 0.32 * (z - zb)
        span = 100 - 8 * k
        wrap('LeftArm', 'Leather', (cx + 0.07 + 0.035 * k, 0), lambda d, zb=zb: zb - 0.06 * max(0.0, math.cos(math.radians(d))) ** 2,
             zb + 0.3, R, R, -span, span, ex=2.6, th=0.045, nu=26, nv=3, name='lame',
             trim=T('blr', mat='Silver', w=0.035, th=0.02))
    for t in (-55, 0, 55):   # rivets round the cap
        x, y = se(math.radians(t), 2.6)
        rivet('LeftArm', 'Silver', (cx + 0.06 + x * 0.735, y * 0.715, 3.9), (x, y, 0.15), 0.032, flat=0.6)


def leg():
    """the left leg (+X); the right one is its mirror"""
    cx = 0.5
    def trouser_folds(d, z):
        t = math.radians(d)
        blouse = env(z, 0.84, 1.08, 0.06) * (0.03 * math.sin(math.pi * clamp((z - 0.84) / 0.24))
                                              + 0.014 * puff(z * 55 + 2 * math.sin(t * 3)))
        knee = 0.016 * max(0.0, math.sin(t)) ** 2 * env(z, 0.98, 1.32, 0.08) * puff(z * 42 + 1.2 * math.cos(t))
        hip = 0.012 * max(0.0, -math.sin(t)) ** 1.5 * env(z, 1.6, 1.98, 0.1) * puff(z * 28 + 2.2 * math.cos(t))
        return blouse + knee + hip + 0.01 * math.sin(t * 6 + z * 2.5) + fine() * 0.003 * math.sin(z * 80 + t * 11)
    tube('LeftLeg', 'Trousers', (cx, 0), rows(0.62, 2.0, dens(16), ((0.96, 0.14, 3.0), (1.15, 0.18, 1.5), (1.8, 0.2, 1.2))),
         0.535, 0.545, 180, 8, 0.025, dens(36), extra=trouser_folds, name='trousers')
    # a seam down the outer front, riveted
    xs = 0.15
    if HIGH[0]:
        for k in range(6):
            rivet('LeftLeg', 'Steel', (cx + xs, -(0.545 + 0.025), 1.86 - k * 0.15), (0, -1, 0), 0.02, flat=0.6)
    # the knee guard: a kite of hardened leather with a sharp ridge, a silver diamond, and a strap behind
    W, zc = 0.25, 1.14
    kite = lambda x, z: 0.035 + 0.06 * (1 - abs(x) / W) + 0.03 * math.sin(math.pi * clamp((z - 0.87) / 0.6))
    sheet('LeftLeg', 'Leather', 'front', (0.545 + 0.02, cx), -W + 0.012, W - 0.012, lambda x: zc - 0.27 * (1 - abs(x) / W),
          lambda x: zc + 0.33 * (1 - abs(x) / W), kite, th=0.045, nu=12, nv=10, bevel=0.006, name='knee')
    w2 = 0.075
    sheet('LeftLeg', 'Silver', 'front', (0.545 + 0.02, cx), -w2 + 0.002, w2 - 0.002, lambda x: zc + 0.02 - 0.1 * (1 - abs(x) / w2),
          lambda x: zc + 0.02 + 0.12 * (1 - abs(x) / w2), lambda x, z: kite(x, z) + 0.045 + 0.02 * (1 - abs(x) / w2), th=0.02,
          nu=4, nv=4, bevel=0.004, name='knee_diamond')
    wrap('LeftLeg', 'Strap', (cx, 0), 1.1, 1.165, 0.565, 0.575, -86, 266, ex=8, th=0.02, nu=36, nv=1, bevel=0.004,
         name='knee_strap')
    # the boot: a tall leather boot with a toe box and a sole, a flared cuff, and crossing straps
    BC = (0.52, -0.03)
    BW, BD, BR = 0.55, 0.57, 0.14
    half = lambda hw, hd: 2 * (hw - BR) + 2 * (hd - BR) + math.pi * BR

    def toe(s_, z):
        return 0.16 * min(1.0, max(0.0, (0.32 - z) / 0.2)) ** 0.7 * max(0.0, 1 - abs(s_) / 0.65) ** 0.8
    H = half(BW, BD)
    crease = lambda s_, z: fine() * 0.007 * max(0.0, 1 - abs(s_) / 0.5) * env(z, 0.28, 0.58, 0.06) * puff(z * 60 + s_ * 4)
    bwrap('LeftLeg', 'Leather', BC, 0.04, 0.72, BW, BD, BR, -H, H, nu=dens(64), nv=dens(10, 3),
          extra=lambda s_, z: toe(s_, z) + crease(s_, z), name='boot')
    bwrap('LeftLeg', 'Leather', BC, 0.64, 0.87, BW + 0.03, BD + 0.03, BR, -H, H, nu=64, nv=3,
          extra=lambda s_, z: 0.07 * (z - 0.64) / 0.23 + 0.008 * math.sin(s_ * 9), name='boot_cuff')
    S = half(BW + 0.035, BD + 0.035)
    bwrap('LeftLeg', 'Leather', BC, -0.02, 0.05, BW + 0.035, BD + 0.035, BR, -S, S, nu=64, nv=1,
          extra=lambda s_, z: toe(s_, 0.04), name='sole')

    def sole_fill(u, v):
        s_ = -S + 2 * S * u
        x, y = rr_point(s_, BW + 0.035 + toe(s_, 0.04), BD + 0.035 + toe(s_, 0.04), BR)
        return (BC[0] + v * x, BC[1] + v * y, -0.02)
    slab('LeftLeg', 'Leather', sole_fill, 48, 3, 0.03, lambda p: (p[0], p[1], p[2] + 1), bevel=0.006, name='sole_bottom')
    for zc_, tilt, ph, lift in ((0.47, 0.1, 0.0, 0.018), (0.47, -0.1, 0.0, 0.03), (0.2, 0.0, 0.0, 0.018)):
        z0 = lambda s_, zc_=zc_, tilt=tilt, ph=ph: zc_ + tilt * math.sin(math.pi * s_ / H + ph)
        bwrap('LeftLeg', 'Strap', BC, z0, lambda s_, z0=z0: z0(s_) + 0.06, BW, BD, BR, -H, H, nu=48, nv=1,
              extra=lambda s_, z, lift=lift: toe(s_, z) + lift, bevel=0.004, name='boot_strap')
    ring('LeftLeg', 'Silver', (BC[0] + BW + 0.018 + 0.02 + 0.004, BC[1], 0.23), (1, 0, 0), (0, -1, 0), 0.05, 0.055,
         bar=0.018, th=0.02, name='boot_buckle')


def holster():
    """on the right leg only: two thigh straps with silver diamonds, and a pouch hung from the slung belt"""
    cx = -0.5
    for z in (1.6, 1.36):
        wrap('RightLeg', 'Strap', (cx, 0), z, z + 0.065, 0.565, 0.575, 180, 540, ex=8, th=0.02, nu=40, nv=1, closed=True,
             bevel=0.004, name='thigh_strap')
        w = 0.05
        sheet('RightLeg', 'Silver', 'front', (0.575 + 0.02, cx), -0.2 - w, -0.2 + w,
              lambda x, z=z: z + 0.0325 - 0.065 * (1 - abs(x + 0.2) / w), lambda x, z=z: z + 0.0325 + 0.065 * (1 - abs(x + 0.2) / w),
              lambda x, z: 0.004 + 0.015 * (1 - abs(x + 0.2) / w), th=0.016, nu=4, nv=4, bevel=0.003, name='strap_diamond')
    # the pouch on the outside of the thigh
    PC = (-1.11, 0.02)
    hw, hd, r = 0.075, 0.2, 0.04
    Hp = 2 * (hw - r) + 2 * (hd - r) + math.pi * r
    bwrap('RightLeg', 'Leather', PC, 1.3, 1.76, hw, hd, r, -Hp, Hp, nu=32, nv=4, th=0.025,
          extra=lambda s_, z: 0.012 * math.sin(math.pi * (z - 1.3) / 0.46), name='pouch')
    for z, sgn in ((1.3, 1), (1.76, -1)):
        slab('RightLeg', 'Leather', lambda u, v, z=z: (PC[0] - hw + 2 * hw * u, PC[1] - hd + 2 * hd * v, z), 2, 6, 0.025,
             lambda p, sgn=sgn: (p[0], p[1], p[2] + sgn), bevel=0.004, name='pouch_end')
    sheet('RightLeg', 'Leather', 'left', (-PC[0] + hw + 0.012, PC[1]), -0.215, 0.215, lambda x: 1.5 - 0.09 * (1 - abs(x) / 0.215),
          1.8, lambda x, z: 0.004 + 0.015 * (z - 1.5), th=0.022, nu=8, nv=4, bevel=0.005, name='pouch_flap')
    rivet('RightLeg', 'Silver', (PC[0] - hw - 0.05, PC[1], 1.44), (-1, 0, 0), 0.034, flat=0.6)
    for y in (-0.1, 0.14):   # the drop straps up to the slung belt
        sheet('RightLeg', 'Strap', 'left', (1.04, y), -0.03, 0.03, 1.74, 2.02,
              lambda x, z: 0.01 + 0.075 * clamp((2.0 - z) / 0.25), th=0.018, nu=1, nv=4, bevel=0.003, name='drop_strap')


def pieces():
    hat()
    collar()
    shirt_and_belts()
    capelet()
    cape()
    scarf()
    arm()
    leg()
    A.mirror_left_to_right()
    pauldron()
    holster()


# ------------------------------------------------------------------ materials

def material(name, kind, c1, c2, edge_col, rough, metal=0.0, stain=None, grime='#0b0a0c'):
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

    def op(kind_, a, b=None, clamp_=False):
        n = N.new('ShaderNodeMath')
        n.operation = kind_
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

    def band(x, a, b, soft=0.004):
        return op('MULTIPLY', rng(x, a - soft, a), rng(x, b + soft, b))

    duv = N.new('ShaderNodeSeparateXYZ')
    L.new(det.outputs['UV'], duv.inputs[0])
    du_, dv_ = duv.outputs['X'], duv.outputs['Y']
    geo = N.new('ShaderNodeNewGeometry')
    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.012
    bev.samples = 8
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.998, 0.96)
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.05
    ao.samples = 24
    cav = rng(ao.outputs['AO'], 0.1, 1.0, 0.5, 1.0)
    crease = rng(ao.outputs['AO'], 0.4, 0.95, 1.0, 0.0)
    low = noise(3.0, 3, 0.5)
    r0, r1 = rough
    if kind == 'cloth':
        # a fine twill, soft mottling, stains, edges worn pale where the cloth frays
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
        col = mix(op('MULTIPLY', low, 0.85), lin(c1), lin(c2))
        if stain:
            blot = rng(noise(1.4, 5, 0.62), 0.5, 0.68)
            col = mix(op('MULTIPLY', blot, 0.75), col, lin(stain))
            dust = rng(noise(2.4, 4, 0.6), 0.55, 0.75)
            col = mix(op('MULTIPLY', dust, 0.15), col, lin(edge_col))
        col = mix(op('MULTIPLY', weave, 0.12), col, lin(edge_col))
        col = mix(op('MULTIPLY', edge, 0.4), col, lin(edge_col))
        col = mix(op('MULTIPLY', crease, 0.5), col, lin(grime))
        rgh = op('ADD', rng(weave, 0.0, 1.0, r0, r1), op('MULTIPLY', edge, 0.05), clamp_=True)
        height = op('ADD', op('MULTIPLY', weave, 0.6), op('MULTIPLY', noise(4.0, 3), 0.4))
        bump_strength, bump_dist = 0.35, 0.003
    elif kind == 'leather':
        cells = N.new('ShaderNodeTexVoronoi')
        cells.inputs['Scale'].default_value = 70
        L.new(tc.outputs['Object'], cells.inputs['Vector'])
        wrinkle = noise(9.0, 6, 0.65)
        col = mix(op('MULTIPLY', low, 0.8), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', rng(wrinkle, 0.5, 0.75), 0.18), col, lin(edge_col))
        col = mix(op('MULTIPLY', edge, 0.45), col, lin(edge_col))
        col = mix(op('MULTIPLY', crease, 0.45), col, lin(grime))
        rgh = op('ADD', rng(wrinkle, 0.3, 0.7, r0, r1), op('MULTIPLY', edge, -0.15), clamp_=True)
        st = N.new('ShaderNodeMath')
        st.operation = 'FRACT'
        L.new(op('DIVIDE', du_, 0.03), st.inputs[0])
        stitch = op('MULTIPLY', band(st.outputs[0], 0.15, 0.65, 0.08), band(dv_, 0.016, 0.024, 0.003))
        groove = band(dv_, 0.01, 0.03, 0.004)
        col = mix(op('MULTIPLY', stitch, 0.85), col, lin('#6d6577'))
        col = mix(op('MULTIPLY', groove, 0.35), col, lin('#060508'))
        height = op('ADD', op('ADD', op('MULTIPLY', cells.outputs['Distance'], 0.5), op('MULTIPLY', wrinkle, 0.6)),
                    op('SUBTRACT', op('MULTIPLY', stitch, 0.6), op('MULTIPLY', groove, 0.4)))
        bump_strength, bump_dist = 0.3, 0.004
    elif kind == 'metal':
        grain = noise(1.0, 3, 0.6, vec=mapped(det.outputs['UV'], (6.0, 420.0, 1.0)))
        col = mix(op('MULTIPLY', low, 0.6), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', edge, 0.7), col, lin(edge_col))
        rgh = op('ADD', rng(grain, 0.3, 0.7, r0 - 0.03, r0 + 0.03), op('MULTIPLY', low, r1 - r0))
        rgh = op('SUBTRACT', rgh, op('MULTIPLY', edge, 0.1), clamp_=True)
        tarnish = op('MULTIPLY', crease, rng(noise(7.0, 5, 0.6), 0.3, 0.65))
        col = mix(op('MULTIPLY', tarnish, 0.7), col, lin(grime))
        rgh = op('ADD', rgh, op('MULTIPLY', tarnish, 0.25), clamp_=True)
        micro = []
        for rot in ((0.3, 0.0, 0.2), (1.1, 0.7, 2.0), (0.0, 1.3, 0.9)):
            micro.append(rng(noise(1.0, 1, 0.5, vec=mapped(tc.outputs['Object'], (160.0, 160.0, 2.5), rot)), 0.7, 0.74))
        mic = op('MULTIPLY', op('MAXIMUM', op('MAXIMUM', micro[0], micro[1]), micro[2]), rng(noise(3.0, 2), 0.45, 0.62))
        col = mix(op('MULTIPLY', mic, 0.3), col, lin(edge_col))
        rgh = op('SUBTRACT', rgh, op('MULTIPLY', mic, 0.1), clamp_=True)
        height = op('ADD', op('MULTIPLY', grain, 0.05), op('SUBTRACT', op('MULTIPLY', noise(5.0, 2, 0.4), 0.2),
                                                         op('MULTIPLY', mic, 0.15)))
        bump_strength, bump_dist = 0.1, 0.003
    elif kind == 'felt':
        fuzz = noise(70.0, 6, 0.7)
        col = mix(op('MULTIPLY', low, 0.8), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', rng(fuzz, 0.45, 0.8), 0.12), col, lin(edge_col))
        col = mix(op('MULTIPLY', edge, 0.4), col, lin(edge_col))
        col = mix(op('MULTIPLY', crease, 0.5), col, lin(grime))
        rgh = rng(fuzz, 0.3, 0.7, r0, r1)
        height = op('ADD', op('MULTIPLY', fuzz, 0.5), op('MULTIPLY', noise(8.0, 4), 0.5))
        bump_strength, bump_dist = 0.22, 0.002
    elif kind == 'glass':   # tinted lens glass: glossy, darker toward its rim
        col = mix(op('MULTIPLY', low, 0.6), lin(c1), lin(c2))
        col = mix(op('MULTIPLY', edge, 0.5), col, lin(edge_col))
        rgh = op('ADD', r0, op('MULTIPLY', rng(noise(12.0, 3), 0.4, 0.7), r1 - r0))
        height = op('MULTIPLY', noise(30.0, 2), 0.05)
        bump_strength, bump_dist = 0.05, 0.001
    else:   # feather: black at the quill, purple at the tip, fine barbs swept back
        along = rng(du_, -0.25, 0.32)
        col = mix(op('POWER', along, 1.8), lin(c1), lin(c2))
        sw = N.new('ShaderNodeTexWave')
        sw.inputs['Scale'].default_value = 1.0
        sw.inputs['Distortion'].default_value = 0.6
        acr = op('ABSOLUTE', op('SUBTRACT', dv_, 0.07))
        sweep = N.new('ShaderNodeCombineXYZ')
        L.new(op('ADD', du_, op('MULTIPLY', acr, 1.6)), sweep.inputs[0])
        L.new(mapped(sweep.outputs[0], (90.0, 90.0, 1.0)), sw.inputs['Vector'])
        barbs = sw.outputs['Fac']
        col = mix(op('MULTIPLY', barbs, 0.3), col, lin(edge_col))
        col = mix(op('MULTIPLY', rng(acr, 0.012, 0.0), 0.8), col, lin('#08070a'))   # the dark quill
        rgh = rng(barbs, 0.0, 1.0, r0, r1)
        height = barbs
        bump_strength, bump_dist = 0.3, 0.002
    col = mix(1.0, col, grey(cav), 'MULTIPLY')
    rb = N.new('ShaderNodeBevel')
    rb.inputs['Radius'].default_value = 0.006
    rb.samples = 8
    bn = N.new('ShaderNodeBump')
    bn.inputs['Strength'].default_value = bump_strength
    bn.inputs['Distance'].default_value = bump_dist
    L.new(height, bn.inputs['Height'])
    L.new(rb.outputs['Normal'], bn.inputs['Normal'])
    mv = N.new('ShaderNodeValue')
    mv.outputs[0].default_value = metal
    tags = {}
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


SOFT = {'Cloak', 'Lining', 'Silk', 'Shirt', 'Trousers', 'Felt', 'Binding', 'Feather'}   # shaded smooth up to 60 deg


def materials():
    material('Cloak', 'cloth', '#0f0e11', '#161418', '#2e2a33', (0.82, 0.95), stain='#070608')
    material('Lining', 'cloth', '#230a3c', '#2d0d4e', '#46207a', (0.6, 0.78))
    material('Silk', 'cloth', '#3a0f6c', '#4a1688', '#7543bd', (0.42, 0.58), grime='#12051f')
    material('Shirt', 'cloth', '#0c0b0e', '#111014', '#24222a', (0.85, 0.95))
    material('Trousers', 'cloth', '#0e0d11', '#141318', '#26242c', (0.8, 0.94), stain='#070609')
    material('Leather', 'leather', '#0e0b11', '#141018', '#30283a', (0.42, 0.68))
    material('Strap', 'leather', '#1a1320', '#221928', '#3e3247', (0.45, 0.7))
    material('Silver', 'metal', '#a7abb4', '#c3c6ce', '#f1f3f7', (0.17, 0.3), 1.0, grime='#3a3a42')
    material('Steel', 'metal', '#8c9099', '#9fa3ac', '#dadde4', (0.24, 0.36), 1.0, grime='#33333a')
    material('DarkMetal', 'metal', '#171320', '#201929', '#6e52a8', (0.28, 0.42), 0.9, grime='#070609')
    material('Felt', 'felt', '#0d0c0f', '#121114', '#2a2730', (0.82, 0.95))
    material('Binding', 'cloth', '#0e0d10', '#131216', '#2e2b33', (0.38, 0.5))
    material('Lens', 'glass', '#2c0b58', '#3d1477', '#9a72e0', (0.04, 0.1))
    material('Feather', 'feather', '#0d0b11', '#5a22a6', '#7a4fc0', (0.35, 0.5))


# ------------------------------------------------------------------ assembly

def join(prefix):
    """one mesh per part, each piece shaded smooth with hard edges past 35 deg (60 for cloth and felt)"""
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for part in PARTS:
        obs = [ob for p, ob in A.PIECES if p == part]
        if not obs:
            continue
        bm = bmesh.new()
        mats = []
        for ob in obs:
            m = ob.data.materials[0]
            if m not in mats:
                mats.append(m)
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            for poly in me.polygons:
                poly.material_index = mats.index(m)
            A.smooth(me, 60 if m.name in SOFT else 35)
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
        out[part] = ob
    return out


def build(high=True):
    materials()
    HIGH[0] = False
    A.PIECES.clear()
    pieces()
    if STAGE == 'stats':
        dg = bpy.context.evaluated_depsgraph_get()
        rows = {}
        for part, ob in A.PIECES:
            me = ob.evaluated_get(dg).to_mesh()
            k = (part, ob.name.split('.')[0])
            rows[k] = rows.get(k, 0) + sum(len(p.vertices) - 2 for p in me.polygons)
        for (part, name), n in sorted(rows.items(), key=lambda r: -r[1]):
            print(f'{part:10s} {name:16s} {n}')
    low = join(PREFIX)
    if not high:
        return low, {}
    A.PIECES.clear()
    HIGH[0] = True
    pieces()
    hi = join('High_')
    HIGH[0] = False
    return low, hi


# ------------------------------------------------------------------ rig, preview, export

def rig_chain(ob, prefix, path, knots):
    """bones along a strip that streams out sideways (the scarf): a root over path(knots[0]..knots[1]),
    then a chain through the rest. Each vertex is weighted by how far along the strip it lies, blending
    between the two nearest bones"""
    samples = [path(i / 400) for i in range(401)]
    kd = KDTree(len(samples))
    for i, p in enumerate(samples):
        kd.insert(p, i)
    kd.balance()
    ad = bpy.data.armatures.new('Rig_' + prefix)
    arm = bpy.data.objects.new('Rig_' + prefix, ad)
    bpy.context.scene.collection.objects.link(arm)
    names = []
    with bpy.context.temp_override(active_object=arm, object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        parent = None
        for i in range(len(knots) - 1):
            b = ad.edit_bones.new(prefix + 'Root' if i == 0 else f'{prefix}_{i - 1}')
            b.head, b.tail = path(knots[i]), path(knots[i + 1])
            b.parent = parent
            b.use_connect = parent is not None
            parent = b
            names.append(b.name)
        bpy.ops.object.mode_set(mode='OBJECT')
    groups = {n: ob.vertex_groups.new(name=n) for n in names}
    mids = [(knots[i] + knots[i + 1]) / 2 for i in range(len(knots) - 1)]
    for v in ob.data.vertices:
        s = kd.find(ob.matrix_world @ v.co)[1] / 400
        if s <= mids[0]:
            w = {0: 1.0}
        elif s >= mids[-1]:
            w = {len(mids) - 1: 1.0}
        else:
            k = max(i for i in range(len(mids)) if mids[i] <= s)
            f = (s - mids[k]) / (mids[k + 1] - mids[k])
            w = {k: 1 - f, k + 1: f}
        for k, x in w.items():
            if x > 0:
                groups[names[k]].add([v.index], x, 'REPLACE')
    ob.parent = arm
    md = ob.modifiers.new('rig', 'ARMATURE')
    md.object = arm
    return arm


def preview(path, samples=48):
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 640, 760
    shots = []
    for i, (az, el) in enumerate(((0, 8), (40, 10), (180, 8))):
        a = math.radians(az - 90)
        d = 19.0
        cam_d.lens = 85
        cam.location = (0.35 + d * math.cos(a) * math.cos(math.radians(el)), d * math.sin(a) * math.cos(math.radians(el)),
                        2.9 + d * math.sin(math.radians(el)))
        cam.rotation_euler = (Vector((0.35, 0, 2.85)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
    # close-ups: the hat and collar from the front three-quarter, and the left side
    sc.render.resolution_x, sc.render.resolution_y = 900, 900
    for tag, az, tgt, dist, z in (('closeup', -30, (0.2, 0, 3.75), 9.5, 4.9), ('side', 75, (0.6, 0, 2.6), 15, 3.6)):
        a = math.radians(az - 90)
        cam.location = (dist * math.cos(a), dist * math.sin(a), z)
        cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path.replace('.png', f'_{tag}.png')
        bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def export(objs, refs):
    for o in bpy.data.objects:
        o.select_set(False)
    rigs = []
    if 'Cape' in objs:
        rigs.append(A.rig_cloth(objs['Cape'], 'Cape', (-0.8, 0.0, 0.8), (3.88, 3.0, 2.12, 1.25, 0.35)))
    if 'Scarf' in objs:
        rigs.append(rig_chain(objs['Scarf'], 'Scarf', scarf_path, (0.0, 0.1, 0.27, 0.44, 0.61, 0.78, 1.0)))
    for o in bpy.data.objects:
        o.select_set(False)
    for o in list(objs.values()) + list(refs.values()) + rigs:
        o.select_set(True)
    fbx = os.path.join(OUT, 'WandererOutfit.fbx')
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH', 'ARMATURE'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP',
                             add_leaf_bones=False, armature_nodetype='NULL', bake_anim=False)
    print('EXPORTED', fbx, flush=True)


def main():
    A.reset()
    objs, highs = build(high=STAGE != 'stats')
    A.PARTS = BODY
    refs = A.load_rig()
    A.PARTS = PARTS
    os.makedirs(OUT, exist_ok=True)
    for ob in list(objs.values()) + list(highs.values()):
        print(ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), flush=True)
    if STAGE == 'stats':
        return
    if STAGE == 'preview':
        for ob in objs.values():
            ob.hide_render = True
        preview(os.path.join(OUT, 'preview.png'), samples=int(A.opt('--samples', '32')))
        return
    maps = A.bake(objs, highs, RES)
    A.baked_materials(objs, maps)
    preview(os.path.join(OUT, 'preview.png'))
    if not A.ONLY:
        export(objs, refs)


if __name__ == '__main__':
    main()
