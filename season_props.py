"""Seasonal map decorations (static meshes) in the monsters' chunky low-poly, dotted-fabric style.
    blender -b --factory-startup --python season_props.py -- <out_dir> <Name> [<Name> ...]   (or a theme: Halloween)
    blender --factory-startup --python season_props.py -- <out_dir> <Name|Theme> ... --live
(--live builds them one after another in the open window so you can watch; it doesn't export.)

Writes SeasonPropData.luau next to the exports (each prop's size and light anchors) for the Studio
placer. Units: 1 Blender unit ~ 2.2 studs after import. Props face -Y.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from kit import Monster, _view3d_override

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LIVE = '--live' in args
args = [a for a in args if a != '--live']
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export', 'season')
NAMES = args[1:] or ['Halloween']
TAU = math.tau

PALETTE = dict(
    # Halloween
    pumpkin='#f2801e', pumpkin2='#d85f14', rib='#c4561a', stem='#4a5a24', stem2='#3a2a16', carve='#2a1206',
    glow='#ffcf4a', glow2='#ff8a1a', stone='#8a8794', stone2='#a4a1ae', stone3='#6c6976', mossy='#5f7a3a',
    carving='#4c4a56', bark='#3e3038', bark2='#56424c', iron='#2c2a32', iron2='#45424e', brew='#7aff5a',
    brew2='#c8ff8a', bone='#efe6d2', web='#eef0f6', bat='#2a2232', batwing='#40324a', purple='#8a4ad0',
    wood='#6e4a2c', wood2='#5a3a22', lamp='#ffb23a', metal='#2e2c36', candle='#f4ead2', flame='#ffd86a',
    banner='#5a2a7a', bannertext='#ff9a2a', dirt='#5a4030',
)


def setup(m, *keys):
    for k in keys:
        m.color(k, PALETTE[k], dots=True)


def cyl(m, col, a, b, r, sides=8, smooth=False, cap=0.0, r1=None):
    a, b = Vector(a), Vector(b)
    up = (0, 0, 1) if abs(b.z - a.z) < 0.9 * (b - a).length else (0, -1, 0)
    r1 = r if r1 is None else r1
    m.loft('Root', col, [tuple(a), tuple(b)], [(r, r), (r1, r1)], sides=sides, steps=1, smooth=smooth, cap_round=cap, up=up)


def light(m, kind, at, r):
    m.lights = getattr(m, 'lights', []) + [(kind, tuple(at), r)]


def tri(m, col, center, w, h, depth, slant=0.0, down=False, face=Vector((0, -1, 0))):
    """a carved triangle on a surface facing `face`: flat base, point up (or down)"""
    yaw = math.degrees(math.atan2(face.x, -face.y))
    m.box('Root', col, tuple(center), (w, depth, h), rot=(0, slant + (180 if down else 0), yaw), bevel=0.0,
          taper=dict(axis='z', end=1, scale=(0.05, 1)))


# ------------------------------------------------------------------ Halloween

def pumpkin_body(m, rng, c, r, h, ribs=10):
    """a squat ribbed pumpkin centred at c (radius r, half-height h)"""
    c = Vector(c)
    m.blob('Root', 'pumpkin', tuple(c), (r, r, h), u=12, v=8, smooth=False)
    for i in range(ribs):
        a = TAU * (i + 0.5) / ribs
        pts, rad = [], []
        for e in (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25):
            x, y, z = math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)
            pts.append(tuple(c + Vector((x * (r + 0.02), y * (r + 0.02), z * (h + 0.02)))))
            rad.append((0.03 * r, 0.055 * r))
        m.loft('Root', 'rib', pts, rad, sides=4, steps=2, smooth=False)
    # stem, curled, with a leaf
    top = c + Vector((0, 0, h * 0.92))
    m.loft('Root', 'stem', [tuple(top), tuple(top + Vector((0.05 * r, 0.03 * r, 0.32 * r))), tuple(top + Vector((0.2 * r, 0.1 * r, 0.42 * r)))],
           [(0.13 * r, 0.13 * r), (0.1 * r, 0.1 * r), (0.06 * r, 0.06 * r)], sides=6, steps=2, smooth=False)
    m.spike('Root', 'stem', tuple(top + Vector((0, 0, 0.08 * r))), (-1, 0.3, 0.25), 0.45 * r, 0.3 * r, 0.04 * r)


def jack_face(m, c, r, h, mood='grin', yaw=0.0):
    """a carved, glowing face on the pumpkin's front (rotated by yaw degrees round Z)"""
    c = Vector(c)
    rotz = lambda v: Vector((v.x * math.cos(math.radians(yaw)) - v.y * math.sin(math.radians(yaw)),
                             v.x * math.sin(math.radians(yaw)) + v.y * math.cos(math.radians(yaw)), v.z))
    face = rotz(Vector((0, -1, 0)))

    def surf(x, z):
        y = -math.sqrt(max(0.0, 1 - (x / r) ** 2 - (z / h) ** 2)) * r
        return c + rotz(Vector((x, y, z)))
    for s in (-1, 1):
        e = surf(0.38 * r * s, 0.25 * h)
        tri(m, 'carve', e, 0.36 * r, 0.32 * h, 0.12 * r, slant=18 * s if mood == 'angry' else 0, face=face)
        tri(m, 'glow', e + face * 0.03 * r, 0.24 * r, 0.22 * h, 0.1 * r, slant=18 * s if mood == 'angry' else 0, face=face)
    n = surf(0, -0.02 * h)
    tri(m, 'carve', n, 0.16 * r, 0.16 * h, 0.1 * r, face=face)
    tri(m, 'glow2', n + face * 0.03 * r, 0.1 * r, 0.1 * h, 0.08 * r, face=face)
    for k in range(7):   # the grin, with teeth
        f = (k - 3) / 3
        p = surf(0.55 * r * f, -0.34 * h + 0.14 * h * f * f)
        m.box('Root', 'carve', tuple(p), (0.17 * r, 0.12 * r, 0.14 * h), rot=(0, 0, yaw), bevel=0.0)
        m.box('Root', 'glow', tuple(p + face * 0.04 * r), (0.12 * r, 0.1 * r, 0.09 * h), rot=(0, 0, yaw), bevel=0.0)
        if k % 2 == 1:
            tri(m, 'pumpkin', p + face * 0.05 * r + Vector((0, 0, 0.05 * h)), 0.1 * r, 0.1 * h, 0.06 * r, down=True, face=face)
    light(m, 'lamp', c + face * 0.2 * r, 1.0 * r)


def pumpkin(m):
    """a jack-o'-lantern with a grin"""
    setup(m, 'pumpkin', 'rib', 'stem', 'carve', 'glow', 'glow2')
    rng = random.Random(1)
    pumpkin_body(m, rng, (0, 0, 0.62), 0.85, 0.62)
    jack_face(m, (0, 0, 0.62), 0.85, 0.62)


def pumpkin_big(m):
    """a giant angry jack-o'-lantern, a candle glowing inside, vines round its base"""
    setup(m, 'pumpkin', 'pumpkin2', 'rib', 'stem', 'stem2', 'carve', 'glow', 'glow2', 'dirt')
    rng = random.Random(2)
    pumpkin_body(m, rng, (0, 0, 1.45), 1.9, 1.4, ribs=12)
    jack_face(m, (0, 0, 1.45), 1.9, 1.4, mood='angry')
    for i in range(7):   # curling vines on the ground
        a = TAU * i / 7 + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [tuple(d * 1.6 + Vector((0, 0, 0.12))), tuple(d * 2.3 + Vector((0, 0, 0.1)) + Vector((-d.y, d.x, 0)) * 0.4),
               tuple(d * 2.7 + Vector((-d.y, d.x, 0)) * 0.1 + Vector((0, 0, 0.1)))]
        m.loft('Root', 'stem', pts, [(0.09, 0.09), (0.07, 0.07), (0.04, 0.04)], sides=5, steps=2, smooth=False)
        m.spike('Root', 'stem', pts[1], (d.x, d.y, 0.6), 0.5, 0.32, 0.04)
    m.blob('Root', 'dirt', (0, 0, 0.05), (2.0, 2.0, 0.12), u=10, v=3)


def pumpkin_pile(m):
    """three jack-o'-lanterns heaped together, different faces, a lit candle on top"""
    setup(m, 'pumpkin', 'pumpkin2', 'rib', 'stem', 'carve', 'glow', 'glow2', 'candle', 'flame')
    rng = random.Random(3)
    for (x, y, z, r, h, yaw, mood) in ((-0.75, 0, 0.55, 0.75, 0.55, -18, 'grin'), (0.8, -0.1, 0.5, 0.68, 0.5, 20, 'angry'),
                                       (0.05, 0.35, 1.35, 0.62, 0.48, 0, 'grin')):
        pumpkin_body(m, rng, (x, y, z), r, h, ribs=9)
        jack_face(m, (x, y, z), r, h, mood=mood, yaw=yaw)
    # a melting candle on the top one
    cyl(m, 'candle', (0.05, 0.35, 1.8), (0.05, 0.35, 2.3), 0.13, sides=7)
    m.loft('Root', 'candle', [(0.15, 0.25, 2.25), (0.17, 0.23, 1.95)], [(0.05, 0.05), (0.06, 0.06)], sides=5, steps=1, smooth=False)
    m.spike('Root', 'flame', (0.05, 0.35, 2.33), (0, 0, 1), 0.35, 0.16)
    light(m, 'lamp', (0.05, 0.35, 2.5), 0.4)


def grave_round(m):
    """a rounded headstone carved RIP with a cross, mossy, sunk in a mound"""
    setup(m, 'stone', 'stone2', 'stone3', 'carving', 'mossy', 'dirt')
    m.box('Root', 'stone', (0, 0, 1.05), (1.5, 0.38, 1.7), rot=(-6, 0, 3), bevel=0.06)
    m.loft('Root', 'stone', [(-0.75, 0, 1.85), (0, 0, 2.3), (0.75, 0, 1.85)], [(0.19, 0.19)] * 3, sides=6, steps=3, smooth=False, up=(0, -1, 0))
    m.blob('Root', 'stone2', (0, -0.02, 1.95), (0.72, 0.18, 0.38), rot=(-6, 0, 3), u=10, v=4)
    # the carving: a cross and RIP letters as raised dark strips
    m.box('Root', 'carving', (0, -0.21, 1.6), (0.1, 0.05, 0.6), rot=(-6, 0, 3), bevel=0.0)
    m.box('Root', 'carving', (0, -0.21, 1.72), (0.38, 0.05, 0.1), rot=(-6, 0, 3), bevel=0.0)
    for x in (-0.38, 0.0, 0.38):
        m.box('Root', 'carving', (x, -0.22, 1.0), (0.22, 0.05, 0.28), rot=(-6, 0, 3), bevel=0.0)
    m.blob('Root', 'mossy', (-0.45, -0.15, 2.05), (0.35, 0.2, 0.12), u=7, v=3)
    m.blob('Root', 'mossy', (0.6, -0.12, 0.4), (0.3, 0.2, 0.25), u=7, v=3)
    m.blob('Root', 'dirt', (0, -0.9, 0.05), (0.9, 1.4, 0.22), u=9, v=4)
    m.box('Root', 'stone3', (0, 0, 0.12), (1.8, 0.7, 0.24), bevel=0.04)


def grave_cross(m):
    """a leaning stone cross on a stepped base"""
    setup(m, 'stone', 'stone2', 'stone3', 'mossy', 'dirt')
    m.box('Root', 'stone3', (0, 0, 0.15), (1.2, 1.0, 0.3), bevel=0.04)
    m.box('Root', 'stone2', (0, 0, 0.4), (0.85, 0.7, 0.25), bevel=0.04)
    m.box('Root', 'stone', (0.08, 0, 1.55), (0.32, 0.3, 2.2), rot=(0, 7, 0), bevel=0.04)
    m.box('Root', 'stone', (0.2, 0, 2.05), (1.25, 0.3, 0.32), rot=(0, 7, 0), bevel=0.04)
    m.blob('Root', 'mossy', (0.0, -0.1, 0.55), (0.45, 0.4, 0.15), u=7, v=3)
    m.blob('Root', 'mossy', (0.55, -0.05, 2.15), (0.25, 0.2, 0.1), u=6, v=3)
    m.blob('Root', 'dirt', (0, -0.9, 0.05), (0.8, 1.2, 0.2), u=9, v=4)


def grave_skull(m):
    """a cracked, broken slab with a skull and bones in front"""
    setup(m, 'stone', 'stone2', 'stone3', 'carving', 'mossy', 'bone', 'carve', 'dirt')
    m.box('Root', 'stone2', (0, 0, 0.75), (1.3, 0.34, 1.5), rot=(-10, 0, -8), bevel=0.05)
    m.box('Root', 'stone2', (0.45, 0.05, 1.7), (0.55, 0.3, 0.5), rot=(-10, 25, -8), bevel=0.04)   # broken-off corner, tipped
    m.box('Root', 'carve', (-0.15, -0.19, 0.95), (0.06, 0.04, 0.9), rot=(-10, 25, -8), bevel=0.0)   # the crack
    m.box('Root', 'carve', (0.1, -0.19, 0.55), (0.05, 0.04, 0.5), rot=(-10, -30, -8), bevel=0.0)
    m.box('Root', 'stone3', (0, 0, 0.1), (1.6, 0.7, 0.2), bevel=0.04)
    # skull and crossed bones at its foot
    m.blob('Root', 'bone', (0.1, -0.75, 0.32), (0.3, 0.28, 0.27), u=8, v=6)
    m.box('Root', 'bone', (0.1, -0.85, 0.12), (0.3, 0.2, 0.14), bevel=0.03)
    for s in (-1, 1):
        m.blob('Root', 'carve', (0.1 + 0.11 * s, -1.0, 0.36), (0.07, 0.04, 0.08), u=5, v=4)
        cyl(m, 'bone', (-0.6, -0.65 + 0.25 * s, 0.08), (0.6, -0.65 - 0.25 * s, 0.08), 0.06, sides=5)
    m.blob('Root', 'mossy', (-0.5, -0.1, 1.45), (0.3, 0.2, 0.12), u=6, v=3)


def dead_tree(m):
    """a bare, twisted, spooky tree: crooked trunk, clawing branches, a lantern hung from a bough"""
    setup(m, 'bark', 'bark2', 'metal', 'lamp', 'dirt')
    rng = random.Random(9)
    trunk = [(0, 0, -0.1), (0.15, 0.05, 1.4), (-0.2, 0.1, 2.8), (0.25, -0.05, 4.1), (0.05, 0.1, 5.2)]
    m.loft('Root', 'bark', trunk, [(0.8, 0.8), (0.52, 0.52), (0.42, 0.42), (0.32, 0.32), (0.16, 0.16)], sides=7, steps=3, smooth=False)
    for a in range(5):   # gnarled roots
        ang = TAU * a / 5 + 0.2
        d = Vector((math.cos(ang), math.sin(ang), 0))
        m.loft('Root', 'bark2', [tuple(d * 0.4 + Vector((0, 0, 0.6))), tuple(d * 1.1 + Vector((0, 0, 0.1))), tuple(d * 1.7 + Vector((0, 0, -0.05)))],
               [(0.3, 0.3), (0.18, 0.18), (0.08, 0.08)], sides=5, steps=2, smooth=False)
    branches = []
    for ang, z, ln, rise in ((0.3, 2.6, 2.4, 0.5), (2.4, 3.3, 2.0, 0.65), (4.2, 2.9, 2.2, 0.45), (5.4, 4.0, 1.6, 0.8), (1.5, 4.4, 1.5, 0.9)):
        base = Vector((0, 0, z))
        d = Vector((math.cos(ang), math.sin(ang), rise)).normalized()
        mid = base + d * ln * 0.55 + Vector((0, 0, 0.15))
        tip = base + d * ln + Vector((math.cos(ang + 0.8), math.sin(ang + 0.8), 0)) * 0.4
        m.loft('Root', 'bark', [tuple(base), tuple(mid), tuple(tip)], [(0.22, 0.22), (0.13, 0.13), (0.04, 0.04)], sides=5, steps=2, smooth=False)
        branches.append((mid, tip, ang))
        for f in (0.5, 0.85):   # little claws off each bough
            p = base + (tip - base) * f
            m.spike('Root', 'bark2', tuple(p), (math.cos(ang - 1), math.sin(ang - 1), 0.8), 0.6, 0.12, 0.08)
    # a lantern hanging from the first bough
    mid, tip, ang = branches[0]
    hang = tip + Vector((0, 0, -0.1))
    cyl(m, 'metal', tuple(hang), tuple(hang + Vector((0, 0, -0.7))), 0.03, sides=5)
    c = hang + Vector((0, 0, -1.05))
    m.box('Root', 'metal', tuple(c + Vector((0, 0, 0.3))), (0.42, 0.42, 0.08), bevel=0.02)
    m.box('Root', 'lamp', tuple(c), (0.3, 0.3, 0.5), bevel=0.03)
    m.box('Root', 'metal', tuple(c - Vector((0, 0, 0.3))), (0.38, 0.38, 0.08), bevel=0.02)
    light(m, 'lamp', c, 0.8)
    m.blob('Root', 'dirt', (0, 0, 0.02), (1.6, 1.6, 0.15), u=9, v=3)


def cauldron(m):
    """a fat iron witch's cauldron on stubby legs over a log fire, glowing green brew, bubbles, a bone"""
    setup(m, 'iron', 'iron2', 'brew', 'brew2', 'bone', 'wood', 'wood2', 'glow2', 'glow', 'stone3')
    rng = random.Random(5)
    m.blob('Root', 'iron', (0, 0, 1.25), (1.25, 1.25, 1.0), u=12, v=8)
    m.loft('Root', 'iron2', [(1.1 * math.cos(TAU * i / 16), 1.1 * math.sin(TAU * i / 16), 2.05) for i in range(17)],
           [(0.16, 0.16)] * 17, sides=6, steps=1, smooth=False, cap_round=0.0)   # the rim
    m.blob('Root', 'brew', (0, 0, 1.98), (1.0, 1.0, 0.12), u=12, v=4)
    for _ in range(6):   # bubbles
        a, d = rng.uniform(0, TAU), rng.uniform(0, 0.75)
        rr = rng.uniform(0.1, 0.22)
        m.blob('Root', 'brew2', (math.cos(a) * d, math.sin(a) * d, 2.05 + rr * 0.5), (rr, rr, rr), u=6, v=4)
    cyl(m, 'bone', (-0.5, -0.3, 2.0), (0.4, 0.5, 2.7), 0.08, sides=5)   # a bone poking out
    m.blob('Root', 'bone', (0.45, 0.55, 2.75), (0.14, 0.14, 0.12), u=6, v=4)
    for s in (-1, 1):   # handles
        m.loft('Root', 'iron2', [(1.15 * s, -0.3, 1.9), (1.45 * s, 0, 2.05), (1.15 * s, 0.3, 1.9)], [(0.07, 0.07)] * 3, sides=5, steps=2, smooth=False)
    for i in range(3):   # legs
        a = TAU * i / 3 + 0.5
        m.box('Root', 'iron2', (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.35), (0.25, 0.25, 0.7), bevel=0.04)
    for i in range(5):   # logs and the fire
        a = TAU * i / 5
        d = Vector((math.cos(a), math.sin(a), 0))
        cyl(m, 'wood' if i % 2 else 'wood2', tuple(d * 1.3 + Vector((0, 0, 0.15))), tuple(d * 0.2 + Vector((0, 0, 0.35))), 0.15, sides=6)
    for i in range(6):
        a = TAU * i / 6 + 0.3
        m.spike('Root', 'glow2' if i % 2 else 'glow', (math.cos(a) * 0.4, math.sin(a) * 0.4, 0.3), (math.cos(a) * 0.3, math.sin(a) * 0.3, 1), 0.55, 0.22)
    for i in range(8):
        a = TAU * i / 8
        m.blob('Root', 'stone3', (math.cos(a) * 1.55, math.sin(a) * 1.55, 0.12), (0.25, 0.22, 0.16), u=6, v=4)
    light(m, 'glow', (0, 0, 2.2), 1.2)
    light(m, 'lamp', (0, 0, 0.5), 0.8)


def halloween_arch(m):
    """a spooky arch over the conveyor: twisted dead-wood posts, jack-o'-lanterns on top, a tattered
    banner, bats hanging under the beam and lanterns swinging from its ends (spans ~22 studs)"""
    setup(m, 'bark', 'bark2', 'pumpkin', 'rib', 'stem', 'carve', 'glow', 'glow2', 'banner', 'bannertext',
          'bat', 'batwing', 'metal', 'lamp', 'web', 'stone', 'stone3')
    rng = random.Random(13)
    W = 5.6
    for s in (-1, 1):
        x = W * s
        m.blob('Root', 'stone3', (x, 0, 0.3), (0.9, 0.9, 0.5), u=8, v=4)
        post = [(x, 0, 0.0), (x + 0.15 * s, 0.1, 2.2), (x - 0.15 * s, -0.05, 4.4), (x, 0.05, 6.8)]
        m.loft('Root', 'bark', post, [(0.58, 0.58), (0.48, 0.48), (0.44, 0.44), (0.38, 0.38)], sides=7, steps=3, smooth=False)
        for z in (1.6, 3.6, 5.3):   # spiky snags
            m.spike('Root', 'bark2', (x, -0.3, z), (0.4 * s, -1, 0.5), 0.8, 0.18, 0.12)
        # a jack-o'-lantern crowning each post
        pumpkin_body(m, rng, (x, 0, 7.55), 0.8, 0.6, ribs=9)
        jack_face(m, (x, 0, 7.55), 0.8, 0.6, mood='angry')
        # lanterns at the beam ends
        cyl(m, 'metal', (x + 0.95 * s, -0.2, 6.5), (x + 0.95 * s, -0.2, 6.0), 0.03, sides=5)
        c = Vector((x + 0.95 * s, -0.2, 5.65))
        m.box('Root', 'metal', tuple(c + Vector((0, 0, 0.3))), (0.42, 0.42, 0.08), bevel=0.02)
        m.box('Root', 'lamp', tuple(c), (0.3, 0.3, 0.5), bevel=0.03)
        m.box('Root', 'metal', tuple(c - Vector((0, 0, 0.3))), (0.38, 0.38, 0.08), bevel=0.02)
        light(m, 'lamp', c, 0.9)
    # the crooked crossbeam
    m.loft('Root', 'bark', [(-W - 0.9, 0, 6.6), (-2.0, 0.05, 6.9), (2.0, -0.05, 6.75), (W + 0.9, 0, 6.6)],
           [(0.38, 0.38), (0.34, 0.34), (0.34, 0.34), (0.38, 0.38)], sides=7, steps=3, smooth=False)
    # tattered banner (the game can write on it) with spiky torn edges
    m.box('Root', 'banner', (0, -0.42, 5.75), (7.2, 0.12, 1.3), bevel=0.03)
    for i in range(9):
        x = -3.4 + 6.8 * i / 8
        m.spike('Root', 'banner', (x, -0.42, 5.12), (0, 0, -1), 0.45 + 0.2 * (i % 2), 0.55, 0.1)
    m.box('Root', 'bannertext', (0, -0.5, 5.8), (5.4, 0.04, 0.12), bevel=0.0)
    m.box('Root', 'bannertext', (0, -0.5, 6.25), (6.6, 0.04, 0.08), bevel=0.0)
    # bats hanging upside down from the beam
    for x in (-3.0, -1.2, 1.4, 3.2):
        cyl(m, 'metal', (x, 0, 6.35), (x, 0, 6.15), 0.02, sides=4)
        m.blob('Root', 'bat', (x, 0, 5.95), (0.18, 0.15, 0.25), u=6, v=5)
        for s in (-1, 1):
            m.strip('Root', 'batwing', [(x, 0, 6.05), (x + 0.5 * s, 0.05, 5.9), (x + 0.6 * s, 0.05, 5.55)],
                    [(x, 0, 5.8), (x + 0.3 * s, 0.05, 5.65), (x + 0.4 * s, 0.05, 5.5)], thickness=0.04)
            m.spike('Root', 'bat', (x + 0.08 * s, 0, 5.75), (0.2 * s, 0, -1), 0.14, 0.08)
    # cobwebs in the top corners
    for s in (-1, 1):
        x = W * s
        for k in range(4):
            a = (k / 3) * (math.pi / 2)
            end = Vector((x - math.cos(a) * 1.6 * s, -0.35, 6.35 - math.sin(a) * 1.6))
            cyl(m, 'web', (x, -0.35, 6.35), tuple(end), 0.02, sides=3)
        for rr in (0.6, 1.1, 1.5):
            pts = [(x - math.cos(a) * rr * s, -0.35, 6.35 - math.sin(a) * rr) for a in (0, 0.5, 1.0, 1.57)]
            m.loft('Root', 'web', pts, [(0.015, 0.015)] * 4, sides=3, steps=1, smooth=False)


def cobweb(m):
    """a big cobweb for fence corners and trees: spokes and sagging rings, a fat spider"""
    setup(m, 'web', 'bat', 'purple')
    spokes = 7
    for k in range(spokes):
        a = (k / (spokes - 1)) * (math.pi / 2)
        cyl(m, 'web', (0, 0, 0), (math.cos(a) * 2.4, 0, -math.sin(a) * 2.4), 0.025, sides=3)
    for rr in (0.6, 1.1, 1.6, 2.1):
        pts = []
        for k in range(spokes):
            a = (k / (spokes - 1)) * (math.pi / 2)
            sag = 0.12 * rr if 0 < k < spokes - 1 else 0
            pts.append((math.cos(a) * (rr - sag), 0, -math.sin(a) * (rr - sag)))
        m.loft('Root', 'web', pts, [(0.02, 0.02)] * len(pts), sides=3, steps=1, smooth=False)
    m.blob('Root', 'bat', (1.1, -0.05, -1.0), (0.2, 0.18, 0.24), u=6, v=5)
    m.blob('Root', 'purple', (1.1, -0.12, -0.8), (0.12, 0.1, 0.1), u=6, v=4)
    for i in range(4):
        for s in (-1, 1):
            m.loft('Root', 'bat', [(1.1, -0.05, -1.0 + 0.08 * i - 0.1), (1.1 + 0.3 * s, -0.08, -0.95 + 0.1 * i), (1.1 + 0.42 * s, -0.08, -1.2 + 0.1 * i)],
                   [(0.025, 0.025)] * 3, sides=3, steps=1, smooth=False)


# ------------------------------------------------------------------ Christmas

XMAS = dict(pine='#2f7a3e', pine2='#3f9450', snow='#f4f8fd', snow2='#dde8f4', trunk='#6a4426', gold='#ffd23a', gold2='#e8a820',
            red='#e2323a', red2='#b81e2a', green='#2e9a48', blue='#3a8ae8', white='#ffffff', silver='#d8dce6',
            carrot='#ff8a2a', coal='#2a2a30', scarf='#e2323a', scarf2='#2e9a48', hat='#26262e', wood2='#5a3a22', star='#fff2a0')
PALETTE.update(XMAS)


def stripe_cane(m, pts, r, cols=('red', 'white'), seg=0.28):
    """a striped candy cane along the polyline `pts` (alternating short segments)"""
    path = [Vector(p) for p in pts]
    k = 0
    for a, b in zip(path, path[1:]):
        n = max(1, int((b - a).length / seg))
        for i in range(n):
            p0, p1 = a + (b - a) * (i / n), a + (b - a) * ((i + 1) / n)
            cyl(m, cols[k % 2], tuple(p0), tuple(p1), r, sides=7)
            k += 1


def present(m, c, size, box_col, ribbon_col, yaw=0.0):
    c = Vector(c)
    sx, sy, sz = size
    m.box('Root', box_col, tuple(c + Vector((0, 0, sz / 2))), (sx, sy, sz), rot=(0, 0, yaw), bevel=0.04)
    m.box('Root', ribbon_col, tuple(c + Vector((0, 0, sz / 2))), (sx + 0.04, sy * 0.18, sz + 0.04), rot=(0, 0, yaw), bevel=0.0)
    m.box('Root', ribbon_col, tuple(c + Vector((0, 0, sz / 2))), (sx * 0.18, sy + 0.04, sz + 0.04), rot=(0, 0, yaw), bevel=0.0)
    for s in (-1, 1):   # the bow
        m.blob('Root', ribbon_col, tuple(c + Vector((0.18 * s * sx, 0, sz + 0.1))), (0.2 * sx, 0.1 * sx, 0.12 * sx), rot=(0, 25 * s, yaw), u=6, v=4)
    m.blob('Root', ribbon_col, tuple(c + Vector((0, 0, sz + 0.06))), (0.08 * sx, 0.08 * sx, 0.08 * sx), u=5, v=4)


def xmas_tree(m):
    """a giant decorated Christmas tree: snowy tiers, baubles, a gold garland, a glowing star, presents"""
    setup(m, 'pine', 'pine2', 'snow', 'trunk', 'gold', 'gold2', 'red', 'green', 'blue', 'silver', 'star', 'red2', 'white')
    rng = random.Random(25)
    cyl(m, 'trunk', (0, 0, 0), (0, 0, 1.6), 0.55, sides=8)
    tiers = ((3.4, 2.6), (2.9, 2.4), (2.35, 2.2), (1.8, 2.0), (1.2, 1.8), (0.7, 1.4))
    z = 1.2
    rings = []
    for i, (r, h) in enumerate(tiers):
        cyl(m, 'pine' if i % 2 == 0 else 'pine2', (0, 0, z), (0, 0, z + h), r, r1=0.05, sides=9)
        # snow resting on the tier's shoulders
        for k in range(9):
            a = TAU * (k + 0.5) / 9
            m.blob('Root', 'snow', (math.cos(a) * r * 0.82, math.sin(a) * r * 0.82, z + 0.22), (0.38 * r * 0.4 + 0.1, 0.3, 0.12), rot=(0, 0, math.degrees(a)), u=6, v=3)
        rings.append((z, r, h))
        z += h * 0.6
    top = z + 0.4
    # baubles hung round each tier's rim
    cols = ('red', 'gold', 'blue', 'silver', 'green')
    for j, (z0, r, h) in enumerate(rings):
        for k in range(7 + j % 2):
            a = TAU * k / (7 + j % 2) + j * 0.4
            rr = 0.17 + 0.05 * (k % 2)
            m.blob('Root', cols[(k + j) % len(cols)], (math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, z0 + 0.05), (rr, rr, rr), u=7, v=5)
    # a gold garland spiralling down
    pts = []
    for i in range(40):
        t = i / 39
        zz = top - 0.6 - t * (top - 2.0)
        frac = (zz - 1.2) / (top - 1.2)
        rr = 3.2 * (1 - frac) * 0.9 + 0.25
        a = t * TAU * 3.2
        pts.append((math.cos(a) * rr, math.sin(a) * rr, zz))
    m.loft('Root', 'gold', pts, [(0.07, 0.07)] * len(pts), sides=4, steps=1, smooth=False)
    # the star
    for k in range(5):
        a = TAU * k / 5 + math.pi / 2
        m.spike('Root', 'star', (0, -0.05, top + 0.35), (math.cos(a), 0, math.sin(a)), 0.75, 0.34, 0.16)
    m.blob('Root', 'gold', (0, -0.05, top + 0.35), (0.3, 0.2, 0.3), u=7, v=5)
    light(m, 'lamp', (0, 0, top + 0.35), 1.6)
    # presents round the foot
    for k, (box, rib) in enumerate((('red', 'gold'), ('blue', 'white'), ('green', 'red'), ('gold', 'red2'), ('silver', 'blue'))):
        a = TAU * k / 5 + 0.3
        present(m, (math.cos(a) * 2.6, math.sin(a) * 2.6, 0), (rng.uniform(0.8, 1.2), rng.uniform(0.8, 1.2), rng.uniform(0.6, 1.0)), box, rib, yaw=math.degrees(a))


def presents(m):
    """a heap of wrapped presents"""
    setup(m, 'red', 'red2', 'gold', 'green', 'blue', 'white', 'silver')
    present(m, (-0.55, 0, 0), (1.2, 1.1, 0.9), 'red', 'gold', yaw=10)
    present(m, (0.65, 0.1, 0), (0.95, 0.95, 0.75), 'blue', 'white', yaw=-15)
    present(m, (0.05, 0.6, 0), (0.8, 0.8, 1.1), 'green', 'red', yaw=30)
    present(m, (-0.4, 0.05, 0.9), (0.7, 0.7, 0.55), 'gold', 'red2', yaw=-20)
    present(m, (0.6, -0.05, 0.75), (0.5, 0.5, 0.45), 'silver', 'blue', yaw=40)


def candy_cane(m):
    """a tall striped candy cane planted in a snow mound, a bow on its neck"""
    setup(m, 'red', 'white', 'snow', 'green', 'gold')
    hook = [(0, 0, 0), (0, 0, 3.6)]
    for i in range(1, 8):
        a = math.pi * i / 7
        hook.append((0.55 - math.cos(a) * 0.55, 0, 3.6 + math.sin(a) * 0.55))
    hook.append((1.1, 0, 3.25))
    stripe_cane(m, hook, 0.2)
    for s in (-1, 1):
        m.blob('Root', 'green', (0.25 * s, -0.12, 2.9), (0.25, 0.1, 0.14), rot=(0, 25 * s, 0), u=6, v=4)
    m.blob('Root', 'gold', (0, -0.18, 2.9), (0.1, 0.08, 0.1), u=5, v=4)
    m.blob('Root', 'snow', (0, 0, 0.05), (0.75, 0.75, 0.28), u=8, v=4)


def snowman(m):
    """a jolly snowman: three snowballs, coal eyes and buttons, carrot nose, scarf, top hat, twig arms"""
    setup(m, 'snow', 'snow2', 'coal', 'carrot', 'scarf', 'scarf2', 'hat', 'red', 'wood2')
    m.blob('Root', 'snow', (0, 0, 0.95), (1.05, 1.05, 0.95), u=10, v=8)
    m.blob('Root', 'snow', (0, 0, 2.35), (0.78, 0.78, 0.7), u=10, v=8)
    m.blob('Root', 'snow', (0, 0, 3.45), (0.58, 0.58, 0.55), u=10, v=8)
    m.blob('Root', 'snow2', (0, 0, 0.12), (1.3, 1.3, 0.2), u=10, v=4)
    for s in (-1, 1):
        m.blob('Root', 'coal', (0.2 * s, -0.5, 3.6), (0.07, 0.05, 0.08), u=5, v=4)
        m.loft('Root', 'wood2', [(0.7 * s, 0, 2.5), (1.4 * s, -0.1, 3.0), (1.8 * s, -0.1, 3.4)], [(0.06, 0.06), (0.05, 0.05), (0.03, 0.03)], sides=5, steps=2, smooth=False)
        m.spike('Root', 'wood2', (1.45 * s, -0.1, 3.05), (0.3 * s, 0, 1), 0.35, 0.05)
    for z in (2.65, 2.35, 2.05, 1.4, 1.0):
        m.blob('Root', 'coal', (0, -0.78 + (0.07 if z < 1.6 else 0.06), z), (0.07, 0.05, 0.07), u=5, v=4)
    m.spike('Root', 'carrot', (0, -0.52, 3.45), (0, -1, -0.08), 0.6, 0.13)
    # scarf with stripes and a hanging tail
    m.loft('Root', 'scarf', [(0.6 * math.cos(TAU * i / 12), 0.6 * math.sin(TAU * i / 12), 2.95) for i in range(13)], [(0.13, 0.16)] * 13,
           sides=5, steps=1, smooth=False, cap_round=0.0)
    m.box('Root', 'scarf', (0.35, -0.55, 2.55), (0.28, 0.12, 0.85), rot=(10, 0, -10), bevel=0.03)
    for z in (2.35, 2.65):
        m.box('Root', 'scarf2', (0.35, -0.62, z), (0.3, 0.06, 0.08), rot=(10, 0, -10), bevel=0.0)
    # top hat
    m.loft('Root', 'hat', [(0, 0, 3.88), (0, 0, 4.0)], [(0.62, 0.62)] * 2, sides=10, steps=1, smooth=False)
    m.loft('Root', 'hat', [(0, 0, 3.98), (0, 0, 4.7)], [(0.4, 0.4), (0.42, 0.42)], sides=10, steps=1, smooth=False)
    m.loft('Root', 'red', [(0, 0, 4.05), (0, 0, 4.18)], [(0.42, 0.42)] * 2, sides=10, steps=1, smooth=False)


def sleigh(m):
    """Santa's sleigh: a curly red body with gold trim and runners, a sack of presents in the back"""
    setup(m, 'red', 'red2', 'gold', 'gold2', 'scarf2', 'green', 'blue', 'white', 'silver', 'snow')
    # runners: a gold rail each side curling up at the front
    for s in (-1, 1):
        rail = [(1.0 * s, 1.8, 0.15), (1.0 * s, -1.6, 0.15), (1.0 * s, -2.3, 0.5), (1.0 * s, -2.4, 1.0), (1.0 * s, -2.0, 1.15)]
        m.loft('Root', 'gold', rail, [(0.09, 0.09)] * 5, sides=5, steps=2, smooth=False)
        for y in (-1.0, 0.4, 1.4):
            cyl(m, 'gold2', (1.0 * s, y, 0.15), (0.85 * s, y, 0.75), 0.07, sides=5)
    # the body: a tub with a high curled back
    m.box('Root', 'red', (0, 0.1, 1.15), (2.0, 3.0, 0.9), bevel=0.2, taper=dict(axis='y', end=-1, scale=(0.9, 0.75)))
    m.box('Root', 'red2', (0, 1.45, 1.9), (2.0, 0.5, 1.6), rot=(-12, 0, 0), bevel=0.2)
    for s in (-1, 1):
        m.loft('Root', 'red', [(0.95 * s, -1.35, 1.2), (0.95 * s, -1.8, 1.6), (0.95 * s, -1.55, 2.0), (0.95 * s, -1.25, 1.8)], [(0.12, 0.12)] * 4,
               sides=5, steps=2, smooth=False)   # front curl
    m.loft('Root', 'gold', [(-1.02, -1.3, 1.6), (-1.02, 1.6, 1.6)], [(0.05, 0.05)] * 2, sides=4, steps=1, smooth=False)
    m.loft('Root', 'gold', [(1.02, -1.3, 1.6), (1.02, 1.6, 1.6)], [(0.05, 0.05)] * 2, sides=4, steps=1, smooth=False)
    m.box('Root', 'scarf2', (0, 0.3, 1.62), (1.7, 1.6, 0.12), bevel=0.05)   # green velvet seat
    # the sack, bulging with presents
    m.blob('Root', 'silver', (0, 1.0, 2.2), (0.75, 0.6, 0.7), u=8, v=6)
    for k, (box, rib) in enumerate((('blue', 'white'), ('green', 'red'), ('red', 'gold'))):
        present(m, (-0.4 + 0.4 * k, 0.9 + 0.1 * (k % 2), 2.6 + 0.1 * k), (0.4, 0.4, 0.38), box, rib, yaw=20 * k)
    m.blob('Root', 'snow', (0, -0.2, 0.1), (1.6, 2.6, 0.12), u=10, v=4)


def xmas_arch(m):
    """the conveyor arch: two giant candy canes, a pine garland with baubles and lights, a sign, a star"""
    setup(m, 'red', 'white', 'pine', 'pine2', 'gold', 'blue', 'green', 'silver', 'snow', 'star', 'scarf', 'red2')
    W = 5.6
    for s in (-1, 1):
        x = W * s
        hook = [(x, 0, 0), (x, 0, 6.6)]
        for i in range(1, 8):
            a = math.pi * i / 7
            hook.append((x - s * (0.7 - math.cos(a) * 0.7), 0, 6.6 + math.sin(a) * 0.7))
        hook.append((x - s * 1.4, 0, 6.2))
        stripe_cane(m, hook, 0.36, seg=0.4)
        m.blob('Root', 'snow', (x, 0, 0.1), (1.0, 1.0, 0.35), u=8, v=4)
    # the garland between them, sagging, with baubles and little lights
    pts = [(-W + 1.4, -0.1, 6.3)]
    for i in range(1, 12):
        t = i / 12
        pts.append((-W + 1.4 + (2 * W - 2.8) * t, -0.1, 6.3 - math.sin(math.pi * t) * 0.6))
    pts.append((W - 1.4, -0.1, 6.3))
    for i, p in enumerate(pts):
        m.blob('Root', 'pine' if i % 2 else 'pine2', p, (0.55, 0.45, 0.45), rot=(0, 0, 30 * i), u=7, v=5)
        if 0 < i < len(pts) - 1:
            col = ('red', 'gold', 'blue', 'silver')[i % 4]
            m.blob('Root', col, (p[0], p[1] - 0.45, p[2] - 0.35), (0.18, 0.18, 0.18), u=6, v=4)
    # the sign, hung on ribbons, a star on top
    for s in (-1, 1):
        cyl(m, 'scarf', (2.0 * s, -0.2, 6.0), (2.0 * s, -0.2, 5.3), 0.05, sides=4)
    m.box('Root', 'red2', (0, -0.2, 4.9), (5.2, 0.2, 1.05), bevel=0.08)
    m.box('Root', 'gold', (0, -0.2, 4.9), (5.4, 0.16, 1.2), bevel=0.06)
    for k in range(5):
        a = TAU * k / 5 + math.pi / 2
        m.spike('Root', 'star', (0, -0.15, 7.25), (math.cos(a), 0, math.sin(a)), 0.8, 0.36, 0.16)
    cyl(m, 'gold', (0, -0.15, 5.75), (0, -0.15, 7.0), 0.07, sides=5)   # the rod the star stands on
    m.blob('Root', 'gold', (0, -0.15, 7.25), (0.32, 0.2, 0.32), u=7, v=5)
    light(m, 'lamp', (0, -0.3, 7.25), 1.4)


# ------------------------------------------------------------------ Easter

EASTER = dict(egg1='#ffb4d4', egg2='#a8d8ff', egg3='#fff08a', egg4='#c8f0a8', egg5='#d8b8ff', eggw='#ffffff',
              fur='#f6f2f8', fur2='#e4dcec', earpink='#ffb4cc', nose='#ff8ab0', eye='#2a2230', grass='#7ad85a', grass2='#5ec24a',
              basket='#d8a464', basket2='#b8844a', ribbon='#ff8ac0', ribbon2='#9ad0ff', petal='#ffc8e0', petal2='#fff4a0',
              stemg='#5ab84a', carrotO='#ff9a3a', soil='#8a6448', archw='#fff6e8', archw2='#ffe0ec')
PALETTE.update(EASTER)


def painted_egg(m, c, r, base, band, dots, tilt=0.0):
    """an Easter egg: a base colour, a zig-zag band and polka dots"""
    c = Vector(c)
    m.blob('Root', base, tuple(c), (r, r, r * 1.32), rot=(tilt, 0, 0), u=10, v=8)
    n = 12
    pts = []
    for i in range(n + 1):
        a = TAU * i / n
        z = 0.12 * r * (1 if i % 2 else -1)
        pts.append(tuple(c + Vector((math.cos(a) * r * 1.01, math.sin(a) * r * 1.01, z))))
    m.loft('Root', band, pts, [(0.09 * r, 0.12 * r)] * (n + 1), sides=4, steps=1, smooth=False, cap_round=0.0)
    for zf, rf in ((0.6, 0.78), (-0.55, 0.82)):
        for k in range(6):
            a = TAU * k / 6 + zf
            p = c + Vector((math.cos(a) * r * rf, math.sin(a) * r * rf, zf * r * 1.32))
            m.blob('Root', dots, tuple(p), (0.12 * r, 0.12 * r, 0.12 * r), u=5, v=4)


def easter_egg_big(m):
    """a giant painted egg on a nest of grass"""
    setup(m, 'egg1', 'egg2', 'egg3', 'eggw', 'grass', 'grass2')
    painted_egg(m, (0, 0, 2.0), 1.4, 'egg1', 'egg2', 'eggw')
    for i in range(16):
        a = TAU * i / 16
        m.spike('Root', 'grass' if i % 2 else 'grass2', (math.cos(a) * 1.2, math.sin(a) * 1.2, 0.1), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), 0.9, 0.35, 0.05)
    m.blob('Root', 'grass2', (0, 0, 0.15), (1.6, 1.6, 0.3), u=10, v=4)


def easter_egg_trio(m):
    """three painted eggs huddled in the grass"""
    setup(m, 'egg2', 'egg3', 'egg4', 'egg5', 'egg1', 'eggw', 'grass', 'grass2')
    painted_egg(m, (-0.7, 0, 0.75), 0.55, 'egg3', 'egg5', 'eggw', tilt=-8)
    painted_egg(m, (0.65, 0.1, 0.7), 0.5, 'egg2', 'egg1', 'egg3', tilt=10)
    painted_egg(m, (0.0, 0.55, 0.65), 0.45, 'egg4', 'egg2', 'eggw', tilt=4)
    for i in range(12):
        a = TAU * i / 12
        m.spike('Root', 'grass' if i % 2 else 'grass2', (math.cos(a) * 1.0, math.sin(a) * 0.8, 0.05), (math.cos(a) * 0.4, math.sin(a) * 0.4, 1), 0.6, 0.28, 0.04)


def bunny(m):
    """a big sitting bunny statue: round body, tall ears with pink insides, a cotton tail, holding an egg"""
    setup(m, 'fur', 'fur2', 'earpink', 'nose', 'eye', 'egg1', 'egg2', 'eggw', 'grass2')
    m.blob('Root', 'fur', (0, 0.15, 1.2), (1.1, 1.0, 1.15), u=10, v=8)
    m.blob('Root', 'fur2', (0, -0.55, 1.05), (0.7, 0.4, 0.75), u=8, v=6)   # tummy
    m.blob('Root', 'fur', (0, -0.2, 2.75), (0.78, 0.72, 0.68), u=10, v=8)   # head
    for s in (-1, 1):
        m.blob('Root', 'fur', (0.38 * s, -0.75, 2.6), (0.28, 0.22, 0.22), u=6, v=5)   # cheeks
        m.blob('Root', 'eye', (0.3 * s, -0.78, 2.95), (0.1, 0.06, 0.13), u=6, v=4)
        m.blob('Root', 'eggw', (0.33 * s, -0.83, 3.0), (0.035, 0.02, 0.04), u=4, v=3)
        ear = [(0.3 * s, -0.1, 3.3), (0.45 * s, -0.05, 4.2), (0.55 * s, 0.05, 4.9)]
        m.loft('Root', 'fur', ear, [(0.22, 0.1), (0.28, 0.12), (0.08, 0.06)], sides=6, steps=2, smooth=False, up=(0, -1, 0))
        m.loft('Root', 'earpink', [tuple(Vector(p) + Vector((0, -0.08, 0))) for p in ear], [(0.12, 0.04), (0.16, 0.05), (0.04, 0.03)],
               sides=6, steps=2, smooth=False, up=(0, -1, 0))
        m.blob('Root', 'fur', (0.75 * s, -0.3, 0.3), (0.38, 0.6, 0.28), u=7, v=4)   # feet
        m.blob('Root', 'fur2', (0.55 * s, -0.75, 1.55), (0.22, 0.3, 0.2), u=6, v=4)   # paws
    m.blob('Root', 'nose', (0, -0.9, 2.72), (0.1, 0.07, 0.08), u=5, v=4)
    m.blob('Root', 'eggw', (0, 1.15, 0.9), (0.35, 0.3, 0.33), u=7, v=5)   # tail
    painted_egg(m, (0, -1.0, 1.35), 0.38, 'egg1', 'egg2', 'eggw')
    m.blob('Root', 'grass2', (0, 0, 0.08), (1.4, 1.4, 0.15), u=10, v=4)


def egg_basket(m):
    """a woven basket of painted eggs with a ribbon on its handle"""
    setup(m, 'basket', 'basket2', 'grass', 'egg1', 'egg2', 'egg3', 'egg4', 'egg5', 'eggw', 'ribbon')
    m.loft('Root', 'basket', [(0, 0, 0.05), (0, 0, 0.9)], [(0.95, 0.95), (1.15, 1.15)], sides=12, steps=1, smooth=False)
    for z in (0.25, 0.55, 0.85):   # weave bands
        m.loft('Root', 'basket2', [(math.cos(TAU * i / 16) * (0.97 + z * 0.2), math.sin(TAU * i / 16) * (0.97 + z * 0.2), z) for i in range(17)],
               [(0.05, 0.07)] * 17, sides=4, steps=1, smooth=False, cap_round=0.0)
    m.blob('Root', 'grass', (0, 0, 0.92), (1.05, 1.05, 0.18), u=10, v=4)
    for k, (base, band, dots) in enumerate((('egg1', 'egg2', 'eggw'), ('egg3', 'egg5', 'eggw'), ('egg2', 'egg1', 'egg3'), ('egg4', 'egg5', 'eggw'))):
        a = TAU * k / 4 + 0.4
        painted_egg(m, (math.cos(a) * 0.5, math.sin(a) * 0.5, 1.2), 0.32, base, band, dots, tilt=15 * math.cos(a))
    m.loft('Root', 'basket2', [(-1.05, 0, 0.85), (-0.8, 0, 1.9), (0, 0, 2.35), (0.8, 0, 1.9), (1.05, 0, 0.85)], [(0.08, 0.1)] * 5,
           sides=5, steps=2, smooth=False, up=(0, -1, 0))
    for s in (-1, 1):
        m.blob('Root', 'ribbon', (0.22 * s, -0.08, 2.3), (0.25, 0.08, 0.15), rot=(0, 25 * s, 0), u=6, v=4)


def carrot_patch(m):
    """a little carrot patch: tilled soil with orange carrot tops and leafy greens"""
    setup(m, 'soil', 'carrotO', 'stemg', 'grass')
    m.box('Root', 'soil', (0, 0, 0.12), (3.2, 2.2, 0.24), bevel=0.08)
    rng = random.Random(31)
    for row in (-0.55, 0.0, 0.55):
        for k in range(5):
            x = -1.2 + 0.6 * k + rng.uniform(-0.1, 0.1)
            m.blob('Root', 'carrotO', (x, row, 0.28), (0.14, 0.14, 0.12), u=6, v=4)
            for j in range(3):
                a = j * 2.1 + rng.uniform(0, 1)
                m.spike('Root', 'stemg' if j % 2 else 'grass', (x, row, 0.3), (math.cos(a) * 0.4, math.sin(a) * 0.4, 1), 0.55, 0.16, 0.03)


def flower_arch(m):
    """the conveyor arch for spring: white trellis posts wrapped in flowers, a ribbon bow, painted eggs"""
    setup(m, 'archw', 'archw2', 'stemg', 'grass', 'petal', 'petal2', 'egg1', 'egg2', 'egg3', 'eggw', 'ribbon', 'ribbon2', 'egg5')
    rng = random.Random(41)
    W = 5.6
    for s in (-1, 1):
        x = W * s
        m.box('Root', 'archw', (x, 0, 3.3), (0.5, 0.5, 6.6), bevel=0.06)
        m.box('Root', 'archw2', (x, 0, 0.2), (1.0, 1.0, 0.4), bevel=0.06)
        for z in (1.2, 2.6, 4.0, 5.4):   # flowers climbing the posts
            for k in range(3):
                a = TAU * k / 3 + z
                c = Vector((x + math.cos(a) * 0.38, math.sin(a) * 0.38, z + 0.2 * k))
                m.blob('Root', 'petal' if k % 2 else 'petal2', tuple(c), (0.22, 0.22, 0.16), u=6, v=4)
                m.blob('Root', 'egg3', tuple(c + Vector((0, 0, 0.12))), (0.07, 0.07, 0.06), u=4, v=3)
        painted_egg(m, (x, 0, 7.5), 0.55, 'egg1' if s < 0 else 'egg2', 'egg5', 'eggw')
    # an arched top beam with a flower garland
    pts = [(-W, 0, 6.6)]
    for i in range(1, 12):
        t = i / 12
        pts.append((-W + 2 * W * t, 0, 6.6 + math.sin(math.pi * t) * 1.1))
    pts.append((W, 0, 6.6))
    m.loft('Root', 'archw', pts, [(0.25, 0.25)] * len(pts), sides=6, steps=2, smooth=False)
    for i, p in enumerate(pts[1:-1]):
        m.blob('Root', 'grass', (p[0], p[1] - 0.25, p[2] - 0.15), (0.4, 0.25, 0.3), u=6, v=4)
        m.blob('Root', ('petal', 'petal2', 'egg2', 'egg1')[i % 4], (p[0] + 0.1, p[1] - 0.45, p[2] - 0.1), (0.2, 0.12, 0.2), u=6, v=4)
    # the bow at the top
    for s in (-1, 1):
        m.blob('Root', 'ribbon', (0.45 * s, -0.3, 7.6), (0.55, 0.15, 0.35), rot=(0, 20 * s, 0), u=7, v=4)
        m.box('Root', 'ribbon', (0.25 * s, -0.3, 7.0), (0.18, 0.08, 0.9), rot=(0, 15 * s, 0), bevel=0.02)
    m.blob('Root', 'ribbon2', (0, -0.35, 7.6), (0.18, 0.15, 0.18), u=6, v=4)
    # a sign board under the beam
    m.box('Root', 'archw2', (0, -0.2, 5.3), (5.2, 0.2, 1.0), bevel=0.08)
    for s in (-1, 1):   # hung from the beam on ribbons
        cyl(m, 'ribbon2', (2.2 * s, -0.2, 7.3 - 0.5 * abs(s)), (2.2 * s, -0.2, 5.75), 0.05, sides=4)


PROPS = {
    'C_XmasTree': xmas_tree, 'C_Presents': presents, 'C_CandyCane': candy_cane, 'C_Snowman': snowman,
    'C_Sleigh': sleigh, 'C_Arch': xmas_arch,
    'E_EggBig': easter_egg_big, 'E_EggTrio': easter_egg_trio, 'E_Bunny': bunny, 'E_Basket': egg_basket,
    'E_Carrots': carrot_patch, 'E_Arch': flower_arch,
    'H_Pumpkin': pumpkin, 'H_PumpkinBig': pumpkin_big, 'H_PumpkinPile': pumpkin_pile,
    'H_GraveRound': grave_round, 'H_GraveCross': grave_cross, 'H_GraveSkull': grave_skull,
    'H_DeadTree': dead_tree, 'H_Cauldron': cauldron, 'H_Arch': halloween_arch, 'H_Cobweb': cobweb,
}
THEME_SETS = {'Halloween': [n for n in PROPS if n.startswith('H_')], 'Christmas': [n for n in PROPS if n.startswith('C_')],
              'Easter': [n for n in PROPS if n.startswith('E_')]}


def make(name):
    m = Monster(name)
    m.static = True
    m.bone('Root', (0, 0, 0), (0, 0, 1))
    PROPS[name](m)
    return m


names = []
for n in NAMES:
    names += THEME_SETS.get(n, [n])
NAMES = names

if LIVE:
    import bpy
    queue = list(NAMES)
    state = {'steps': None}

    def tick():
        with _view3d_override():
            while True:
                if state['steps'] is None:
                    if not queue:
                        print("LIVE ALL DONE")
                        return None
                    state['steps'] = make(queue.pop(0))._steps(OUT, True)
                try:
                    return next(state['steps'])
                except StopIteration:
                    state['steps'] = None
                    return 2.5   # admire it for a moment, then the next prop
    bpy.app.timers.register(tick, first_interval=1.5)
else:
    import bpy
    os.makedirs(OUT, exist_ok=True)
    out_lines = ["-- generated by monsters/season_props.py: each prop's size and light anchors in Blender units,",
                 "-- anchors relative to the mesh's bounding-box centre (Blender axes: x right, y back, z up)",
                 "return {"]
    for name in NAMES:
        m = make(name)
        m.build(OUT, live=False)
        ob = bpy.data.objects[name]
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        mid = (lo + hi) / 2
        size = hi - lo
        lights = ", ".join("{ kind = \"%s\", at = Vector3.new(%.3f, %.3f, %.3f), r = %.2f }" % (k, *(Vector(p) - mid), r)
                           for k, p, r in getattr(m, 'lights', []))
        out_lines.append("\t%s = { size = Vector3.new(%.3f, %.3f, %.3f), lights = { %s } }," % (name, size.x, size.y, size.z, lights))
        print("BUILT", name, "size", tuple(round(v, 2) for v in size))
    out_lines.append("}")
    with open(os.path.join(OUT, 'SeasonPropData.luau'), 'w') as f:
        f.write("\n".join(out_lines) + "\n")
    print("WROTE SeasonPropData.luau")
