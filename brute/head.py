"""The Brute's head: the R6 head's own shape and proportions, with an original brutish face sculpted into it.

It's built the way you'd sculpt it in clay. The base is the plain R6 head (a cylinder as tall as it is wide, its top
and bottom edges rounded over), and onto it go solid forms (ellipsoids, rounded boxes, tubes along curves that swell
and taper), each blended in or carved out: the brow, the sockets, the nose, the muzzle, the lips and teeth, the eyes. No ears.
The head is the surface of all of them together, found by firing rays out from inside it along directions laid out
round it (crowded toward the face). The rays start up and down its middle at the height they're aimed at, so they meet
the brow, the lids and the lips square on rather than glancing up or down past them. Fine detail (creases, wrinkles, the lines of the snarl, scars) is then pushed in
or out along that surface.

Units are head radii (an R6 head is 2 across and 2 tall): x toward the head's left, y back (the face looks down -y),
z up, from the head's centre. Features on the +x side are mirrored to the other.

    FORMS, DETAILS         the sculpt, in the order it's built up
    grid(nu, nv)           the ray directions
    build(G, scale, centre, name, upto) -> the head as a mesh; update() re-sculpts it in place
    eyes(scale, centre)    the two eyeballs, their own mesh (they glow)
"""
import math
import bmesh, bpy
import numpy as np
from mathutils import Vector, Matrix

R6_R = 0.6                          # an R6 head's radius, in studs


# ------------------------------------------------------------------ solids (signed distances, numpy)

def length(v):
    return np.sqrt((v * v).sum(-1))


def ellipsoid(P, c, r):
    q = P - np.asarray(c, float)
    r = np.asarray(r, float)
    k0 = length(q / r)
    k1 = length(q / (r * r))
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)


def sphere(P, c, r):
    return length(P - np.asarray(c, float)) - r


def rbox(P, c, half, rad, frame=None):
    """a box with rounded edges; frame (3x3, its columns the box's axes) turns it"""
    q = P - np.asarray(c, float)
    if frame is not None:
        q = q @ np.asarray(frame, float)
    q = np.abs(q) - (np.asarray(half, float) - rad)
    return length(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - rad


def catmull(ctrl, n):
    """a smooth curve through the control points (each a tuple of any length), n points along it"""
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


def tube(P, ctrl, n=0):
    """a tube along a curve, its radius swelling and tapering: ctrl is a list of (x, y, z, radius); with n, it's
    smoothed into a curve of n points first"""
    pts = catmull(ctrl, n) if n else np.asarray(ctrl, float)
    best = np.full(P.shape[:-1], 1e9)
    for i in range(len(pts) - 1):
        a, b = pts[i, :3], pts[i + 1, :3]
        ra, rb = pts[i, 3], pts[i + 1, 3]
        ba = b - a
        t = np.clip(((P - a) @ ba) / max(ba @ ba, 1e-12), 0, 1)
        d = length(P - (a + t[..., None] * ba)) - (ra + t * (rb - ra))
        best = np.minimum(best, d)
    return best


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def add(d, s, k):
    return smin(d, s, k)


def carve(d, s, k):
    return -smin(-d, s, k)


# ------------------------------------------------------------------ the forms

FORMS = []      # (name, fn(P, M, d) -> d): P the points, M the same with x mirrored onto the +x side


def form(name):
    def deco(f):
        FORMS.append((name, f))
        return f
    return deco


def rcyl(P, r, h, rad):
    """an upright cylinder, its top and bottom edges rounded over"""
    q = np.stack([np.hypot(P[..., 0], P[..., 1]) - (r - rad), np.abs(P[..., 2]) - (h - rad)], -1)
    return length(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - rad


def face_y(x, z):
    """where the plain R6 head's front is, at (x, z): its sides upright between z -0.5 and 0.5, rounded over above
    and below"""
    az = np.abs(z)
    R = np.where(az <= 0.5, 1.0, 0.5 + np.sqrt(np.clip(0.25 - (az - 0.5) ** 2, 0, None)))
    return -np.sqrt(np.clip(R * R - x * x, 0, None))


def at(x, z, out):
    """a point `out` in front of the plain head's surface, at (x, z)"""
    return (x, float(face_y(x, z)) - out, z)


def on(x, z, out, r):
    """a tube's control point whose front stands `out` proud of the plain head's surface at (x, z), its radius r"""
    return (x, float(face_y(x, z)) - out + r, z, r)


EYE = (0.355, 0.125)                      # the left eye, on the face
EYE_R = 0.115
EYE_C = np.array([EYE[0], float(face_y(*EYE)) + 0.05 + EYE_R, EYE[1]])    # its eyeball's centre
EYE_W = 0.145                             # half the width of the opening between its lids
LID_T = 0.03                              # how far the lids stand off the eyeball
Z_M = -0.43                               # the line the teeth meet on
X_M = 0.28                                # the mouth's corners


@form('the plain R6 head')
def _base(P, M, d):
    return rcyl(P, 1.0, 1.0, 0.5)


@form('the brow: a heavy ridge, its inner ends dragged down into a scowl')
def _brow(P, M, d):
    d = add(d, tube(M, [on(0.0, 0.25, 0.05, 0.06), on(0.15, 0.285, 0.09, 0.08), on(0.36, 0.34, 0.1, 0.085),
                        on(0.58, 0.32, 0.06, 0.07), on(0.78, 0.26, -0.03, 0.05)], 20), 0.09)
    d = add(d, ellipsoid(P, at(0.0, 0.25, -0.02), (0.1, 0.08, 0.08)), 0.06)     # bunched between the brows
    return d


@form('eye sockets, carved in deepest under the brow')
def _sockets(P, M, d):
    d = carve(d, ellipsoid(M, at(EYE[0], EYE[1] + 0.005, 0.03), (0.17, 0.12, 0.1)), 0.06)
    return carve(d, ellipsoid(M, at(EYE[0] - 0.01, EYE[1] + 0.06, 0.05), (0.16, 0.08, 0.085)), 0.05)


@form('the nose: broad and flattened, broken once, its wings flared')
def _nose(P, M, d):
    d = add(d, tube(P, [on(0.0, 0.25, 0.015, 0.05), on(0.0, 0.12, 0.07, 0.058), on(0.014, 0.04, 0.115, 0.064),
                        on(0.007, -0.05, 0.16, 0.074), on(0.0, -0.11, 0.195, 0.082)], 12), 0.05)
    d = add(d, ellipsoid(P, at(0.0, -0.12, 0.115), (0.1, 0.095, 0.08)), 0.04)    # the tip
    d = add(d, ellipsoid(M, at(0.12, -0.15, 0.0), (0.075, 0.08, 0.065)), 0.04)   # the wings
    d = add(d, ellipsoid(P, at(0.0, -0.14, -0.08), (0.2, 0.1, 0.1)), 0.08)       # its base, into the face
    d = carve(d, ellipsoid(M, at(0.064, -0.205, 0.13), (0.032, 0.05, 0.025)), 0.015)   # the nostrils
    return d


def arch(x):
    """the front of the upper teeth, curving back round the mouth"""
    return -1.035 + 1.1 * x * x


def lip_lift(x):
    """how far the upper lip is drawn up off the teeth (most over the canines: a snarl), and the lower lip down"""
    c = np.clip(1 - (np.abs(x) / X_M) ** 2.5, 0, 1) ** 0.6
    up = (0.06 + 0.032 * np.exp(-((np.abs(x) - 0.145) / 0.07) ** 2)) * c
    return up, 0.046 * c ** 0.8


def mouth_line(x):
    return Z_M - 0.03 * (np.asarray(x) / X_M) ** 2       # its corners pulled down


@form('the muzzle, and a square chin')
def _muzzle(P, M, d):
    d = add(d, ellipsoid(P, at(0.0, -0.44, -0.26), (0.42, 0.34, 0.25)), 0.12)
    d = add(d, ellipsoid(M, at(0.3, -0.46, 0.0), (0.05, 0.05, 0.05)), 0.04)      # the knots at the corners
    d = add(d, rbox(P, at(0.0, -0.7, -0.08), (0.25, 0.14, 0.15), 0.1), 0.1)
    return d


@form('the snarl: cheeks bunched up, the sides of the nose drawn up')
def _snarl(P, M, d):
    d = add(d, ellipsoid(M, at(0.3, -0.16, -0.08), (0.13, 0.11, 0.11)), 0.1)
    d = add(d, ellipsoid(M, at(0.17, -0.03, -0.06), (0.07, 0.08, 0.1)), 0.06)
    return d


def teeth(P, M):
    """the teeth showing in the snarl: upper incisors and fangs, the lower front teeth behind them, clenched"""
    d = np.full(P.shape[:-1], 1e9)
    for xc, w, h, kind in ((0.042, 0.082, 0.1, 'i'), (0.115, 0.064, 0.09, 'i'), (0.175, 0.058, 0.115, 'c'),
                           (0.228, 0.05, 0.075, 'p')):
        s = 2.2 * xc
        t = np.array([1, s, 0]) / math.hypot(1, s)
        n = np.array([s, -1, 0]) / math.hypot(1, s)
        front = np.array([xc, arch(xc), 0])
        if kind == 'c':
            top = front - n * 0.03 + np.array([0, 0, Z_M + 0.105])
            tip = front - n * 0.026 + np.array([0, 0, Z_M + 0.105 - h])
            d = np.minimum(d, tube(M, [(*top, 0.029), (*(top * 0.4 + tip * 0.6), 0.025), (*tip, 0.008)], 6))
        else:
            c = front - n * 0.028 + np.array([0, 0, Z_M + 0.105 - h / 2])
            d = np.minimum(d, rbox(M, c, (w / 2 - 0.003, 0.028, h / 2), 0.014, np.stack([t, -n, (0, 0, 1)], 1)))
    for xc, w, h in ((0.031, 0.06, 0.085), (0.09, 0.056, 0.085), (0.146, 0.056, 0.095), (0.2, 0.05, 0.075)):
        s = 2.2 * xc
        t = np.array([1, s, 0]) / math.hypot(1, s)
        n = np.array([s, -1, 0]) / math.hypot(1, s)
        c = np.array([xc, arch(xc) + 0.03, Z_M - 0.005 - h / 2]) - n * 0.026
        d = np.minimum(d, rbox(M, c, (w / 2 - 0.003, 0.026, h / 2), 0.013, np.stack([t, -n, (0, 0, 1)], 1)))
    # the gums above and below them
    gx = np.linspace(0, 0.26, 8)
    d = np.minimum(d, tube(M, [(x, arch(x) + 0.05, Z_M + 0.12, 0.044) for x in gx]))
    d = np.minimum(d, tube(M, [(x, arch(x) + 0.08, Z_M - 0.11, 0.044) for x in gx]))
    return d


@form('the mouth: the lips drawn back off clenched teeth')
def _mouth(P, M, d):
    x, y, z = M[..., 0], M[..., 1], M[..., 2]
    up, lo = lip_lift(x)
    zm = mouth_line(x)
    opening = np.maximum(z - (zm + up), (zm - lo) - z)
    opening = np.maximum(opening, (x - X_M) * 0.5)
    hole = np.maximum(opening, y - (arch(np.minimum(x, X_M)) + 0.1))
    d = carve(d, hole, 0.012)
    d = np.minimum(d, teeth(P, M))
    xs = np.linspace(0, X_M + 0.01, 9)
    u_, l_ = lip_lift(xs)
    zs = mouth_line(xs)
    ru = 0.026 - 0.012 * (xs / X_M) ** 2
    rl = 0.034 - 0.017 * (xs / X_M) ** 2
    d = add(d, tube(M, [(xx, arch(xx) - 0.032, zz + uu + r * 0.55, r) for xx, zz, uu, r in zip(xs, zs, u_, ru)], 24),
            0.025)
    d = add(d, tube(M, [(xx, arch(xx) - 0.022, zz - ll - r * 0.5, r) for xx, zz, ll, r in zip(xs, zs, l_, rl)], 24),
            0.025)
    return d


def almond(qx):
    """the opening between the lids, in the eyeball's frame (qx across it, out from the nose): the heights of its
    upper and lower edges. It slants down toward the nose (a glare), its upper lid highest toward the outside"""
    s = np.clip(qx / EYE_W, -1.6, 1.6)
    tilt = 0.12 * qx + 0.004
    return (0.05 * (1 - s * s) * (1 + 0.15 * s) + tilt,
            -0.036 * (1 - s * s) * (1 - 0.1 * s) + tilt)


def lid_curve(f, s0, s1, lift, r, n=9):
    """a tube lying on the lids, following the opening's edge (f picks the upper or lower edge) lifted off it"""
    pts = []
    for s in np.linspace(s0, s1, n):
        qx = s * EYE_W * 1.05
        qz = almond(qx)[f] + lift * (1 - 0.35 * s * s)
        rr = EYE_R + LID_T + 0.002
        qy = -math.sqrt(max(rr * rr - qx * qx - qz * qz, 1e-6))
        pts.append((EYE_C[0] + qx, EYE_C[1] + qy, EYE_C[2] + qz, r))
    return pts


@form('the eyes: heavy lids, the lower lids drawn up tight, the eyeballs in them')
def _eyes(P, M, d):
    q = M - EYE_C
    zu, zl = almond(q[..., 0])
    opening = np.maximum(q[..., 2] - zu, zl - q[..., 2])
    lids = -smin(-(length(q) - (EYE_R + LID_T)), opening, 0.008)
    d = add(d, lids, 0.03)
    d = carve(d, tube(M, lid_curve(0, -1.05, 1.1, 0.04, 0.014), 16), 0.02)        # the fold over the upper lid
    d = carve(d, tube(M, lid_curve(1, -0.7, 1.05, -0.042, 0.012), 16), 0.03)      # the crease under the lower
    inner = EYE_C + np.array([-EYE_W * 1.02, -math.sqrt((EYE_R + LID_T) ** 2 - EYE_W ** 2), almond(-EYE_W)[0]])
    d = carve(d, ellipsoid(M, inner, (0.022, 0.03, 0.018)), 0.01)                   # the inner corner
    return np.minimum(d, sphere(M, EYE_C, EYE_R - 0.012))     # a socket behind the eye (its own mesh, eyes())


def sdf(P, upto=None):
    M = P.copy()
    M[..., 0] = np.abs(M[..., 0])
    d = np.full(P.shape[:-1], 1e3)
    for name, f in FORMS[:upto]:
        d = f(P, M, d)
    return d


# ------------------------------------------------------------------ fine detail (heights over the face)

def seg_dist(X, Z, pts):
    """distance from each point to a polyline, and how far along it (0..1) the nearest point is"""
    best = np.full(X.shape, 1e9)
    along = np.zeros(X.shape)
    lens = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(lens) or 1.0
    acc = 0.0
    for i in range(len(pts) - 1):
        (ax, az), (bx, bz) = pts[i], pts[i + 1]
        dx, dz = bx - ax, bz - az
        t = np.clip(((X - ax) * dx + (Z - az) * dz) / max(dx * dx + dz * dz, 1e-12), 0, 1)
        dd = np.hypot(X - ax - t * dx, Z - az - t * dz)
        closer = dd < best
        best = np.where(closer, dd, best)
        along = np.where(closer, (acc + t * lens[i]) / total, along)
        acc += lens[i]
    return best, along


def ridge(X, Z, pts, w, h, taper=None):
    """a raised line (or with h < 0, a crease) along a polyline, its height eased by taper(along)"""
    dd, a = seg_dist(X, Z, pts)
    k = taper(a) if taper is not None else 1.0
    return h * k * np.exp(-(dd / w) ** 2)


def blob(X, Z, cx, cz, rx, rz, h):
    return h * np.exp(-(((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2))


def mirror(f):
    return lambda X, Z: f(X, Z) + f(-X, Z)


def ends(a, soft=0.25):
    return np.clip(a / soft, 0, 1) * np.clip((1 - a) / soft, 0, 1)


DETAILS = []    # (name, fn(X, Z) -> height): X, Z the point's x and height, seen from the front


def detail(name):
    def deco(f):
        DETAILS.append((name, f))
        return f
    return deco


@detail('creases: the scowl, the wrinkled nose, the folds of the snarl')
def _creases(X, Z):
    h = mirror(lambda x, z: ridge(x, z, [(0.045, 0.2), (0.06, 0.3), (0.08, 0.4)], 0.014, -0.02, ends))(X, Z)
    h += ridge(X, Z, [(-0.09, 0.2), (0.0, 0.185), (0.09, 0.2)], 0.012, -0.012, ends)
    h += mirror(lambda x, z: sum(ridge(x, z, [(0.045, zz), (0.1, zz - 0.035), (0.14, zz - 0.08)], 0.011, -0.009, ends)
                                 for zz in (0.13, 0.09, 0.05)))(X, Z)
    h += mirror(lambda x, z: ridge(x, z, [(0.2, -0.1), (0.25, -0.2), (0.31, -0.33), (0.34, -0.47)], 0.018, -0.035,
                                   lambda a: np.clip(a / 0.1, 0, 1) * np.clip((1 - a) / 0.35, 0, 1)))(X, Z)
    h += mirror(lambda x, z: ridge(x, z, [(0.25, 0.0), (0.36, -0.03), (0.47, -0.005)], 0.012, -0.012, ends))(X, Z)
    h += mirror(lambda x, z: sum(ridge(x, z, [(0.53, 0.2 - k * 0.05), (0.6, 0.21 - k * 0.075)], 0.011, -0.009, ends)
                                 for k in range(3)))(X, Z)
    h += mirror(lambda x, z: ridge(x, z, [(0.035, -0.22), (0.04, -0.33)], 0.012, 0.008, ends))(X, Z)
    h += ridge(X, Z, [(-0.2, -0.585), (0.0, -0.6), (0.2, -0.585)], 0.02, -0.02, ends)
    return h


@detail('detail: forehead lines, an old scar across the brow, another on the cheek')
def _detail(X, Z):
    h = ridge(X, Z, [(-0.42, 0.55), (-0.2, 0.53), (0.0, 0.51), (0.2, 0.53), (0.42, 0.55)], 0.016, -0.011, ends)
    h += ridge(X, Z, [(-0.36, 0.64), (0.0, 0.62), (0.36, 0.64)], 0.016, -0.009, ends)
    for pts in ([(0.2, 0.66), (0.29, 0.44), (0.36, 0.3)], [(0.5, 0.02), (0.58, -0.14), (0.64, -0.3)]):
        h += ridge(X, Z, pts, 0.016, 0.01, ends)
        dd, a = seg_dist(X, Z, pts)
        h -= 0.007 * ends(a) * np.exp(-((dd - 0.026) / 0.012) ** 2)
    return h


def heights(X, Z, front, upto):
    h = np.zeros_like(X)
    for name, f in DETAILS[:upto]:
        h = h + f(X, Z)
    return h * front


# ------------------------------------------------------------------ the head

def spaced(n, lo, hi, dens, closed):
    x = np.linspace(lo, hi, 4001)
    dv = dens(x)
    c = np.concatenate([[0], np.cumsum((dv[1:] + dv[:-1]) / 2 * np.diff(x))])
    c /= c[-1]
    t = np.arange(n) / n if closed else np.linspace(0, 1, n)
    return np.interp(t, c, x)


def grid(nu, nv):
    """ray directions round the head: nu columns (from the back, round through the front), nv + 1 rows bottom to
    top, crowded toward the face"""
    th = np.radians(spaced(nu, -270, 90, lambda t: 1 + 2.4 * np.exp(-((t + 90) / 55) ** 2), True))
    ph = np.radians(spaced(nv + 1, -89, 89, lambda p: 1 + 1.8 * np.exp(-((p + 10) / 38) ** 2), False))
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    D = np.stack([np.cos(TH) * np.cos(PH), np.sin(TH) * np.cos(PH), np.sin(PH)], -1)
    return dict(D=D, nu=nu, nv=nv)


def origin(D):
    """where the ray along each direction starts: on the head's upright middle line, higher for rays aimed higher"""
    return np.stack([np.zeros(D.shape[:-1]), np.zeros(D.shape[:-1]), 0.7 * D[..., 2]], -1)


def cast(D, upto=None, r_max=2.2):
    """where each ray leaves the head (its outermost crossing)"""
    shape = D.shape[:-1]
    D = D.reshape(-1, 3)
    O = origin(D)
    n = len(D)
    r = np.full(n, r_max)
    out = np.full(n, r_max)
    act = np.arange(n)
    for _ in range(400):
        d = sdf(O[act] + D[act] * r[act, None], upto)
        inside = d < 0
        keep = act[~inside]
        step = np.maximum(d[~inside] * 0.7, 0.0015)
        out[keep] = r[keep]
        r[keep] = np.maximum(r[keep] - step, 0)
        act = keep[r[keep] > 0]
        if not len(act):
            break
    lo, hi = r.copy(), out.copy()
    for _ in range(24):
        mid = (lo + hi) / 2
        ins = sdf(O + D * mid[:, None], upto) < 0
        lo = np.where(ins, mid, lo)
        hi = np.where(ins, hi, mid)
    return (O + D * ((lo + hi) / 2)[:, None]).reshape(shape + (3,))


def normals(P, upto=None, e=0.002):
    g = np.zeros_like(P)
    for k in range(3):
        o = np.zeros(3)
        o[k] = e
        g[..., k] = sdf(P + o, upto) - sdf(P - o, upto)
    return g / np.maximum(length(g)[..., None], 1e-9)


def points(G, scale, centre, upto=None):
    """the sculpted head's points on the grid (its two pole points last), with the first `upto` steps of the sculpt
    (the forms, then the details)"""
    nf = len(FORMS)
    fu = None if upto is None or upto > nf else upto
    du = len(DETAILS) if upto is None else max(0, upto - nf)
    P = cast(G['D'], fu)
    if du:
        N = normals(P, fu)
        front = np.clip((-G['D'][..., 1] - 0.15) / 0.35, 0, 1)
        P = P + N * heights(P[..., 0], P[..., 2], front, du)[..., None]
    G['P'] = P
    Q = P * R6_R * scale + np.array(centre)
    poles = np.stack([Q[:, 0].mean(0), Q[:, -1].mean(0)])
    return np.concatenate([Q.reshape(-1, 3), poles])


def build(G, scale, centre, name, upto=None):
    """the head as a mesh: a quad grid round it, closed at the top and bottom by a fan to a pole. Its points can be
    re-sculpted in place with update()"""
    nu, nv = G['nu'], G['nv']
    Q = points(G, scale, centre, upto)
    me = bpy.data.meshes.new(name)
    idx = lambda i, j: (i % nu) * (nv + 1) + j
    faces = [(idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)) for i in range(nu) for j in range(nv)]
    bot, top = nu * (nv + 1), nu * (nv + 1) + 1
    faces += [(bot, idx(i + 1, 0), idx(i, 0)) for i in range(nu)]
    faces += [(top, idx(i, nv), idx(i + 1, nv)) for i in range(nu)]
    me.from_pydata([tuple(q) for q in Q], [], faces)
    uv = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth = True
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            if vi >= nu * (nv + 1):
                uv.data[li].uv = (0.5, 0.0 if vi == bot else 1.0)
            else:
                i, j = divmod(vi, nv + 1)
                uv.data[li].uv = (i / nu, j / nv)
    for p in me.polygons:      # the seam: the last column's faces reach back round to column 0
        us = [uv.data[li].uv.x for li in p.loop_indices]
        if max(us) - min(us) > 0.5:
            for li in p.loop_indices:
                if uv.data[li].uv.x < 0.5:
                    uv.data[li].uv.x += 1.0
    me.update()
    if sum(p.normal.dot(Vector(p.center) - Vector(centre)) for p in me.polygons) < 0:
        me.flip_normals()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def update(ob, G, scale, centre, upto=None):
    Q = points(G, scale, centre, upto)
    ob.data.vertices.foreach_set('co', Q.astype(np.float32).ravel())
    ob.data.update()


STEPS = len(FORMS) + len(DETAILS)


def step_name(k):
    return FORMS[k - 1][0] if k <= len(FORMS) else DETAILS[k - 1 - len(FORMS)][0]


def eyes(scale, centre, name='Brute_Eyes'):
    """the two eyeballs as their own mesh (to glow: Neon in Studio), filling the openings between the lids"""
    bm = bmesh.new()
    for side in (1, -1):
        c = EYE_C * np.array([side, 1, 1])
        m = Matrix.Translation(Vector(c * R6_R * scale) + Vector(centre)) @ Matrix.Scale(EYE_R * R6_R * scale, 4)
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0, matrix=m)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.new(name='UVMap')
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob
