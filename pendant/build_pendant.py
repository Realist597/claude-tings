"""A silver pendant on a chain for the R6 body, drawn from reference.png: a pear-cut amethyst, point up, in a silver
bezel inside a cage of thorns, hung from a leafed bail on a cable chain. The chain lies round the neck the way a
necklace would on the blocky R6 body: across the top of the torso either side of the head, just over the back's top
edge, and over the front edge and down the chest to the pendant.

Two meshes, each a light game mesh with its detailed version's shape and stylised paint baked onto it (oxidised
dark in the recesses, bright silver where it stands proud, the gem's facets light and dark):
    Pendant_Chain   the chain; every link shares one patch of its texture
    Pendant_Charm   the bail, the cage and the gem

    python build_pendant.py -- --stage all       # build, bake, preview and export
    python build_pendant.py -- --stage preview   # build and render the detailed versions only (quick)
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as A                 # noqa: E402

STAGE = A.STAGE
OUT = os.path.join(HERE, 'export')

TORSO = ((-1.0, 1.0), (-0.5, 0.5), (2.0, 4.0))   # the R6 torso's box (studs)
LIFT = 0.082            # how far the pendant stands off the chest (its back just clears it)
CHARM_SCALE = 1.3       # the pendant drawn below, scaled up to sit right against the chain

# a chain link: a stadium of wire. Half the straight, the radius of its ends (both to the wire's centre), the wire
LINK_H, LINK_R, WIRE = 0.022, 0.024, 0.012
PITCH = 2 * (LINK_H + LINK_R) - 2 * WIRE        # centre to centre, each link's ends through its neighbours'

SILVER, OXIDE, HIGHLIGHT = '#c3c0bb', '#35302c', '#f1eee8'
GEM_DARK, GEM_MID, GEM_LIGHT, GEM_SPARK = '#1a052e', '#43196e', '#7a4cb0', '#d4c0f0'


def lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)


def nrm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def catmull(ctrl, n, closed=False):
    """a smooth curve through the control points, n points along it"""
    c = np.asarray(ctrl, float)
    if closed:
        c = np.concatenate([c[-1:], c, c[:2]])
    else:
        c = np.concatenate([2 * c[:1] - c[1:2], c, 2 * c[-1:] - c[-2:-1]])
    segs = len(c) - 3
    out = []
    for t in np.linspace(0, segs, n, endpoint=not closed):
        i = min(int(t), segs - 1)
        u = t - i
        p0, p1, p2, p3 = c[i:i + 4]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(out)


def resample(pts, step, closed=False):
    """points spaced evenly along a polyline, about step apart"""
    P = np.concatenate([pts, pts[:1]]) if closed else pts
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / step)))
    t = np.linspace(0, s[-1], n, endpoint=not closed) if closed else np.linspace(0, s[-1], n + 1)
    return np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1)


def frames(pts, closed=False, up=(0, -1, 0)):
    """tangents and a twist-free pair of normals along a curve (parallel transport; a closed curve's twist spread
    evenly round it)"""
    P = np.asarray(pts, float)
    if closed:
        T = nrm(np.roll(P, -1, 0) - np.roll(P, 1, 0))
    else:
        T = nrm(np.gradient(P, axis=0))
    up = np.asarray(up, float)
    n0 = up - T[0] * up.dot(T[0])
    if np.linalg.norm(n0) < 1e-6:
        n0 = np.cross(T[0], [0, 0, 1.0])
    N = [nrm(n0)]
    for i in range(1, len(P)):
        n = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(nrm(n))
    N = np.array(N)
    if closed:   # how far it has twisted by the time it's back round: undo that a little at each point
        n_end = N[-1] - T[0] * N[-1].dot(T[0])
        ang = math.atan2(np.dot(np.cross(nrm(n_end), N[0]), T[0]), np.dot(nrm(n_end), N[0]))
        for i in range(len(P)):
            a = ang * i / len(P)
            B = np.cross(T[i], N[i])
            N[i] = N[i] * math.cos(a) + B * math.sin(a)
    B = np.cross(T, N)
    return T, N, B


# ------------------------------------------------------------------ mesh building

class Builder:
    """faces into one bmesh, with UVs (in studs, packed later) and, on the detailed version, paint per vertex"""

    def __init__(self, name, high):
        self.name, self.high = name, high
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.flat = self.bm.faces.layers.int.new('flat')    # 1: shade flat (the gem's facets)
        self.gem = self.bm.faces.layers.int.new('gem')

    def vert(self, p):
        return self.bm.verts.new(Vector(p))

    def face(self, vs, uvs, flat=0, gem=0):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        f[self.flat] = flat
        f[self.gem] = gem
        return f

    def loft(self, C, N, B, sec, sx, sy, closed=False, cap0=False, cap1=False, uv0=(0.0, 0.0), uv_scale=1.0):
        """rings of the cross-section sec (a list of (a, b) round a loop) along the curve C, scaled by sx, sy
        along N, B at each point. A scale of 0 at an end closes it to a point; cap0 / cap1 fan a flat end shut"""
        C = np.asarray(C, float)
        m = len(sec)
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
        if closed:
            s_close = s[-1] + np.linalg.norm(C[0] - C[-1])
        per = sum(math.dist(sec[j], sec[(j + 1) % m]) for j in range(m)) * max(np.max(sx), np.max(sy))
        rings = []
        for i in range(len(C)):
            if sx[i] < 1e-7 and sy[i] < 1e-7:
                rings.append([self.vert(C[i])])
            else:
                rings.append([self.vert(C[i] + N[i] * a * sx[i] + B[i] * b * sy[i]) for a, b in sec])
        rows = list(range(len(C) - 1)) + ([len(C) - 1] if closed else [])
        for i in rows:
            i1 = (i + 1) % len(C)
            r0, r1 = rings[i], rings[i1]
            u0 = s[i] * uv_scale + uv0[0]
            u1 = (s[i1] if i1 else s_close if closed else s[i1]) * uv_scale + uv0[0]
            for j in range(m):
                v0, v1 = j / m * per * uv_scale + uv0[1], (j + 1) / m * per * uv_scale + uv0[1]
                if len(r0) == 1:
                    self.face([r0[0], r1[j], r1[(j + 1) % m]], [(u0, (v0 + v1) / 2), (u1, v0), (u1, v1)])
                elif len(r1) == 1:
                    self.face([r0[j], r1[0], r0[(j + 1) % m]], [(u0, v0), (u1, (v0 + v1) / 2), (u0, v1)])
                else:
                    self.face([r0[j], r1[j], r1[(j + 1) % m], r0[(j + 1) % m]], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        for cap, i, rev in ((cap0, 0, True), (cap1, len(C) - 1, False)):
            if cap and len(rings[i]) > 1:
                c = self.vert(C[i])
                for j in range(m):
                    a, b = rings[i][j], rings[i][(j + 1) % m]
                    uvs = [(0.5, 0.5), (0.5 + sec[j][0] * 0.1, 0.5 + sec[j][1] * 0.1),
                           (0.5 + sec[(j + 1) % m][0] * 0.1, 0.5 + sec[(j + 1) % m][1] * 0.1)]
                    if rev:
                        self.face([c, b, a], [uvs[0], uvs[2], uvs[1]])
                    else:
                        self.face([c, a, b], uvs)

    def tube(self, C, r, closed=False, around=None, up=(0, -1, 0), ends=True):
        C = np.asarray(C, float)
        T, N, B = frames(C, closed, up)
        m = around or (20 if self.high else 6)
        sec = [(math.cos(TAU * j / m), math.sin(TAU * j / m)) for j in range(m)]
        r = np.broadcast_to(np.asarray(r, float), (len(C),))
        self.loft(C, N, B, sec, r, r, closed, cap0=ends and not closed, cap1=ends and not closed)

    def ball(self, c, r, axes=None):
        """a sphere (or an ellipsoid, r a triple along the axes)"""
        r = np.broadcast_to(np.asarray(r, float), (3,))
        ax = np.eye(3) if axes is None else np.asarray(axes, float)
        nu, nv = (20, 12) if self.high else (8, 5)
        C = [np.asarray(c) + ax[2] * r[2] * -math.cos(math.pi * k / nv) for k in range(nv + 1)]
        rad = [math.sin(math.pi * k / nv) for k in range(nv + 1)]
        sec = [(math.cos(TAU * j / nu), math.sin(TAU * j / nu)) for j in range(nu)]
        N = np.tile(ax[0], (nv + 1, 1))
        Bv = np.tile(ax[1], (nv + 1, 1))
        self.loft(C, N, Bv, sec, np.array(rad) * r[0], np.array(rad) * r[1])

    def spike(self, base, d, length, w, up=(0, -1, 0), bend=None):
        """a four-edged thorn from base along d, w across at its root, drawn to a point; bend curls it"""
        d = nrm(d)
        k = 10 if self.high else 3
        C = [np.asarray(base) + d * length * t + (0 if bend is None else np.asarray(bend) * length * t * t)
             for t in np.linspace(0, 1, k + 1)]
        T, N, B = frames(np.array(C), False, up)
        if self.high:   # a diamond, its edges just rounded
            sec = []
            for j in range(16):
                a = TAU * j / 16 + math.pi / 4
                c, s = math.cos(a), math.sin(a)
                sec.append((math.copysign(abs(c) ** 1.5, c), math.copysign(abs(s) ** 1.5, s)))
        else:
            sec = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        t = np.linspace(0, 1, k + 1)
        sz = w * (1 - t) ** 1.2
        self.loft(C, N, B, sec, sz, sz * 0.8, cap0=True)

    def finish(self, smooth_angle=None):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        flat = [f[self.flat] for f in self.bm.faces]
        gem = [f[self.gem] for f in self.bm.faces]
        self.bm.free()
        for p, fl in zip(me.polygons, flat):
            p.use_smooth = not fl
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob['gem'] = gem
        return ob


TAU = math.tau


# ------------------------------------------------------------------ the chain

def box_project(p, h):
    """the point h off the torso nearest p, and the outward normal there (edges rounded by h)"""
    lo = np.array([TORSO[0][0], TORSO[1][0], TORSO[2][0]])
    hi = np.array([TORSO[0][1], TORSO[1][1], TORSO[2][1]])
    q = np.clip(p, lo, hi)
    d = p - q
    if np.linalg.norm(d) > 1e-9:
        n = d / np.linalg.norm(d)
    else:                       # inside: out through the nearest face
        dist = np.concatenate([p - lo, hi - p])
        k = int(np.argmin(dist))
        n = np.zeros(3)
        n[k % 3] = -1 if k < 3 else 1
        q = p.copy()
        q[k % 3] = lo[k % 3] if k < 3 else hi[k % 3]
    return q + n * h, n


def chain_path():
    """the chain's line on the body (h 0 off it), evenly spaced at the links' pitch from the pendant round, the
    body's outward normal along it, and how far each point is (along the chain) from the pendant"""
    half = [(0.0, -0.56, 3.33), (0.1, -0.545, 3.37), (0.26, -0.53, 3.56), (0.4, -0.52, 3.82), (0.47, -0.51, 3.985),
            (0.55, -0.33, 4.03), (0.62, 0.0, 4.03), (0.56, 0.32, 4.03), (0.42, 0.51, 3.965), (0.21, 0.53, 3.875)]
    ctrl = half + [(0.0, 0.535, 3.85)] + [(-x, y, z) for x, y, z in reversed(half[1:])]
    P = catmull(ctrl, 3000, closed=True)
    for _ in range(4):          # onto the body, then smoothed, a few times over
        P = np.array([box_project(p, 0.0)[0] for p in P])
        P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4
    seg = np.linalg.norm(np.diff(np.concatenate([P, P[:1]]), axis=0), axis=1)
    L = seg.sum()
    n = int(round(L / PITCH / 2)) * 2           # an even number, so flat and upright links alternate all round
    P = resample(P, L / n, closed=True)[:n]
    N = np.array([box_project(p + 0.002 * nrm(p - [0, 0, 3]), 0.0)[1] for p in P])
    for _ in range(6):                          # the normal turns smoothly over the torso's edges
        N = nrm(np.roll(N, 1, 0) + 2 * N + np.roll(N, -1, 0))
    k = np.arange(n)
    along = np.minimum(k, n - k) * (L / n)
    return P, N, along, L / n


def link_template(high):
    """one link's wire: its centreline round the stadium (in its own plane: x along the chain, y across), the
    outward direction in the plane at each point, and the arc length"""
    m = 56 if high else 12
    per = 4 * LINK_H + TAU * LINK_R
    out = []
    for s in np.linspace(0, per, m, endpoint=False):
        if s < 2 * LINK_H:                                       # the near side, left to right
            c, o = (-LINK_H + s, -LINK_R), (0, -1)
        elif s < 2 * LINK_H + math.pi * LINK_R:                  # round the right end
            a = -math.pi / 2 + (s - 2 * LINK_H) / LINK_R
            c, o = (LINK_H + LINK_R * math.cos(a), LINK_R * math.sin(a)), (math.cos(a), math.sin(a))
        elif s < 4 * LINK_H + math.pi * LINK_R:                  # the far side, back
            c, o = (LINK_H - (s - 2 * LINK_H - math.pi * LINK_R), LINK_R), (0, 1)
        else:                                                    # round the left end
            a = math.pi / 2 + (s - 4 * LINK_H - math.pi * LINK_R) / LINK_R
            c, o = (-LINK_H + LINK_R * math.cos(a), LINK_R * math.sin(a)), (math.cos(a), math.sin(a))
        out.append((c, o, s / per))
    return out


def chain(high):
    """every link round the chain: alternately lying flat on the body and standing up off it; near the pendant
    they lift off the chest with it. Each link's UVs are the same, so they share one patch of texture"""
    P, N, along, step = chain_path()
    bd = Builder('High_Chain' if high else 'Pendant_Chain', high)
    tpl = link_template(high)
    around = 16 if high else 5
    T = nrm(np.roll(P, -1, 0) - np.roll(P, 1, 0))
    centres = []
    for i in range(len(P)):
        t = T[i]
        n = nrm(N[i] - t * N[i].dot(t))
        b = np.cross(t, n)
        flat = i % 2 == 0
        lift = LIFT * math.exp(-(along[i] / 0.13) ** 2)
        h = max(WIRE + 0.004 if flat else LINK_R + WIRE + 0.004, lift)
        c = P[i] + N[i] * h
        if i == 0:
            c = np.array([0.0, TORSO[1][0] - LIFT, P[0][2]])     # the link through the bail
        centres.append(c)
        across, off = (b, n) if flat else (n, b)                 # in the link's plane, and out of it
        rings = []
        for (cx, cy), (ox, oy), _ in tpl:
            o = t * ox + across * oy
            cc = c + t * cx + across * cy
            rings.append([bd.vert(cc + WIRE * (math.cos(TAU * j / around) * o + math.sin(TAU * j / around) * off))
                          for j in range(around)])
        m = len(tpl)
        for a in range(m):
            for j in range(around):
                a1, j1 = (a + 1) % m, (j + 1) % around
                u0, u1 = a / m, (a + 1) / m
                v0, v1 = j / around, (j + 1) / around
                bd.face([rings[a][j], rings[a1][j], rings[a1][j1], rings[a][j1]],
                        [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    return bd, np.array(centres)


# ------------------------------------------------------------------ the pendant (its own frame: x across, z up,
#                                                                    -y out from the chest; 0 at the bail's eye)

GEM_TOP, GEM_H, GEM_HW = -0.27, 0.31, 0.105
A_PEAR = GEM_HW / 0.7698


def pear(t):
    """the gem's outline, t 0 at its point (top) round its right side to pi at its bottom, on to 2 pi"""
    t = np.asarray(t, float)
    s = np.where(t <= math.pi, 1.0, -1.0)
    tt = np.where(t <= math.pi, t, TAU - t)
    x = s * A_PEAR * np.sin(tt) * np.sin(tt / 2)
    z = GEM_TOP - GEM_H * (1 - np.cos(tt)) / 2
    return np.stack([x, np.zeros_like(x), z], -1)


def outline(n, off=0.0):
    """the outline offset outward by off, closed, n points; and the outward normals"""
    t = np.linspace(0, TAU, n, endpoint=False)
    P = pear(t)
    T = nrm(np.roll(P, -1, 0) - np.roll(P, 1, 0))
    Nout = np.stack([T[:, 2], np.zeros(n), -T[:, 0]], -1)       # the tangent turned outward in the x-z plane
    c = P.mean(0)
    flip = np.sum((P - c) * Nout, axis=1) < 0
    Nout[flip] *= -1
    return P + Nout * off, Nout, t


def at(t, off):
    """a point of the offset outline at parameter t, and its outward normal there"""
    P, Nout, ts = outline(720, off)
    i = int(round((t % TAU) / TAU * 720)) % 720
    return P[i], Nout[i]


def gem(bd):
    """a pear brilliant: its crown (a table and a ring of triangular facets) toward the viewer, the pavilion
    behind. Each facet its own flat face, painted on its own"""
    n = 24
    t = np.linspace(0, TAU, n, endpoint=False)
    G = pear(t)
    c = np.array([0, 0, GEM_TOP - GEM_H * 0.62])
    Th = pear(t + math.pi / n)
    Tb = c + (Th - c) * 0.56 + np.array([0, -0.045, 0])                # the table's corners, set back half a step
    Gf = G + np.array([0, -0.004, 0])                                  # the girdle, front and back
    Gb = G + np.array([0, 0.004, 0])
    Pv = c + (G - c) * 0.42 + np.array([0, 0.036, 0])
    cul = c + np.array([0, 0.05, 0])
    top = c + np.array([0, -0.047, 0])
    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris += [(Gf[i], Gf[j], Tb[i]), (Tb[i - 1], Gf[i], Tb[i]),          # bezel and upper-girdle facets
                 (Tb[i], top, Tb[i - 1]),                                   # the table
                 (Gf[j], Gf[i], Gb[i]), (Gb[i], Gb[j], Gf[j]),               # the girdle's band
                 (Gb[j], Gb[i], Pv[i]), (Pv[i], Pv[j], Gb[j]),               # the pavilion
                 (Pv[j], Pv[i], cul)]
    out = []
    for k, tri in enumerate(tris):
        a, b, cc = (np.asarray(p, float) for p in tri)
        nn = nrm(np.cross(b - a, cc - a))
        if np.dot(nn, (a + b + cc) / 3 - c) < 0:
            b, cc = cc, b
            nn = -nn
        e1 = nrm(b - a)
        e2 = np.cross(nn, e1)
        uvs = [((p - a).dot(e1), (p - a).dot(e2)) for p in (a, b, cc)]
        f = bd.face([bd.vert(a), bd.vert(b), bd.vert(cc)], uvs, flat=1, gem=1)
        out.append((f, nn, k))
    return out


def charm(high):
    """the bail and its leaf, the ring, the cap, the bezel and its claws, the cage of thorns round it, the
    scrolls between, and the gem"""
    bd = Builder('High_Charm' if high else 'Pendant_Charm', high)
    fine = 360 if high else 64
    # the bail: an eye the chain runs through, and a leaf hanging from it with curls either side
    a = np.linspace(0, TAU, 72 if high else 14, endpoint=False)
    bd.tube(np.stack([np.zeros_like(a), 0.048 * np.cos(a), 0.048 * np.sin(a)], 1), 0.011, closed=True,
            up=(1, 0, 0))
    zs = np.array([-0.032, -0.045, -0.065, -0.09, -0.115, -0.138, -0.155, -0.165])
    wd = np.array([0.0, 0.022, 0.048, 0.062, 0.05, 0.03, 0.018, 0.0])
    dp = np.array([0.0, 0.018, 0.028, 0.032, 0.028, 0.022, 0.017, 0.0])
    k = 6 if high else 2
    zz = np.interp(np.linspace(0, len(zs) - 1, (len(zs) - 1) * k + 1), np.arange(len(zs)), zs)
    ww = np.interp(zz[::-1], zs[::-1], wd[::-1])[::-1]
    dd = np.interp(zz[::-1], zs[::-1], dp[::-1])[::-1]
    C = np.stack([np.zeros_like(zz), np.zeros_like(zz), zz], 1)
    m = 24 if high else 6
    sec = []
    for j in range(m):                                  # a lens, ridged down its middle: pointed at its sides
        q = TAU * j / m
        c, s = math.cos(q), math.sin(q)
        sec.append((math.copysign(abs(c) ** 1.6, c), math.copysign(abs(s) ** 1.25, s)))
    bd.loft(C, np.tile([1.0, 0, 0], (len(C), 1)), np.tile([0, -1.0, 0], (len(C), 1)), sec, ww / 2, dd / 2)
    for sd in (-1, 1):
        q = np.linspace(0, 1.55 * math.pi, 40 if high else 8)
        rr = 0.024 * (1 - 0.55 * q / q[-1])
        curl = np.stack([sd * (0.012 + rr * np.sin(q)), np.full_like(q, -0.006), -0.075 - 0.02 * q / q[-1]
                         - rr * (1 - np.cos(q)) * 0.9], 1)
        bd.tube(curl, np.linspace(0.0065, 0.0035, len(q)))
    bd.ball((0, 0, -0.17), 0.016)
    a = np.linspace(0, TAU, 48 if high else 12, endpoint=False)
    bd.tube(np.stack([0.02 * np.cos(a), np.zeros_like(a), -0.198 + 0.02 * np.sin(a)], 1), 0.0065, closed=True,
            up=(0, -1, 0))
    # the cap over the gem's point, a little thorn either side of it
    zc = np.linspace(-0.214, -0.282, 10 if high else 4)
    rc = np.interp(-zc, [0.214, 0.224, 0.245, 0.268, 0.282], [0.0, 0.016, 0.022, 0.026, 0.008])
    Cc = np.stack([np.zeros_like(zc), np.zeros_like(zc) - 0.004, zc], 1)
    sec = [(math.cos(TAU * j / (20 if high else 6)), math.sin(TAU * j / (20 if high else 6)))
           for j in range(20 if high else 6)]
    bd.loft(Cc, np.tile([1.0, 0, 0], (len(zc), 1)), np.tile([0, -1.0, 0], (len(zc), 1)), sec, rc, rc * 0.8,
            cap1=True)
    for sd in (-1, 1):
        bd.spike((sd * 0.02, -0.004, -0.262), (sd * 1.0, 0, 0.7), 0.042, 0.009, bend=(0, 0, 0.3))
    # the bezel round the gem, and its six claws over the gem's edge
    P, Nout, _ = outline(fine, 0.008)
    bd.tube(P, 0.011, closed=True, up=(0, -1, 0))
    for t in (0.55, 1.6, 2.65, TAU - 0.55, TAU - 1.6, TAU - 2.65):
        p, n = at(t, 0.0)
        bd.ball(p - n * 0.004 + np.array([0, -0.022, 0]), (0.01, 0.015, 0.009),
                axes=[nrm(np.cross(n, [0, -1, 0])), n, [0, -1, 0]])
    # the cage: a second frame further out, thorns standing off it, bars and scrolls tying it to the bezel
    OFF = 0.04
    P, Nout, _ = outline(fine, OFF)
    order = np.nonzero(P[:, 2] < GEM_TOP - 0.012)[0]   # it stops short of the cap: from its right side round
    bd.tube(P[order], 0.0085, up=(0, -1, 0))
    for sd in (-1, 1):                                  # its ends curl in onto the cap
        e = P[order[0] if sd > 0 else order[-1]]
        bd.tube(catmull([e, e + (np.array([0, 0, -0.268]) - e) * 0.5 + np.array([0, 0, 0.012]),
                         np.array([sd * 0.012, -0.004, -0.262])], 12 if high else 4), 0.0075)
    for t, length, w, barbs in ((math.pi, 0.07, 0.026, True), (1.91, 0.052, 0.023, True), (0.62, 0.036, 0.017, False)):
        for tt in ((t,) if t == math.pi else (t, TAU - t)):
            p, n = at(tt, OFF)
            q, _ = at(tt, 0.019)
            bd.tube(np.array([q, p]), 0.0075, around=12 if high else 5)        # the bar out to it
            bd.ball(p, 0.016)
            bd.spike(p + n * 0.01, n, length, w)
            if barbs:
                side = nrm(np.cross(n, [0, -1, 0]))
                for sg in (-1, 1):
                    bd.spike(p + n * 0.006 + side * sg * 0.01, nrm(n * 0.35 + side * sg), 0.03, 0.012,
                             bend=n * 0.8)
    for t0, t1 in ((1.05, 1.42), (2.3, 2.75)):           # scrolls between the bezel and the cage
        for mirror in (False, True):
            ta, tb = (t0, t1) if not mirror else (TAU - t0, TAU - t1)
            pa, na = at(ta, 0.02)
            pb, nb = at(tb, OFF - 0.008)
            mid = (pa + pb) / 2
            q = np.linspace(0, 1, 40 if high else 8)
            pts = [pa + (pb - pa) * s + (na + nb) / 2 * 0.012 * math.sin(TAU * s) for s in q]
            bd.tube(np.array(pts), 0.0055)
            bd.ball(mid + (na + nb) / 2 * 0.004, 0.009)
    if high:   # beads of granulation along the cage, and a bead between each of the bezel's claws
        P, Nout, ts = outline(720, OFF)
        for i in range(0, 720, 9):
            if P[i, 2] < GEM_TOP - 0.03:
                bd.ball(P[i] + np.array([0, -0.0075, 0]), 0.0042)
    facets = gem(bd)
    return bd, facets


# ------------------------------------------------------------------ paint (the detailed meshes)

def occlusion(ob, rays=16, reach=0.018):
    """how open each vertex is (0 shut in, 1 open): rays out over its hemisphere, against the mesh itself"""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    rng = np.random.default_rng(3)
    dirs = nrm(rng.standard_normal((rays, 3)))
    out = np.ones(len(me.vertices))
    for k, v in enumerate(me.vertices):
        n = np.array(v.normal)
        p = np.array(v.co) + n * 0.0015
        hit = 0
        tot = 0
        for d in dirs:
            if d.dot(n) < 0:
                d = -d
            tot += 1
            if tree.ray_cast(Vector(p), Vector(d), reach)[0] is not None:
                hit += 1
        out[k] = 1 - hit / max(tot, 1)
    return out


def set_paint(ob, col, rough, metal):
    me = ob.data
    for name, kind, data, key in (('Col', 'FLOAT_COLOR', np.c_[col, np.ones(len(col))].ravel(), 'color'),
                                  ('Rough', 'FLOAT', rough, 'value'), ('Metal', 'FLOAT', metal, 'value')):
        a = me.attributes.new(name, kind, 'POINT')
        a.data.foreach_set(key, np.asarray(data, np.float32))


def paint_chain(ob):
    """each link alike: silver, oxidised where the wire faces into the link's eye and where it meets its
    neighbours, bright along its crown"""
    me = ob.data
    V = np.array([v.co for v in me.vertices])
    Nv = np.array([v.normal for v in me.vertices])
    tpl = link_template(True)
    per_link = len(tpl) * 16
    col, rough = np.zeros((len(V), 3)), np.zeros(len(V))
    base = []
    for (cx, cy), (ox, oy), _ in tpl:        # the template's own shading: in the link's frame
        for j in range(16):
            a = TAU * j / 16
            inward = -math.cos(a)                       # 1 facing into the eye
            crown = abs(math.sin(a))                    # 1 on the link's faces
            ends = max(0.0, abs(cx) - LINK_H) / LINK_R  # 1 round the ends, where the neighbours wear in
            shade = np.clip(0.9 - 0.55 * max(inward, 0) - 0.35 * ends * max(inward + 0.3, 0) + 0.25 * crown ** 3, 0, 1)
            base.append(shade)
    base = np.array(base)
    for k in range(len(V) // per_link):
        s = base
        c = lin(OXIDE)[None] * (1 - s[:, None]) + lin(SILVER)[None] * s[:, None]
        c = c + (lin(HIGHLIGHT) - c) * np.clip((s - 0.95) * 8, 0, 1)[:, None]
        col[k * per_link:(k + 1) * per_link] = c
        rough[k * per_link:(k + 1) * per_link] = 0.28 + 0.35 * (1 - s)
    set_paint(ob, col, rough, np.ones(len(V)))


def paint_charm(ob, facets_n):
    """silver, oxidised in the recesses and lit from above and in front so it reads at a glance; the gem's facets
    each their own shade of violet, a few catching the light"""
    me = ob.data
    V = np.array([v.co for v in me.vertices])
    Nv = np.array([v.normal for v in me.vertices])
    ao = occlusion(ob)
    L = nrm([-0.35, -1.0, 0.65])
    lit = np.clip(Nv @ L, 0, 1)
    s = np.clip(ao * (0.72 + 0.45 * lit), 0, 1)
    col = lin(OXIDE)[None] * (1 - s[:, None]) + lin(SILVER)[None] * s[:, None]
    col = col + (lin(HIGHLIGHT) - col) * np.clip((lit - 0.72) * 3.5 * ao, 0, 1)[:, None]
    rough = 0.3 + 0.35 * (1 - ao)
    metal = np.ones(len(V))
    gem_faces = ob['gem']
    rng = np.random.default_rng(8)
    for p, g in zip(me.polygons, gem_faces):
        if not g:
            continue
        n = np.array(p.normal)
        front = max(0.0, -n[1])
        k = np.clip(0.15 + 0.7 * max(0.0, n @ L) + rng.normal(0, 0.18), 0, 1)
        c = lin(GEM_DARK) + (lin(GEM_MID) - lin(GEM_DARK)) * min(k * 1.6, 1)
        c = c + (lin(GEM_LIGHT) - c) * max(0.0, k - 0.62) * 2.2
        if rng.random() < 0.12 and front > 0.3:
            c = c + (lin(GEM_SPARK) - c) * 0.75
        if abs(n[1]) > 0.97 and n[1] < 0:            # the table: a soft window into the stone
            c = lin(GEM_MID)
        for vi in p.vertices:
            col[vi] = c
            rough[vi] = 0.06
            metal[vi] = 0.0
    set_paint(ob, col, rough, metal)


# ------------------------------------------------------------------ bake, materials

def pack(ob, merge=False):
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=True, scale=True, merge_overlap=merge, margin_method='FRACTION', margin=0.008)
        bpy.ops.object.mode_set(mode='OBJECT')
        ob.select_set(False)


def bake(lo, hi, res, cage, reach):
    """the detailed mesh onto the game mesh: its normals, and its paint (colour, roughness, metalness) through an
    emission pass"""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    bk = sc.render.bake
    bk.margin = 8
    bk.use_clear = True
    bk.use_selected_to_active = True
    bk.cage_extrusion = cage
    bk.max_ray_distance = reach
    pm = bpy.data.materials.new(hi.name + '_Paint')
    pm.use_nodes = True
    nt = pm.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    src = {}
    for ch, attr, sock in (('Color', 'Col', 'Color'), ('Roughness', 'Rough', 'Fac'), ('Metalness', 'Metal', 'Fac')):
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = attr
        src[ch] = at.outputs[sock]
    hi.data.materials.clear()
    hi.data.materials.append(pm)
    tm = bpy.data.materials.new(lo.name + '_Target')
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
    os.makedirs(OUT, exist_ok=True)
    for ch in ('Color', 'Roughness', 'Metalness', 'Normal'):
        img = bpy.data.images.new(f'{lo.name}_{ch}', res, res, alpha=False)
        img.colorspace_settings.name = 'sRGB' if ch == 'Color' else 'Non-Color'
        tnode.image = img
        if ch == 'Normal':
            sc.cycles.samples = 16
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=8, use_selected_to_active=True)
        else:
            nt.links.new(src[ch], em.inputs['Color'])
            sc.cycles.samples = 16
            bpy.ops.object.bake(type='EMIT', margin=8, use_selected_to_active=True)
        img.filepath_raw = os.path.join(OUT, f'{lo.name}_{ch}.png')
        img.file_format = 'PNG'
        img.save()
        maps[ch] = img
        print('BAKED', img.name, flush=True)
    hi.select_set(False)
    lo.select_set(False)
    return maps


def baked_material(ob, maps):
    m = bpy.data.materials.new(ob.name + '_Baked')
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
    nt.links.new(tex['Metalness'].outputs[0], b.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], b.inputs['Normal'])
    ob.data.materials.clear()
    ob.data.materials.append(m)


def paint_material(ob):
    """the detailed mesh shown with its own paint, for quick looks"""
    m = bpy.data.materials.new(ob.name + '_Live')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    for attr, sock, out in (('Col', 'Base Color', 'Color'), ('Rough', 'Roughness', 'Fac'), ('Metal', 'Metallic', 'Fac')):
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = attr
        nt.links.new(at.outputs[out], b.inputs[sock])
    ob.data.materials.clear()
    ob.data.materials.append(m)


# ------------------------------------------------------------------ shots and export

def shots(path, label):
    """the necklace on the R6 body: the chest close up from the front and three-quarter, and the upper body"""
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = 48
    sc.render.resolution_x, sc.render.resolution_y = 560, 640
    files = []
    for i, (az, el, dist, tgt, lens) in enumerate(((0, 6, 9, (0, 0, 3.4), 85), (-35, 14, 9, (0, 0, 3.45), 85),
                                                    (-25, 22, 16, (0, 0, 3.6), 85))):
        a, e = math.radians(az - 90), math.radians(el)
        cam_d.lens = lens
        cam.location = Vector(tgt) + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist
        cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        f = path.replace('.png', f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        files.append(f)
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f).convert('RGB') for f in files]
    ref = Image.open(os.path.join(HERE, 'reference.png')).convert('RGB')
    ref = ref.resize((round(ref.width * 640 / ref.height), 640), Image.LANCZOS)
    W = sum(im.width for im in ims) + ref.width
    out = Image.new('RGB', (W, 640 + 40), (34, 34, 38))
    x = 0
    for im in [ref] + ims:
        out.paste(im, (x, 40))
        x += im.width
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    ImageDraw.Draw(out).text((12, 10), label, fill=(235, 235, 235), font=font)
    out.save(path)
    for f in files:
        os.remove(f)
    print('SHOT', path, flush=True)


def export(objs, refs):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs + [refs['Torso']]:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'Pendant.fbx'), use_selection=True, object_types={'MESH'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True,
                             path_mode='STRIP')
    print('EXPORTED', os.path.join(OUT, 'Pendant.fbx'), flush=True)


def build(high):
    bc, centres = chain(high)
    ch = bc.finish()
    bp, _ = charm(high)
    cm = bp.finish()
    cm.location = Vector(centres[0])            # the pendant hangs from the link through its bail
    cm.scale = (CHARM_SCALE,) * 3
    with bpy.context.temp_override(object=cm, active_object=cm, selected_objects=[cm], selected_editable_objects=[cm]):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    return ch, cm


def main():
    A.reset()
    os.makedirs(OUT, exist_ok=True)
    refs = A.load_rig()
    hc, hm = build(True)
    paint_chain(hc)
    paint_charm(hm, None)
    for o in (hc, hm):
        print(o.name, 'tris', len(o.data.polygons), flush=True)
    if STAGE == 'preview':
        paint_material(hc)
        paint_material(hm)
        shots(os.path.join(OUT, 'preview_detail.png'), 'the detailed pendant and chain, with their paint')
        return
    lc, lm = build(False)
    pack(lc, merge=True)          # the links' patches, all alike, stacked as one
    pack(lm)
    for o in (lc, lm):
        print(o.name, 'tris', len(o.data.polygons), flush=True)
    maps_c = bake(lc, hc, 512, cage=0.006, reach=0.015)
    maps_m = bake(lm, hm, 1024, cage=0.006, reach=0.015)
    for o in (hc, hm):
        bpy.data.objects.remove(o)
    baked_material(lc, maps_c)
    baked_material(lm, maps_m)
    tris = sum(len(o.data.polygons) for o in (lc, lm))
    export([lc, lm], refs)
    shots(os.path.join(OUT, 'preview.png'), f'the game meshes with their baked maps ({tris} triangles), beside the '
          'reference')


if __name__ == '__main__':
    main()
