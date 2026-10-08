"""Species eggs (static meshes, no rig). One egg per species (Forest and Frost Peaks), themed after its monster.
    blender -b --factory-startup --python eggs.py -- <out_dir> <Species> [--live]
Exports <Species>Egg.fbx / .blend. Egg is 3 units tall standing on Z = 0; the game scales it.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Vector
from kit import Monster

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
SPECIES = args[1] if len(args) > 1 else 'Thornhorn'

H, R = 3.0, 1.15   # egg height and widest radius


def shell_radius(t):
    """radius of the egg at normalised height t in [-1, 1] (narrower at the top)"""
    return R * math.sqrt(max(0.0, 1 - t * t)) * (1 - 0.2 * max(t, 0.0))


def surf(a, t, out=0.0):
    """point on the egg surface at azimuth a (radians) and height t, pushed out along the normal"""
    r = shell_radius(t)
    p = Vector((r * math.cos(a), r * math.sin(a), H / 2 + t * H / 2))
    n = normal(a, t)
    return tuple(p + n * out)


def normal(a, t):
    eps = 0.01
    p0 = Vector((shell_radius(t) * math.cos(a), shell_radius(t) * math.sin(a), t * H / 2))
    pu = Vector((shell_radius(t + eps) * math.cos(a), shell_radius(t + eps) * math.sin(a), (t + eps) * H / 2))
    pa = Vector((shell_radius(t) * math.cos(a + eps), shell_radius(t) * math.sin(a + eps), t * H / 2))
    n = (pa - p0).cross(pu - p0)
    if n.length < 1e-6:
        return Vector((0, 0, 1 if t > 0 else -1))
    n.normalize()
    return n if n.dot(Vector((math.cos(a), math.sin(a), t))) > 0 else -n


def rot_to(n):
    """Euler (degrees) that turns +Z onto n, for blobs that should lie flat on the shell"""
    e = Vector(n).to_track_quat('Z', 'Y').to_euler()
    return tuple(math.degrees(x) for x in e)


def add_shell(m, color):
    def build(bm):
        res = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=1.0)
        for v in res['verts']:
            t = max(-1.0, min(1.0, v.co.z))
            r = shell_radius(t) / R
            k = math.hypot(v.co.x, v.co.y)
            sx = (v.co.x / k * r * R) if k > 1e-6 else 0.0
            sy = (v.co.y / k * r * R) if k > 1e-6 else 0.0
            v.co = Vector((sx, sy, H / 2 + t * H / 2))
    m.parts.append(('Root', color, build, 0.0, 0, False))


def patch(m, color, a, t, size, flat=0.12, out=0.0):
    n = normal(a, t)
    m.blob('Root', color, surf(a, t, out), (size, size, flat), rot=rot_to(n), u=8, v=5)


def leaf(m, color, a, t0, t1, width, out=0.05):
    """a leaf lying on the shell from height t0 up to t1, centred on azimuth a"""
    lead, trail = [], []
    n = 8
    for i in range(n):
        f = i / (n - 1)
        t = t0 + (t1 - t0) * f
        w = width * math.sin(math.pi * min(1.0, 0.15 + f * 0.95))
        lead.append(surf(a - w / 2, t, out))
        trail.append(surf(a + w / 2, t, out))
    m.strip('Root', color, lead, trail, thickness=0.06)


def zigzag(m, color, t_center, amp, width, teeth=8, out=0.03):
    """a decorated-egg zigzag band right round the shell"""
    lead, trail = [], []
    n = teeth * 2
    for i in range(n + 1):
        a = i / n * math.tau
        tz = t_center + (amp if i % 2 else -amp)
        lead.append(surf(a, tz + width / 2, out))
        trail.append(surf(a, tz - width / 2, out))
    m.strip('Root', color, lead, trail, thickness=0.05)


def thornhorn(m):
    m.color('shell', '#5aa04e'); m.color('plate', '#e2782f'); m.color('plate2', '#f3b640')
    m.color('horn', '#f6f3ea', dots=False)
    add_shell(m, 'shell')
    for i in range(6):
        a = i * math.tau / 6
        patch(m, 'plate', a + math.tau / 12, 0.32, 0.26, 0.09)
    zigzag(m, 'plate', -0.12, 0.14, 0.13)
    zigzag(m, 'plate2', -0.12, 0.14, 0.05, out=0.05)
    for i in range(5):
        a = i * math.tau / 5 + 0.3
        m.spike('Root', 'horn', surf(a, 0.6), tuple(normal(a, 0.6)), 0.55, 0.24)
    m.spike('Root', 'horn', surf(0, 0.98), (0, 0, 1), 0.5, 0.24)


def bristleboar(m):
    m.color('shell', '#8a5a3c'); m.color('spot', '#d9b48a'); m.color('leaf', '#4f9a3e'); m.color('leaf2', '#7cc95a')
    add_shell(m, 'shell')
    for a, t, s in ((0.3, 0.35, 0.22), (1.5, -0.5, 0.25), (2.6, 0.4, 0.2), (3.7, -0.55, 0.24),
                    (4.8, 0.3, 0.2), (5.6, -0.5, 0.22)):
        patch(m, 'spot', a, t, s, 0.1)
    zigzag(m, 'spot', -0.05, 0.12, 0.16, teeth=7)
    for i in range(6):
        a = i * math.tau / 6
        d = normal(a, 0.75) + Vector((0, 0, 1.2))
        m.spike('Root', 'leaf' if i % 2 else 'leaf2', surf(a, 0.75), tuple(d.normalized()), 0.75, 0.12, 0.45)
    m.spike('Root', 'leaf2', surf(0, 0.98), (0, 0, 1), 0.85, 0.12, 0.5)


def leafclaw(m):
    m.color('shell', '#b6e07a'); m.color('speck', '#3e9a3a'); m.color('leaf', '#3e9a3a'); m.color('leaf2', '#5fae4a')
    m.color('claw', '#f3efe2', dots=False)
    add_shell(m, 'shell')
    for i in range(14):
        a = i * 2.39996
        t = -0.6 + (i % 7) * 0.22
        patch(m, 'speck', a, t, 0.1 + 0.04 * (i % 3), 0.06)
    zigzag(m, 'speck', 0.4, 0.1, 0.1, teeth=9)
    for i in range(3):
        leaf(m, 'leaf' if i % 2 == 0 else 'leaf2', i * math.tau / 3, -0.98, 0.3, 1.5, out=0.09)
    m.spike('Root', 'claw', surf(1.0, 0.35), tuple((normal(1.0, 0.35) + Vector((0, 0, 0.8))).normalized()), 0.5, 0.16)


def mosshell(m):
    m.color('shell', '#86a35e'); m.color('moss', '#4f9a3e'); m.color('cap', '#e0503c', dots=False)
    m.color('spot', '#fff6e6', dots=False); m.color('stem', '#efe6cf', dots=False); m.color('rim', '#8b6a42')
    add_shell(m, 'shell')
    for i in range(8):
        patch(m, 'rim', i * math.tau / 8, -0.35, 0.3, 0.08)
    for a, t, s in ((0, 0.7, 0.5), (2.0, 0.55, 0.45), (4.0, 0.6, 0.45), (1.0, 0.3, 0.32), (3.2, 0.25, 0.3), (5.2, 0.35, 0.3)):
        patch(m, 'moss', a, t, s, 0.14, out=0.02)
    for a, t, k in ((0.8, 0.82, 1.0), (3.6, 0.7, 0.75)):
        base = Vector(surf(a, t))
        n = normal(a, t) + Vector((0, 0, 1.5))
        n.normalize()
        m.box('Root', 'stem', tuple(base + n * 0.22 * k), (0.16 * k, 0.16 * k, 0.45 * k), bevel=0.03)
        cap = base + n * 0.5 * k
        m.blob('Root', 'cap', tuple(cap), (0.32 * k, 0.32 * k, 0.18 * k), u=8, v=5)
        for j in range(3):
            aa = j * math.tau / 3
            m.blob('Root', 'spot', tuple(cap + Vector((math.cos(aa) * 0.18 * k, math.sin(aa) * 0.18 * k, 0.12 * k))),
                   (0.06 * k, 0.06 * k, 0.04 * k), u=6, v=4)


def glowcap(m):
    m.color('shell', '#4e3a62'); m.color('glow', '#58f0e0', dots=False); m.color('glow2', '#c8fff6', dots=False)
    m.color('antler', '#e9dcc4', dots=False)
    add_shell(m, 'shell')
    for i in range(11):
        a = i * 2.39996
        t = -0.7 + (i % 6) * 0.26
        patch(m, 'glow', a, t, 0.12 + 0.05 * (i % 3), 0.06, out=0.01)
    # a little glowcap sprouting from the top, like a mini antler
    for s in (-1, 1):
        d = Vector((0.45 * s, 0.1, 1.0)).normalized()
        base = Vector(surf(0, 0.96))
        m.spike('Root', 'antler', tuple(base), tuple(d), 0.7, 0.14, snap=False)
        tip = base + d * 0.7
        m.blob('Root', 'glow', tuple(tip), (0.22, 0.22, 0.14), u=8, v=5)
        m.blob('Root', 'glow2', tuple(tip + Vector((0, 0, 0.08))), (0.12, 0.12, 0.07), u=6, v=4)


def sylvandrake(m):
    m.color('shell', '#2f7d55'); m.color('scale', '#3f9a68'); m.color('gold', '#ffcf3a', dots=False)
    m.color('crystal', '#6dffb0', dots=False); m.color('leaf', '#7cc95a')
    add_shell(m, 'shell')
    for i in range(16):
        a = i * math.tau / 8 + (0.39 if (i // 8) % 2 else 0)
        t = -0.5 if i < 8 else 0.25
        patch(m, 'scale', a, t, 0.28, 0.07)
    zigzag(m, 'gold', -0.08, 0.13, 0.12, teeth=10)
    for a, t, l in ((0, 0.92, 1.25), (1.2, 0.6, 0.9), (2.6, 0.7, 0.8), (4.3, 0.55, 0.95), (5.4, 0.25, 0.7), (3.4, -0.3, 0.6),
                    (0.6, 0.75, 0.6)):
        d = normal(a, t) + Vector((0, 0, 0.6))
        m.spike('Root', 'crystal', surf(a, t), tuple(d.normalized()), l, 0.32 * l / 0.7 + 0.08, twist=45)
    for i in range(2):
        leaf(m, 'leaf', math.pi / 2 + i * math.pi, -0.95, -0.1, 0.9)


BUILDERS = {'Thornhorn': thornhorn, 'Bristleboar': bristleboar, 'Leafclaw': leafclaw, 'Mosshell': mosshell,
            'GlowcapStag': glowcap, 'SylvanDrake': sylvandrake}


# ------------------------------------------------------------------ Frost Peaks eggs

def snowhare(m):
    m.color('shell', '#f3f7fd'); m.color('speck', '#f4b2c6'); m.color('ear', '#e6eef9'); m.color('pink', '#f4b2c6')
    m.color('ice', '#9feaff', dots=False)
    add_shell(m, 'shell')
    for i in range(12):
        a = i * 2.39996
        t = -0.65 + (i % 6) * 0.22
        patch(m, 'speck', a, t, 0.09 + 0.03 * (i % 3), 0.05)
    zigzag(m, 'pink', -0.25, 0.1, 0.08, teeth=10)
    for s in (-1, 1):   # two little bunny ears with ice tips
        a = math.pi / 2 + s * 0.45
        base = Vector(surf(a, 0.82))
        d = (normal(a, 0.82) + Vector((0, 0, 1.6))).normalized()
        m.box('Root', 'ear', tuple(base + d * 0.4), (0.26, 0.12, 0.8), rot=(0, 25 * s, 0), bevel=0.08)
        m.spike('Root', 'ice', tuple(base + d * 0.8), tuple(d), 0.35, 0.16, twist=45, snap=False)


def frostpenguin(m):
    m.color('shell', '#2b3348'); m.color('belly', '#f7f9ff'); m.color('beak', '#ff9a2e'); m.color('scarf', '#e2413f')
    m.color('scarf2', '#ffffff'); m.color('ice', '#a6efff', dots=False)
    add_shell(m, 'shell')
    # white front belly patch
    for a, t, s in ((-math.pi / 2, -0.35, 0.75), (-math.pi / 2 + 0.6, -0.5, 0.5), (-math.pi / 2 - 0.6, -0.5, 0.5),
                    (-math.pi / 2, 0.05, 0.55)):
        patch(m, 'belly', a, t, s, 0.1, out=0.01)
    zigzag(m, 'scarf', 0.38, 0.05, 0.16, teeth=12)
    zigzag(m, 'scarf2', 0.38, 0.05, 0.05, teeth=12, out=0.05)
    m.spike('Root', 'beak', surf(-math.pi / 2, 0.55), tuple((normal(-math.pi / 2, 0.55) - Vector((0, 0, 0.3))).normalized()), 0.35, 0.22, snap=False)
    for x in (-0.18, 0.0, 0.18):
        m.spike('Root', 'ice', surf(0, 0.98), (x * 2, 0.2, 1), 0.4 if x == 0 else 0.3, 0.16, twist=45, snap=False)


def tuskwalrus(m):
    m.color('shell', '#a9786a'); m.color('spot', '#c9a092'); m.color('whisker', '#5a3a32'); m.color('tusk', '#e2fbff', dots=False)
    m.color('snow', '#f4f8ff')
    add_shell(m, 'shell')
    for a, t, s in ((0.4, 0.3, 0.24), (1.6, -0.45, 0.28), (2.8, 0.35, 0.22), (3.9, -0.5, 0.26), (5.0, 0.2, 0.24)):
        patch(m, 'spot', a, t, s, 0.08)
    for i in range(8):
        patch(m, 'whisker', -math.pi / 2 + (i % 4 - 1.5) * 0.18, 0.05 - 0.12 * (i // 4), 0.05, 0.04, out=0.02)
    for s in (-1, 1):
        a = -math.pi / 2 + 0.3 * s
        m.spike('Root', 'tusk', surf(a, -0.05), tuple((normal(a, -0.05) * 0.4 + Vector((0, 0, -1))).normalized()), 0.75, 0.2, twist=45, snap=False)
    patch(m, 'snow', 0.0, 0.92, 0.55, 0.12, out=0.02)


def snowyowl(m):
    m.color('shell', '#f6f8fc'); m.color('bar', '#7d8594'); m.color('feather', '#eef2f8'); m.color('eye', '#ffcf3a')
    m.color('ice', '#a6efff', dots=False)
    add_shell(m, 'shell')
    for i in range(16):
        a = i * 2.39996
        t = -0.7 + (i % 8) * 0.18
        patch(m, 'bar', a, t, 0.1, 0.04, out=0.01)
    for i in range(3):
        leaf(m, 'feather', math.pi / 2 + (i - 1) * 0.9, -0.95, 0.15, 0.9, out=0.08)
    for s in (-1, 1):
        patch(m, 'eye', -math.pi / 2 + 0.35 * s, 0.45, 0.17, 0.06, out=0.02)
        a = -math.pi / 2 + 0.55 * s
        m.spike('Root', 'ice', surf(a, 0.85), tuple((normal(a, 0.85) + Vector((0, 0, 1.4))).normalized()), 0.5, 0.2, twist=45, snap=False)


def woollymammoth(m):
    m.color('shell', '#7a4f33'); m.color('fur', '#6a4129'); m.color('fur2', '#8e6040'); m.color('tusk', '#eaf6ff', dots=False)
    m.color('snow', '#f4f8ff'); m.color('ice', '#a6efff', dots=False)
    add_shell(m, 'shell')
    for i in range(18):   # shaggy fur hanging off the shell
        a = i * math.tau / 18
        t = 0.35 if i % 2 else 0.05
        d = (normal(a, t) * 0.5 + Vector((0, 0, -1))).normalized()
        m.spike('Root', 'fur' if i % 3 else 'fur2', surf(a, t), tuple(d), 0.65, 0.3, 0.15)
    patch(m, 'snow', 0.0, 0.85, 0.65, 0.16, out=0.02)
    for s in (-1, 1):
        a = -math.pi / 2 + 0.4 * s
        base = Vector(surf(a, -0.25))
        n = normal(a, -0.25)
        pts = [tuple(base), tuple(base + n * 0.45 + Vector((0, 0, -0.25))), tuple(base + n * 0.85 + Vector((0, 0, 0.1))),
               tuple(base + n * 0.95 + Vector((0, 0, 0.55)))]
        m.loft('Root', 'tusk', pts, [(0.13, 0.13), (0.11, 0.11), (0.08, 0.08), (0.03, 0.03)], sides=7, steps=3, smooth=True)
    m.spike('Root', 'ice', surf(0, 0.98), (0, 0, 1), 0.45, 0.22, twist=45, snap=False)


def aurorawhale(m):
    m.color('shell', '#34428a'); m.color('shell2', '#2a346e'); m.color('glow', '#7dffc0', dots=False)
    m.color('glow2', '#b78cff', dots=False); m.color('glow3', '#7fd8ff', dots=False); m.color('ice', '#bff6ff', dots=False)
    m.color('star', '#eaf6ff', dots=False)
    add_shell(m, 'shell')
    zigzag(m, 'glow', 0.35, 0.12, 0.09, teeth=9)
    zigzag(m, 'glow2', 0.0, 0.14, 0.09, teeth=9)
    zigzag(m, 'glow3', -0.38, 0.12, 0.09, teeth=9)
    for i in range(10):
        a = i * 2.39996
        t = -0.85 + (i % 5) * 0.4
        patch(m, 'star', a, t, 0.05, 0.03, out=0.01)
    for d, l in (((0, 0, 1), 0.75), ((0.5, 0.2, 1), 0.5), ((-0.5, 0.2, 1), 0.5), ((0.1, -0.55, 1), 0.45), ((-0.2, 0.6, 1), 0.4)):
        m.spike('Root', 'ice', surf(0, 0.97), tuple(Vector(d).normalized()), l, 0.22 * l / 0.5, twist=45, snap=False)


BUILDERS.update({'SnowHare': snowhare, 'FrostPenguin': frostpenguin, 'TuskWalrus': tuskwalrus, 'SnowyOwl': snowyowl,
                 'WoollyMammoth': woollymammoth, 'AuroraWhale': aurorawhale})


# ------------------------------------------------------------------ Mythic Legends / Underworld eggs
FRONT = -math.pi / 2


def out_dir(a, t, up=1.0, k=1.0):
    return tuple((normal(a, t) * k + Vector((0, 0, up))).normalized())


def curl_horn(m, color, base, d0, s, segs=4, size=0.22, length=0.3):
    prev = Vector(base)
    for j in range(segs):
        a = j * 0.6
        d = Vector((d0[0] * s, 0.2 + 0.5 * math.sin(a), math.cos(a)))
        seg = length * (1 - 0.12 * j)
        m.spike('Root', color, tuple(prev), tuple(d.normalized()), seg * 1.6, size * (1 - 0.18 * j), snap=False)
        prev = prev + d.normalized() * seg


def flames(m, c1, c2, a, t, l, w):
    m.spike('Root', c1, surf(a, t), out_dir(a, t, 1.6, 0.5), l, w, w * 0.4)
    m.spike('Root', c2, surf(a, t, 0.03), out_dir(a, t, 1.8, 0.4), l * 0.65, w * 0.65, w * 0.3)


def imp(m):
    m.color('shell', '#b8222c'); m.color('dark', '#3a1a1e'); m.color('horn', '#1a1214', dots=False, edges=True)
    m.color('gold', '#ff9a2a', dots=False); m.color('wing', '#2e0e16', edges=True)
    add_shell(m, 'shell')
    zigzag(m, 'dark', -0.2, 0.12, 0.12, teeth=8)
    zigzag(m, 'gold', -0.2, 0.12, 0.04, teeth=8, out=0.05)   # glowing hellfire crack
    for i in range(7):
        patch(m, 'dark', i * 2.39996, 0.2 + (i % 3) * 0.15, 0.08, 0.04, out=0.01)
    for s in (-1, 1):
        curl_horn(m, 'horn', surf(math.pi / 2 + 0.5 * s, 0.85), (0.6, 0, 0), s)
        leaf(m, 'wing', s * 0.0 + (0 if s > 0 else math.pi), -0.6, 0.35, 1.0, out=0.08)
    # spade-tipped tail curling round the bottom
    pts = [surf(math.pi / 2 + i * 0.5, -0.75 + 0.08 * i, 0.06) for i in range(6)]
    m.loft('Root', 'dark', pts, [(0.06, 0.06)] * 6, sides=5, steps=2, smooth=True)
    m.box('Root', 'dark', pts[-1], (0.08, 0.32, 0.32), rot=(45, 0, 0), bevel=0.03)


def kitsunekit(m):
    m.color('shell', '#fff3e6'); m.color('orange', '#ff8a3a'); m.color('fire', '#5fd8ff', dots=False)
    m.color('fire2', '#d8f8ff', dots=False); m.color('ear', '#ff8a3a'); m.color('inner', '#ffd0d8')
    m.color('mark', '#e0302a', dots=False, edges=True); m.color('gold', '#ffcf3a', dots=False, edges=True)
    add_shell(m, 'shell')
    # red shrine zigzag round the middle, trimmed in gold (matches the adult's markings)
    zigzag(m, 'mark', 0.35, 0.1, 0.1, teeth=8)
    zigzag(m, 'gold', 0.35, 0.1, 0.035, teeth=8, out=0.05)
    for i in range(3):   # three tails wrapping up from the bottom
        leaf(m, 'orange', i * math.tau / 3 + 0.4, -0.98, 0.2, 1.1, out=0.08)
        leaf(m, 'shell', i * math.tau / 3 + 0.4, 0.05, 0.25, 0.5, out=0.11)
    for s in (-1, 1):
        a = FRONT + 0.6 * s
        base = Vector(surf(a, 0.82))
        d = Vector(out_dir(a, 0.82, 1.8, 0.6))
        m.spike('Root', 'ear', tuple(base), tuple(d), 0.7, 0.3, snap=False)
        m.spike('Root', 'inner', tuple(base + Vector(normal(a, 0.82)) * 0.05), tuple(d), 0.5, 0.18, snap=False)
    for a, t in ((0.3, 0.3), (2.4, 0.1), (4.2, 0.35)):
        flames(m, 'fire', 'fire2', a, t, 0.45, 0.16)


def gryphon(m):
    # storm gryphon: dark slate shell, white feather crown, gold band, cyan lightning
    m.color('shell', '#3b4060'); m.color('white', '#eef1f8'); m.color('wing', '#2c3150', edges=True); m.color('wing2', '#262a42')
    m.color('gold', '#ffcf3a', dots=False, edges=True); m.color('beak', '#ffc23a', dots=False, edges=True)
    m.color('glow', '#5ff2ff', dots=False)
    add_shell(m, 'shell')
    for i in range(10):   # white feathered crown
        a = i * math.tau / 10
        m.spike('Root', 'white', surf(a, 0.55), out_dir(a, 0.55, 0.9, 1.0), 0.5, 0.26, 0.08)
    patch(m, 'white', 0, 0.85, 0.55, 0.14, out=0.02)
    zigzag(m, 'gold', -0.05, 0.08, 0.1, teeth=12)
    zigzag(m, 'glow', -0.4, 0.1, 0.04, teeth=7, out=0.04)   # lightning crackling round the bottom
    for s in (-1, 1):
        for j, col in enumerate(('wing', 'wing2', 'wing')):
            leaf(m, col, (0 if s > 0 else math.pi) + (j - 1) * 0.35, -0.75 + 0.1 * j, 0.25 + 0.05 * j, 0.6, out=0.07 + 0.01 * j)
    m.spike('Root', 'beak', surf(FRONT, 0.6), out_dir(FRONT, 0.6, -0.5, 1.0), 0.4, 0.18, snap=False)


def chimera(m):
    m.color('shell', '#3a2c30'); m.color('mane', '#ff7a1e', edges=True); m.color('mane2', '#b8321a', edges=True)
    m.color('snake', '#1d3a26', edges=True); m.color('snake2', '#7aff5a', dots=False); m.color('horn', '#e2dacb', dots=False, edges=True)
    add_shell(m, 'shell')
    for i in range(14):   # lion mane ruff round the top
        a = i * math.tau / 14
        m.spike('Root', 'mane' if i % 2 else 'mane2', surf(a, 0.45), out_dir(a, 0.45, 0.3, 1.0), 0.55, 0.3, 0.12)
    for s in (-1, 1):
        curl_horn(m, 'horn', surf(math.pi / 2 + 0.4 * s, 0.85), (0.5, 0, 0), s, segs=5, size=0.18, length=0.25)
    # snake coiling round the bottom
    pts = [surf(i * 0.55, -0.7 + 0.06 * i, 0.07) for i in range(11)]
    m.loft('Root', 'snake', pts, [(0.11, 0.11)] * 10 + [(0.14, 0.14)], sides=6, steps=2, smooth=True)
    zigzag(m, 'snake2', -0.25, 0.06, 0.06, teeth=10)


def qilin(m):
    m.color('shell', '#17493c'); m.color('scale', '#0f3128', edges=True); m.color('gold', '#ffcf3a', dots=False, edges=True)
    m.color('flame', '#7fe0ff', dots=False); m.color('flame2', '#e8faff', dots=False); m.color('cloud', '#f6fbff', dots=False)
    add_shell(m, 'shell')
    for i in range(16):
        a = i * math.tau / 8 + (0.39 if i >= 8 else 0)
        t = -0.45 if i < 8 else 0.2
        patch(m, 'gold', a, t, 0.3, 0.07)
        patch(m, 'scale', a, t, 0.22, 0.07, out=0.03)
    for s in (-1, 1):   # branching golden antlers
        base = Vector(surf(math.pi / 2 + 0.35 * s, 0.88))
        d = Vector((0.4 * s, 0.25, 1)).normalized()
        m.spike('Root', 'gold', tuple(base), tuple(d), 0.8, 0.14, twist=45, snap=False)
        m.spike('Root', 'gold', tuple(base + d * 0.35), tuple(Vector((0.8 * s, -0.3, 0.6)).normalized()), 0.35, 0.09, twist=45, snap=False)
    flames(m, 'flame', 'flame2', 0, 0.97, 0.6, 0.22)
    for i in range(6):   # cloud puffs round the base
        a = i * math.tau / 6
        m.blob('Root', 'cloud', surf(a, -0.85, 0.12), (0.32, 0.32, 0.2), u=8, v=5)


def hydra(m):
    m.color('shell', '#143a3a'); m.color('scale', '#0d2828', edges=True); m.color('belly', '#cfc28a'); m.color('eye', '#8dff4a', dots=False)
    m.color('fang', '#f6f0e2', dots=False); m.color('glow', '#8dff4a', dots=False)
    add_shell(m, 'shell')
    for i in range(18):
        a = i * math.tau / 9 + (0.35 if i >= 9 else 0)
        patch(m, 'scale', a, -0.55 if i < 9 else 0.05, 0.25, 0.07)
    zigzag(m, 'belly', -0.25, 0.1, 0.08, teeth=9)
    zigzag(m, 'glow', -0.25, 0.1, 0.03, teeth=9, out=0.05)
    # five little serpent heads rising out of the top
    for i in range(5):
        a = FRONT + (i - 2) * 0.55
        base = Vector(surf(a, 0.7))
        n = Vector(normal(a, 0.7))
        mid = base + n * 0.35 + Vector((0, 0, 0.35))
        tip = mid + n * 0.25 + Vector((0, 0, 0.3 + (0.15 if i == 2 else 0)))
        m.loft('Root', 'shell', [tuple(base), tuple(mid), tuple(tip)], [(0.13, 0.13), (0.1, 0.1), (0.09, 0.09)], sides=6, steps=2, smooth=True)
        head = tip + n * 0.1
        m.blob('Root', 'scale', tuple(head), (0.15, 0.15, 0.11), u=8, v=5)
        for s in (-1, 1):
            side = Vector((-n.y, n.x, 0)) * s
            m.blob('Root', 'eye', tuple(head + side * 0.1 + Vector((0, 0, 0.06))), (0.035, 0.035, 0.035), u=6, v=4)
        m.spike('Root', 'fang', tuple(head + n * 0.1 - Vector((0, 0, 0.05))), (0, 0, -1), 0.1, 0.03, snap=False)


def skullcrawler(m):
    m.color('shell', '#efe4c8', edges=True); m.color('dark', '#140e10', dots=False); m.color('ember', '#ff7a1e', dots=False)
    m.color('leg', '#1e1820', dots=False, edges=True); m.color('wax', '#f2ead6'); m.color('flame', '#ffc43a', dots=False)
    m.color('crack', '#ff7a1e', dots=False)
    add_shell(m, 'shell')
    for s in (-1, 1):   # skull face on the front
        patch(m, 'dark', FRONT + 0.35 * s, 0.3, 0.24, 0.08, out=0.01)
        patch(m, 'ember', FRONT + 0.35 * s, 0.3, 0.08, 0.05, out=0.04)
    m.spike('Root', 'dark', surf(FRONT, 0.02, 0.02), out_dir(FRONT, 0.02, 0.0), 0.05, 0.1, snap=False)
    for k in range(6):
        patch(m, 'shell', FRONT + (k - 2.5) * 0.13, -0.22, 0.06, 0.06, out=0.04)
    zigzag(m, 'crack', 0.55, 0.12, 0.05, teeth=5)
    for i in range(6):   # spider legs round the bottom
        a = i * math.tau / 6 + 0.3
        m.spike('Root', 'leg', surf(a, -0.55), out_dir(a, -0.55, -0.7, 1.0), 0.6, 0.08, snap=False)
    top = Vector(surf(0, 0.98))
    m.loft('Root', 'wax', [tuple(top - Vector((0, 0, 0.05))), tuple(top + Vector((0, 0, 0.4)))], [(0.12, 0.12)] * 2, sides=8, steps=1, smooth=False)
    m.blob('Root', 'flame', tuple(top + Vector((0, 0, 0.55))), (0.08, 0.08, 0.15), u=6, v=5)


def lavatoad(m):
    m.color('shell', '#3a2a2a'); m.color('lava', '#ff6a1e', dots=False); m.color('lava2', '#ffd04a', dots=False)
    m.color('wart', '#5a3a32')
    add_shell(m, 'shell')
    zigzag(m, 'lava', 0.25, 0.18, 0.05, teeth=6)
    zigzag(m, 'lava', -0.35, 0.15, 0.05, teeth=7)
    zigzag(m, 'lava2', 0.25, 0.18, 0.02, teeth=6, out=0.05)
    for i in range(14):
        a = i * 2.39996
        t = -0.75 + (i % 7) * 0.24
        patch(m, 'wart', a, t, 0.1 + 0.03 * (i % 3), 0.07, out=0.02)
    for i in range(5):
        patch(m, 'lava', i * 1.3, 0.75 - 0.1 * (i % 2), 0.09, 0.05, out=0.03)
    for s in (-1, 1):   # bulging toad eyes on top
        m.blob('Root', 'wart', surf(FRONT + 0.4 * s, 0.82, 0.05), (0.22, 0.22, 0.2), u=8, v=6)
        m.blob('Root', 'lava2', surf(FRONT + 0.4 * s, 0.78, 0.2), (0.1, 0.1, 0.1), u=6, v=4)


def bonejackal(m):
    m.color('shell', '#2a2a30'); m.color('bone', '#efe4c8', edges=True); m.color('ghost', '#5dff9a', dots=False)
    m.color('ghost2', '#c8ffd8', dots=False)
    add_shell(m, 'shell')
    for t in (-0.45, -0.2, 0.05, 0.3):   # ribcage hoops
        lead, trail = [], []
        for i in range(9):
            a = FRONT - 1.2 + 2.4 * i / 8
            lead.append(surf(a, t + 0.04, 0.04)); trail.append(surf(a, t - 0.04, 0.04))
        m.strip('Root', 'bone', lead, trail, thickness=0.05)
    lead = [surf(FRONT, -0.6 + 0.12 * i, 0.05) for i in range(9)]
    m.strip('Root', 'bone', [surf(FRONT - 0.07, -0.6 + 0.12 * i, 0.05) for i in range(9)],
            [surf(FRONT + 0.07, -0.6 + 0.12 * i, 0.05) for i in range(9)], thickness=0.05)
    patch(m, 'ghost', FRONT, -0.1, 0.12, 0.06, out=0.0)
    for s in (-1, 1):   # tall bony jackal ears
        a = FRONT + 0.5 * s
        m.spike('Root', 'bone', surf(a, 0.8), out_dir(a, 0.8, 1.8, 0.5), 0.75, 0.24, 0.05)
    for a, t in ((0, 0.95), (2.0, 0.55), (4.2, 0.55)):
        flames(m, 'ghost', 'ghost2', a, t, 0.5, 0.17)


def shadowwraith(m):
    m.color('shell', '#3e3560'); m.color('cloak', '#2a2440'); m.color('void', '#05030a', dots=False)
    m.color('ghost', '#6dffc8', dots=False); m.color('iron', '#4a4a56', dots=False)
    add_shell(m, 'shell')
    patch(m, 'void', FRONT, 0.45, 0.42, 0.1, out=0.01)   # hood opening
    for s in (-1, 1):
        patch(m, 'ghost', FRONT + 0.15 * s, 0.5, 0.07, 0.04, out=0.05)
    for i in range(14):   # tattered cloak strips hanging off the middle
        a = i * math.tau / 14
        m.spike('Root', 'cloak', surf(a, -0.05), out_dir(a, -0.05, -1.0, 0.35), 0.75 + 0.2 * (i % 3), 0.28, 0.04)
    for i in range(12):   # a chain wrapped across
        a = FRONT - 1.4 + 2.8 * i / 11
        t = 0.2 - 0.6 * i / 11
        m.box('Root', 'iron', surf(a, t, 0.05), (0.14, 0.05, 0.1) if i % 2 else (0.05, 0.14, 0.1), bevel=0.02)
    m.spike('Root', 'cloak', surf(0, 0.95), (0, 0.3, 1), 0.5, 0.3, 0.04)   # hood peak


def cerberus(m):
    m.color('shell', '#2a2224'); m.color('lava', '#ff6a1e', dots=False); m.color('collar', '#b8262a')
    m.color('spike', '#d8d8e0', dots=False); m.color('flame', '#ff8a2a', dots=False); m.color('flame2', '#ffe08a', dots=False)
    add_shell(m, 'shell')
    zigzag(m, 'lava', 0.45, 0.15, 0.04, teeth=5)
    zigzag(m, 'lava', -0.5, 0.12, 0.04, teeth=6)
    zigzag(m, 'collar', 0.0, 0.0, 0.2, teeth=10)   # spiked collar band
    for i in range(10):
        a = i * math.tau / 10
        m.spike('Root', 'spike', surf(a, 0.0, 0.05), out_dir(a, 0.0, 0.0), 0.3, 0.1, snap=False)
    for k in range(3):   # three pairs of ears for three heads
        for s in (-1, 1):
            a = FRONT + (k - 1) * 1.0 + 0.2 * s
            m.spike('Root', 'shell', surf(a, 0.78), out_dir(a, 0.78, 1.5, 0.6), 0.45, 0.16, 0.04)
    flames(m, 'flame', 'flame2', 0, 0.97, 0.55, 0.22)


def infernalwyvern(m):
    m.color('shell', '#5a1a1e'); m.color('scale', '#8a2a24'); m.color('wing', '#2a1418'); m.color('horn', '#1a1214', dots=False)
    m.color('lava', '#ff7a1e', dots=False); m.color('lava2', '#ffd04a', dots=False)
    add_shell(m, 'shell')
    for i in range(18):
        a = i * math.tau / 9 + (0.35 if i >= 9 else 0)
        patch(m, 'scale', a, -0.5 if i < 9 else 0.15, 0.25, 0.07)
    zigzag(m, 'lava', -0.15, 0.14, 0.07, teeth=9)
    zigzag(m, 'lava2', -0.15, 0.14, 0.025, teeth=9, out=0.05)
    for s in (-1, 1):
        leaf(m, 'wing', 0 if s > 0 else math.pi, -0.7, 0.55, 1.3, out=0.08)
        m.spike('Root', 'horn', surf(math.pi / 2 + 0.4 * s, 0.85), out_dir(math.pi / 2 + 0.4 * s, 0.85, 1.0, 0.8), 0.6, 0.16, snap=False)
    for i in range(4):   # back spines
        t = 0.75 - 0.3 * i
        m.spike('Root', 'horn', surf(math.pi / 2, t), out_dir(math.pi / 2, t, 0.3), 0.3, 0.12, snap=False)
    flames(m, 'lava', 'lava2', 0, 0.97, 0.5, 0.2)


def hauntedpumpkin(m):
    """Haunted Pumpkin (featured egg): a cursed jack-o'-lantern. Deep burnt-orange shell split by
    near-black ribs, molten fissures glowing through the cracks as if hellfire is bursting out, a
    furious carved face (slanted eyes, a jagged grin full of fangs) blazing gold from inside, a
    gothic iron cage of riveted spiked bands and straps, tattered bat wings folded along the sides,
    a twisted thorny black stem crowned with purple ghost-fire, and a ring of glowing runes."""
    m.color('shell', '#f06a1a'); m.color('rib', '#2a120c', dots=False, edges=True)
    m.color('carve', '#140604', dots=False); m.color('glow', '#ffd23a', dots=False); m.color('glow2', '#ff7a12', dots=False)
    m.color('iron', '#33313c', dots=False, edges=True); m.color('rivet', '#8a8796', dots=False)
    m.color('stem', '#1c1012', edges=True); m.color('thorn', '#0e0809', dots=False)
    m.color('wing', '#2a1238', edges=True); m.color('bone', '#d9d0c2', dots=False)
    m.color('ghost', '#a25cff', dots=False); m.color('ghost2', '#e2c8ff', dots=False); m.color('rune', '#c08cff', dots=False)
    import random
    rnd = random.Random(13)
    add_shell(m, 'shell')

    def on_face(a, width=0.75):
        return abs(((a - FRONT + math.pi) % math.tau) - math.pi) < width

    # near-black ribs between the pumpkin segments
    for i in range(12):
        a = i * math.tau / 12
        if on_face(a, 0.8):
            continue
        leaf(m, 'rib', a, -0.96, 0.92, 0.1, out=0.025)

    # molten fissures: jagged glowing cracks wandering down the shell, a hot core inside each
    def fissure(a, t, steps, drift):
        pts = [(a, t)]
        for _ in range(steps):
            a += drift + rnd.uniform(-0.12, 0.12)
            t -= rnd.uniform(0.09, 0.15)
            pts.append((a, max(t, -0.95)))
        for color, w, out in (('glow2', 0.045, 0.02), ('glow', 0.018, 0.03)):
            m.strip('Root', color, [surf(pa - w, pt, out) for pa, pt in pts], [surf(pa + w, pt, out) for pa, pt in pts], thickness=0.04)
        return pts
    for a0, t0, n, d in ((FRONT + 1.35, 0.55, 8, -0.05), (FRONT + 2.4, 0.7, 10, 0.06), (FRONT - 1.3, 0.5, 8, 0.05),
                         (FRONT - 2.5, 0.75, 10, -0.04), (FRONT + math.pi, 0.4, 7, 0.08)):
        pts = fissure(a0, t0, n, d)
        bx = pts[n // 2]
        fissure(bx[0], bx[1], 3, d * -3)  # a branch

    def carved(color, top, bottom, out):
        m.strip('Root', color, [surf(a, t, out) for a, t in top], [surf(a, t, out) for a, t in bottom], thickness=0.05)

    # furious slanted eyes: the top edge drops towards the nose
    def eye(s, grow, color, out):
        top, bottom = [], []
        for k in range(9):
            f = k / 8  # 0 = inner corner, 1 = outer
            a = FRONT + s * (0.12 - grow + (0.5 + 2 * grow) * f)
            top.append((a, 0.2 + 0.32 * f + grow - 0.06 * f * f))
            bottom.append((a, 0.12 + 0.06 * math.sin(math.pi * f) - grow - 0.04 * f))
        carved(color, top, bottom, out)
    for s in (-1, 1):
        eye(s, 0.045, 'carve', 0.02)
        eye(s, 0.0, 'glow2', 0.033)
        eye(s, -0.03, 'glow', 0.04)
    # a sharp nose slit
    carved('carve', [(FRONT - 0.07, 0.07), (FRONT, 0.0), (FRONT + 0.07, 0.07)],
           [(FRONT - 0.03, -0.04), (FRONT, -0.1), (FRONT + 0.03, -0.04)], 0.025)
    carved('glow2', [(FRONT - 0.045, 0.04), (FRONT, -0.01), (FRONT + 0.045, 0.04)],
           [(FRONT - 0.02, -0.03), (FRONT, -0.075), (FRONT + 0.02, -0.03)], 0.035)
    # the grin: wide, curling up at the ends, long fangs top and bottom
    top, bot = [], []
    n = 17
    for k in range(n):
        f = k / (n - 1)
        a = FRONT - 0.85 + 1.7 * f
        smile = -0.16 * math.sin(math.pi * f) + 0.12 * (abs(f - 0.5) * 2) ** 3
        fang_down = 0.14 if k in (3, 7, 9, 13) else 0.0
        fang_up = 0.12 if k in (5, 11) else 0.0
        top.append((a, -0.17 + smile - fang_down))
        bot.append((a, -0.4 + smile * 1.25 + fang_up + 0.1 * (abs(f - 0.5) * 2) ** 2))
    carved('carve', [(a, t + 0.04) for a, t in top], [(a, t - 0.04) for a, t in bot], 0.02)
    carved('glow2', top, bot, 0.033)
    carved('glow', [(a, t - 0.03) for a, t in top], [(a, t + 0.03) for a, t in bot], 0.04)

    # gothic iron cage: two riveted bands bristling with spikes, straps over the crown
    for tb, spikes in ((0.62, True), (-0.62, False)):
        ring = [surf(i / 24 * math.tau, tb, 0.06) for i in range(25)]
        m.loft('Root', 'iron', ring, [(0.07, 0.1)] * len(ring), sides=6, steps=1, smooth=False, cap_round=0.0)
        for i in range(12):
            a = i / 12 * math.tau + 0.13
            if on_face(a, 0.35):
                continue
            m.blob('Root', 'rivet', surf(a, tb, 0.13), (0.05, 0.05, 0.05), u=6, v=4)
            if spikes and i % 2 == 0:
                m.spike('Root', 'iron', surf(a, tb, 0.08), tuple(normal(a, tb) + Vector((0, 0, 0.5))), 0.38, 0.13, snap=False)
    for a in (FRONT + 0.95, FRONT - 0.95, FRONT + math.pi):
        pts = [surf(a, t, 0.06) for t in (-0.62, -0.2, 0.2, 0.62, 0.86, 0.97)]
        m.loft('Root', 'iron', pts, [(0.06, 0.08)] * len(pts), sides=5, steps=2, smooth=False)

    # tattered bat wings folded along the sides
    for sgn in (-1, 1):
        a = FRONT + sgn * 1.9
        base = Vector(surf(a, 0.3, 0.05))
        outv = Vector(normal(a, 0.3))
        back = Vector((math.cos(a + sgn * 1.2), math.sin(a + sgn * 1.2), 0))
        elbow = base + outv * 0.55 + Vector((0, 0, 1.0))
        fingers = [elbow + back * 1.3 + Vector((0, 0, 0.1)), elbow + back * 1.1 + Vector((0, 0, -0.85)),
                   elbow + back * 0.6 + Vector((0, 0, -1.6))]
        m.loft('Root', 'bone', [tuple(base), tuple(elbow)], [(0.06, 0.06), (0.05, 0.05)], sides=5, steps=1, smooth=False)
        m.spike('Root', 'bone', tuple(elbow), (0, 0, 1), 0.3, 0.08, snap=False)  # wing claw
        prev = elbow
        for i, tip in enumerate(fingers):
            m.loft('Root', 'bone', [tuple(elbow), tuple(tip)], [(0.04, 0.04), (0.02, 0.02)], sides=4, steps=1, smooth=False)
            if i > 0:
                # membrane between this finger and the last, sagging (tattered) at the edge
                lead = [tuple(elbow.lerp(prev, f)) for f in (0.0, 0.5, 1.0)]
                sag = (prev + tip) / 2 + (elbow - (prev + tip) / 2) * 0.3
                trail = [tuple(elbow.lerp(tip, f)) for f in (0.0, 0.5)] + [tuple(sag)]
                m.strip('Root', 'wing', lead, trail, thickness=0.04)
            prev = tip
        m.strip('Root', 'wing', [tuple(base), tuple(base.lerp(elbow, 0.5)), tuple(elbow)],
                [tuple(base + Vector((0, 0, -0.5))), tuple(fingers[2].lerp(base, 0.55)), tuple(fingers[2])], thickness=0.04)

    # twisted thorny black stem crowned with ghost-fire
    stem = [surf(0, 0.9, -0.05), (0.06, 0.02, 3.3), (0.22, -0.05, 3.62), (0.12, -0.2, 3.9), (-0.08, -0.12, 4.1)]
    m.loft('Root', 'stem', stem, [(0.22, 0.22), (0.18, 0.18), (0.14, 0.14), (0.1, 0.1), (0.05, 0.05)], sides=5, steps=2, smooth=False)
    for i, (p, d) in enumerate(((stem[1], (1, 0.3, 0.2)), (stem[2], (-0.8, 0.5, 0.3)), (stem[2], (0.3, -1, 0.2)), (stem[3], (0.6, 0.6, 0.4)))):
        m.spike('Root', 'thorn', p, d, 0.3 - 0.04 * i, 0.08, snap=False)
    for a in (0.0, 2.1, 4.2):
        flames(m, 'ghost', 'ghost2', a, 0.93, 0.55, 0.22)
    m.spike('Root', 'ghost', (-0.05, -0.1, 4.0), (0, 0, 1), 0.7, 0.25, snap=False)
    m.spike('Root', 'ghost2', (-0.05, -0.1, 4.0), (0, 0, 1), 0.45, 0.14, snap=False)

    # a ring of glowing runes round the base
    for i in range(14):
        a = i / 14 * math.tau
        if on_face(a, 0.5):
            continue
        tilt = 0.08 if i % 2 else -0.08
        m.strip('Root', 'rune', [surf(a - 0.03, -0.72, 0.03), surf(a - 0.03 + tilt, -0.82, 0.03)],
                [surf(a + 0.03, -0.72, 0.03), surf(a + 0.03 + tilt, -0.82, 0.03)], thickness=0.03)
        patch(m, 'rune', a + 0.12, -0.77, 0.035, 0.02, out=0.035)


BUILDERS.update({'HauntedPumpkin': hauntedpumpkin, 'Imp': imp, 'KitsuneKit': kitsunekit, 'Gryphon': gryphon, 'Chimera': chimera, 'Qilin': qilin, 'Hydra': hydra,
                 'SkullCrawler': skullcrawler, 'LavaToad': lavatoad, 'BoneJackal': bonejackal, 'ShadowWraith': shadowwraith,
                 'Cerberus': cerberus, 'InfernalWyvern': infernalwyvern})


m = Monster(f'{SPECIES}Egg')
m.static = True
BUILDERS[SPECIES](m)
m.build(OUT)
