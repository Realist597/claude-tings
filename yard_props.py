"""Monster yard props (static meshes) in the monsters' chunky low-poly, dotted-fabric style.
    blender -b --factory-startup --python yard_props.py -- <out_dir> <Name> [<Name> ...]
    blender --factory-startup --python yard_props.py -- <out_dir> <Name> [<Name> ...] --live
(--live builds them one after another in the open window so you can watch; it doesn't export.)

The yard is a forest sanctuary: mossy boulder walls topped with a pointed log palisade, a log gate
arch with a hanging sign, trees, bushes, flowers, glowing mushrooms, a lily pond, hay, a feeding
trough, a giant straw nest, a thatched shelter and lantern posts.

Units: 1 Blender unit ~ 2.2 studs after import. Walls run along X with their inside facing -Y.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from kit import Monster, _view3d_override

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LIVE = '--live' in args
args = [a for a in args if a != '--live']
THEME = None   # --theme Halloween|Christmas|Easter: same props (same shapes and UVs), seasonal colours
if '--theme' in args:
    i = args.index('--theme')
    THEME = args[i + 1]
    del args[i:i + 2]
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
NAMES = args[1:] or ['YardWall']
TAU = math.tau

PALETTE = dict(
    rock='#8d8f99', rock2='#a3a5ae', rock3='#74767f', moss='#6fae3f', moss2='#8cc456',
    wood='#a8703c', wood2='#8a5a2e', woodend='#e0b77c', bark='#6e4626', rope='#d9c08a',
    leaf='#5fa83a', leaf2='#7cc44a', leaf3='#4a8f2e', pine='#3f7d3a', pine2='#53964a',
    straw='#e8c868', straw2='#d1ab4a', water='#58b7e8', water2='#7fd0f2', lily='#66b94a',
    red='#e2493f', pink='#f08bb8', yellow='#ffd84a', white='#f6f3ea', purple='#a576e0',
    glow='#7ef5e8', glowstem='#e8f0e0', lamp='#ffd27a', metal='#4b4d57', sign='#c99155',
)


# seasonal re-skins: the same props with these colours swapped in. Shapes, seeds and texture layout
# don't change, so a themed texture drops straight onto the existing meshes (ThemeService swaps it).
THEMES = {
    'Halloween': dict(leaf='#e8742a', leaf2='#f2a33a', leaf3='#c94a24', red='#8a4ad0', pine='#33424c', pine2='#4c3f6c',
                      moss='#7a8a3a', moss2='#9a8a3a', lily='#8a6a2a', water='#5a2a8a', water2='#7a4aaa', yellow='#ff8a1a',
                      pink='#8a4ad0', purple='#4a2a6a', white='#e8e0d0', glow='#b06aff', glowstem='#d8c8f0', lamp='#ff9a2a',
                      metal='#2a2430', straw='#c8a048', straw2='#a8802a', rope='#b8a070', sign='#8a5a3a'),
    'Christmas': dict(leaf='#eef4fb', leaf2='#ffffff', leaf3='#d6e4f2', red='#e2323a', pine='#2f6a3a', pine2='#f2f6fb',
                      moss='#e8f0f8', moss2='#ffffff', lily='#bcd8ea', water='#a8d8f0', water2='#d8f0fa', yellow='#ffd23a',
                      pink='#e2323a', purple='#2f8a4a', white='#ffffff', glow='#9ad8ff', lamp='#ffcf6a', straw='#e8d8a0',
                      rock='#9aa4b4', rock2='#b8c2d0', rock3='#7c8696'),
    'Easter': dict(leaf='#ffb4d8', leaf2='#ffe2f0', leaf3='#ff96c8', red='#ffffff', pine='#6ac87a', pine2='#8ee09a',
                   moss='#9ae07a', moss2='#b8f090', yellow='#fff07a', pink='#ff9ad0', purple='#c8a0ff', white='#ffffff',
                   glow='#ffc8f0', lamp='#fff0a0', water='#7ad8f0', lily='#8ad87a', straw='#f8e098'),
}
if THEME:
    PALETTE.update(THEMES[THEME])


def setup(m, *keys):
    for k in keys:
        m.color(k, PALETTE[k], dots=True)


def cyl(m, col, a, b, r, sides=8, smooth=False, cap=0.0, r1=None):
    a, b = Vector(a), Vector(b)
    up = (0, 0, 1) if abs(b.z - a.z) < 0.9 * (b - a).length else (0, -1, 0)
    r1 = r if r1 is None else r1
    m.loft('Root', col, [tuple(a), tuple(b)], [(r, r), (r1, r1)], sides=sides, steps=1, smooth=smooth, cap_round=cap, up=up)


def rock(m, rng, center, size, cols=('rock', 'rock2', 'rock3')):
    sx, sy, sz = size
    m.blob('Root', rng.choice(cols), center, (sx, sy, sz), rot=(rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(0, 360)),
           u=7, v=5, smooth=False)


def moss_cap(m, rng, center, r):
    m.blob('Root', rng.choice(('moss', 'moss2')), center, (r, r * 0.85, r * 0.32), rot=(0, 0, rng.uniform(0, 360)), u=8, v=4, smooth=False)


def log_post(m, rng, x, y, z0, z1, r, col=None, point=True):
    col = col or rng.choice(('wood', 'wood2'))
    cyl(m, col, (x, y, z0), (x, y, z1), r, sides=7)
    if point:
        cyl(m, col, (x, y, z1), (x, y, z1 + r * 1.7), r, r1=0.03, sides=7)
    else:
        m.disc('Root', 'woodend', (x, y, z1 + 0.01), (0, 0, 1), r * 0.8, depth=0.02, segments=7)


def lantern(m, center, s=1.0):
    c = Vector(center)
    m.lights = getattr(m, "lights", []) + [("lamp", tuple(c), 1.0 * s)]
    m.box('Root', 'metal', tuple(c + Vector((0, 0, 0.42 * s))), (0.5 * s, 0.5 * s, 0.1 * s), bevel=0.02)
    m.box('Root', 'lamp', tuple(c), (0.36 * s, 0.36 * s, 0.6 * s), bevel=0.04)
    m.box('Root', 'metal', tuple(c - Vector((0, 0, 0.36 * s))), (0.46 * s, 0.46 * s, 0.1 * s), bevel=0.02)
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        m.box('Root', 'metal', tuple(c + Vector((0.19 * s * dx, 0.19 * s * dy, 0))), (0.06 * s, 0.06 * s, 0.7 * s), bevel=0.0)
    cyl(m, 'metal', tuple(c + Vector((0, 0, 0.47 * s))), tuple(c + Vector((0, 0, 0.62 * s))), 0.05 * s, sides=6)


def leaf_ball(m, rng, center, r, cols=('leaf', 'leaf2', 'leaf3')):
    m.blob('Root', rng.choice(cols), center, (r, r * rng.uniform(0.9, 1.1), r * rng.uniform(0.8, 0.95)),
           rot=(0, 0, rng.uniform(0, 360)), u=8, v=6, smooth=False)


# ------------------------------------------------------------------ the props

def yard_wall(m):
    """7.4 long wall segment: mossy boulders with a pointed log palisade on top (tiles along X)."""
    setup(m, 'rock', 'rock2', 'rock3', 'moss', 'moss2', 'wood', 'wood2', 'rope', 'woodend')
    rng = random.Random(7)
    x = -3.9
    while x < 3.9:
        r = rng.uniform(0.85, 1.25)
        rock(m, rng, (x, rng.uniform(-0.1, 0.15), r * 0.75), (r * 1.1, 0.9, r * 0.95))
        if rng.random() < 0.55:
            moss_cap(m, rng, (x + rng.uniform(-0.2, 0.2), -0.1, r * 0.75 + r * 0.8), r * 0.75)
        x += r * 1.25
    # a second, smaller row on top so the palisade sits in rock
    x = -3.6
    while x < 3.7:
        r = rng.uniform(0.55, 0.8)
        rock(m, rng, (x, 0.05, 2.0 + r * 0.3), (r * 1.2, 0.75, r * 0.8))
        x += r * 1.5
    n = 12
    for i in range(n):
        px = -3.7 + 7.4 * (i + 0.5) / n
        top = 5.4 + rng.uniform(-0.35, 0.35)
        log_post(m, rng, px, 0.12, 1.9, top, 0.31)
    for z in (3.3, 4.75):
        cyl(m, 'wood2', (-3.75, -0.25, z), (3.75, -0.25, z), 0.16, sides=6)
        for i in range(0, n, 3):
            px = -3.7 + 7.4 * (i + 0.5) / n
            cyl(m, 'rope', (px, -0.38, z - 0.2), (px, -0.38, z + 0.2), 0.1, sides=6)


def yard_post(m):
    """corner pillar: stacked boulders, a thick log post and a lantern on top"""
    setup(m, 'rock', 'rock2', 'rock3', 'moss', 'moss2', 'wood', 'wood2', 'woodend', 'metal', 'lamp')
    rng = random.Random(11)
    z = 0
    for r in (1.35, 1.15, 0.95):
        rock(m, rng, (0, 0, z + r * 0.7), (r * 1.15, r * 1.1, r * 0.8))
        z += r * 1.15
    moss_cap(m, rng, (0.1, 0, z + 0.25), 0.9)
    cyl(m, 'wood', (0, 0, z - 0.4), (0, 0, z + 3.2), 0.42, sides=8)
    m.disc('Root', 'woodend', (0, 0, z + 3.21), (0, 0, 1), 0.34, depth=0.02, segments=8)
    m.box('Root', 'wood2', (0, -0.55, z + 2.9), (0.2, 1.1, 0.2), bevel=0.03)
    cyl(m, 'metal', (0, -1.0, z + 2.8), (0, -1.0, z + 2.45), 0.03, sides=5)
    lantern(m, (0, -1.0, z + 2.05), 1.0)


def yard_gate(m):
    """doorway arch: two big log posts, a crossbeam with a leafy garland, a hanging sign, lanterns"""
    setup(m, 'wood', 'wood2', 'woodend', 'bark', 'rope', 'sign', 'leaf', 'leaf2', 'leaf3', 'red', 'yellow',
          'metal', 'lamp', 'rock', 'rock2', 'rock3', 'moss')
    rng = random.Random(3)
    for s in (-1, 1):
        rock(m, rng, (3.7 * s, 0, 0.5), (1.0, 1.0, 0.7))
        cyl(m, 'wood', (3.7 * s, 0, 0.0), (3.7 * s, 0, 6.6), 0.48, sides=8)
        m.disc('Root', 'woodend', (3.7 * s, 0, 6.61), (0, 0, 1), 0.4, depth=0.02, segments=8)
        for z in (1.6, 4.2):
            cyl(m, 'rope', (3.7 * s, 0, z - 0.15), (3.7 * s, 0, z + 0.15), 0.52, sides=8)
        # hanging lanterns at the beam ends
        cyl(m, 'metal', (4.55 * s, -0.2, 6.0), (4.55 * s, -0.2, 5.6), 0.03, sides=5)
        lantern(m, (4.55 * s, -0.2, 5.2), 0.9)
    cyl(m, 'wood2', (-4.7, 0, 6.15), (4.7, 0, 6.15), 0.4, sides=8)
    for s in (-1, 1):
        m.disc('Root', 'woodend', (4.71 * s, 0, 6.15), (s, 0, 0), 0.33, depth=0.02, segments=8)
    cyl(m, 'wood', (-4.0, 0.05, 6.9), (4.0, 0.05, 6.9), 0.28, sides=7)
    # garland of leaves and berries along the beam
    for i in range(14):
        x = -3.9 + 7.8 * i / 13
        leaf_ball(m, rng, (x, -0.35, 6.0 + 0.18 * math.sin(i * 1.3)), 0.38)
        if i % 3 == 1:
            m.blob('Root', 'red' if i % 2 else 'yellow', (x + 0.15, -0.65, 5.85), (0.12, 0.12, 0.12), u=6, v=4, smooth=True)
    # hanging sign (the game writes on it)
    for s in (-1, 1):
        cyl(m, 'rope', (1.8 * s, -0.1, 5.8), (1.8 * s, -0.1, 4.95), 0.05, sides=5)
    m.box('Root', 'sign', (0, -0.1, 4.45), (4.6, 0.22, 1.15), bevel=0.06)
    m.box('Root', 'wood2', (0, -0.1, 5.0), (4.8, 0.26, 0.16), bevel=0.03)
    m.box('Root', 'wood2', (0, -0.1, 3.9), (4.8, 0.26, 0.16), bevel=0.03)


def oak_tree(m):
    setup(m, 'bark', 'wood2', 'leaf', 'leaf2', 'leaf3', 'red')
    rng = random.Random(21)
    m.loft('Root', 'bark', [(0, 0, -0.1), (0, 0, 1.2), (0.15, 0.05, 3.0), (0.1, 0, 4.6)],
           [(0.75, 0.75), (0.48, 0.48), (0.42, 0.42), (0.34, 0.34)], sides=8, steps=3, smooth=False)
    for a in range(5):   # root flares
        ang = TAU * a / 5 + 0.3
        d = Vector((math.cos(ang), math.sin(ang), 0))
        m.loft('Root', 'bark', [tuple(d * 0.3 + Vector((0, 0, 0.6))), tuple(d * 1.0 + Vector((0, 0, 0.05)))],
               [(0.28, 0.28), (0.14, 0.14)], sides=6, steps=1, smooth=False)
    for ang, z, ln in ((0.4, 3.4, 1.6), (2.6, 3.8, 1.4), (4.4, 3.1, 1.5)):
        d = Vector((math.cos(ang), math.sin(ang), 0.7)).normalized()
        a = Vector((0, 0, z))
        cyl(m, 'bark', tuple(a), tuple(a + d * ln), 0.22, r1=0.12, sides=6)
    for c, r in (((0, 0, 5.6), 2.2), ((1.5, 0.6, 4.9), 1.6), ((-1.5, 0.4, 5.0), 1.7), ((0.4, -1.5, 4.8), 1.5),
                 ((-0.3, 1.4, 5.0), 1.5), ((0.2, 0.1, 6.8), 1.4)):
        leaf_ball(m, rng, c, r)
    for _ in range(8):
        ang = rng.uniform(0, TAU)
        m.blob('Root', 'red', (math.cos(ang) * 1.9, math.sin(ang) * 1.9, rng.uniform(4.6, 6.2)), (0.14, 0.14, 0.14), u=6, v=4)


def pine_tree(m):
    setup(m, 'bark', 'pine', 'pine2', 'white')
    m.loft('Root', 'bark', [(0, 0, -0.1), (0, 0, 2.0)], [(0.5, 0.5), (0.36, 0.36)], sides=7, steps=1, smooth=False)
    z = 1.3
    for i, (r, h) in enumerate(((2.3, 2.4), (1.9, 2.2), (1.5, 2.0), (1.05, 1.8), (0.6, 1.5))):
        cyl(m, 'pine' if i % 2 == 0 else 'pine2', (0, 0, z), (0, 0, z + h), r, r1=0.05, sides=7)
        z += h * 0.58


def bush(m):
    setup(m, 'leaf', 'leaf2', 'leaf3', 'red', 'purple')
    rng = random.Random(5)
    for c, r in (((0, 0, 0.75), 0.95), ((0.8, 0.2, 0.55), 0.7), ((-0.75, 0.1, 0.55), 0.72), ((0.1, -0.6, 0.5), 0.6), ((0.1, 0.7, 0.5), 0.6)):
        leaf_ball(m, rng, c, r)
    berry = rng.choice(('red', 'purple'))
    for _ in range(9):
        ang = rng.uniform(0, TAU)
        m.blob('Root', berry, (math.cos(ang) * 0.95, math.sin(ang) * 0.85, rng.uniform(0.45, 1.25)), (0.1, 0.1, 0.1), u=6, v=4)


def flower_patch(m):
    setup(m, 'leaf', 'leaf2', 'leaf3', 'pink', 'yellow', 'white', 'red', 'purple')
    rng = random.Random(9)
    for _ in range(14):   # grass tufts
        x, y = rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1)
        for k in range(3):
            ang = rng.uniform(0, TAU)
            tip = Vector((x + math.cos(ang) * 0.15, y + math.sin(ang) * 0.15, rng.uniform(0.35, 0.6)))
            cyl(m, rng.choice(('leaf', 'leaf2', 'leaf3')), (x, y, 0), tuple(tip), 0.06, r1=0.01, sides=4)
    for _ in range(7):
        x, y = rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)
        h = rng.uniform(0.5, 0.85)
        cyl(m, 'leaf3', (x, y, 0), (x, y, h), 0.035, sides=4)
        petal = rng.choice(('pink', 'white', 'red', 'purple'))
        for k in range(5):
            ang = TAU * k / 5
            m.blob('Root', petal, (x + math.cos(ang) * 0.13, y + math.sin(ang) * 0.13, h), (0.11, 0.07, 0.03),
                   rot=(0, 0, math.degrees(ang)), u=6, v=3, smooth=True)
        m.blob('Root', 'yellow', (x, y, h + 0.02), (0.07, 0.07, 0.05), u=6, v=3)


def mushrooms(m):
    """glowcap cluster (the game adds the glow) plus two red toadstools"""
    setup(m, 'glow', 'glowstem', 'white', 'red', 'moss', 'moss2')
    rng = random.Random(13)
    moss_cap(m, rng, (0, 0, 0.05), 1.1)
    for x, y, h, r, cap in ((0, 0, 1.4, 0.6, 'glow'), (0.7, 0.35, 0.95, 0.42, 'glow'), (-0.55, 0.45, 0.8, 0.36, 'glow'),
                            (0.35, -0.7, 0.7, 0.4, 'red'), (-0.6, -0.45, 0.55, 0.3, 'red')):
        cyl(m, 'glowstem', (x, y, 0), (x, y, h), r * 0.32, r1=r * 0.26, sides=6, smooth=True)
        m.blob('Root', cap, (x, y, h), (r, r, r * 0.55), u=9, v=5, smooth=True)
        if cap == 'glow':
            m.lights = getattr(m, "lights", []) + [("glow", (x, y, h), r)]
        for k in range(3):
            ang = rng.uniform(0, TAU)
            m.blob('Root', 'white', (x + math.cos(ang) * r * 0.55, y + math.sin(ang) * r * 0.55, h + r * 0.32), (r * 0.14, r * 0.14, r * 0.06), u=6, v=3)


def stump(m):
    setup(m, 'bark', 'woodend', 'wood2', 'moss', 'moss2', 'red', 'white')
    rng = random.Random(17)
    cyl(m, 'bark', (0, 0, 0), (0, 0, 1.1), 0.95, r1=0.82, sides=9)
    m.disc('Root', 'woodend', (0, 0, 1.11), (0, 0, 1), 0.78, depth=0.02, segments=9)
    for r in (0.55, 0.32):
        cyl(m, 'wood2', (0, 0, 1.115), (0, 0, 1.125), r, sides=9)
        m.disc('Root', 'woodend', (0, 0, 1.13), (0, 0, 1), r - 0.06, depth=0.01, segments=9)
    for a in range(5):
        ang = TAU * a / 5
        d = Vector((math.cos(ang), math.sin(ang), 0))
        m.loft('Root', 'bark', [tuple(d * 0.7 + Vector((0, 0, 0.5))), tuple(d * 1.45 + Vector((0, 0, 0.02)))],
               [(0.26, 0.26), (0.1, 0.1)], sides=6, steps=1, smooth=False)
    moss_cap(m, rng, (0.6, 0.3, 0.6), 0.5)
    m.blob('Root', 'red', (-0.7, -0.6, 0.35), (0.22, 0.22, 0.12), u=8, v=4)
    cyl(m, 'white', (-0.7, -0.6, 0.0), (-0.7, -0.6, 0.33), 0.07, sides=5)


def fallen_log(m):
    setup(m, 'bark', 'woodend', 'wood2', 'moss', 'moss2', 'glow', 'glowstem')
    rng = random.Random(19)
    m.loft('Root', 'bark', [(-2.4, 0, 0.62), (0, 0.1, 0.6), (2.4, 0, 0.58)], [(0.62, 0.62), (0.6, 0.6), (0.56, 0.56)],
           sides=9, steps=3, smooth=False, cap_round=0.0, up=(0, 0, 1))
    for s, r in ((-1, 0.5), (1, 0.46)):
        m.disc('Root', 'woodend', (2.42 * s, 0, 0.6), (s, 0, 0), r, depth=0.02, segments=9)
        m.disc('Root', 'wood2', (2.43 * s, 0, 0.6), (s, 0, 0), r * 0.5, depth=0.02, segments=9)
    for x in (-1.2, 0.4, 1.6):
        moss_cap(m, rng, (x, 0, 1.12), 0.6)
    for x, y in ((0.9, -0.55), (1.2, -0.45)):
        cyl(m, 'glowstem', (x, y, 0.55), (x, y - 0.25, 0.75), 0.06, sides=5)
        m.blob('Root', 'glow', (x, y - 0.28, 0.78), (0.2, 0.2, 0.1), u=8, v=4)
        m.lights = getattr(m, "lights", []) + [("glow", (x, y - 0.28, 0.78), 0.2)]


def hay_bale(m):
    setup(m, 'straw', 'straw2', 'rope')
    rng = random.Random(23)
    m.box('Root', 'straw', (0, 0, 0.62), (2.2, 1.3, 1.24), bevel=0.22, segs=2)
    for x in (-0.55, 0.55):
        m.box('Root', 'rope', (x, 0, 0.62), (0.1, 1.36, 1.3), bevel=0.04)
    for _ in range(16):   # loose straws
        p = Vector((rng.uniform(-1.05, 1.05), rng.choice((-0.66, 0.66)), rng.uniform(0.2, 1.1)))
        d = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))).normalized() * 0.35
        cyl(m, 'straw2', tuple(p), tuple(p + d), 0.03, sides=4)


def trough(m):
    setup(m, 'wood', 'wood2', 'water', 'red', 'leaf2', 'metal')
    rng = random.Random(29)
    for s in (-1, 1):
        m.box('Root', 'wood', (0, 0.62 * s, 0.85), (3.2, 0.18, 0.75), rot=(8 * s, 0, 0), bevel=0.04)
        m.box('Root', 'wood2', (1.62 * s, 0, 0.85), (0.18, 1.3, 0.75), bevel=0.04)
        for t in (-1, 1):
            m.box('Root', 'wood2', (1.35 * s, 0.55 * t, 0.3), (0.2, 0.2, 0.6), rot=(0, 10 * s, 0), bevel=0.03)
        m.box('Root', 'metal', (1.2 * s, 0, 1.24), (0.08, 1.45, 0.06), bevel=0.0)
    m.box('Root', 'wood2', (0, 0, 0.5), (3.2, 1.1, 0.14), bevel=0.03)
    m.box('Root', 'water', (0, 0, 1.0), (3.05, 1.1, 0.06), bevel=0.0)
    for _ in range(6):   # apples and cabbages floating in it
        m.blob('Root', rng.choice(('red', 'leaf2')), (rng.uniform(-1.2, 1.2), rng.uniform(-0.35, 0.35), 1.08), (0.17, 0.17, 0.15), u=7, v=4)


def nest(m):
    """giant straw nest: two woven rims, twigs poking out every way, three big speckled eggs"""
    setup(m, 'straw', 'straw2', 'wood2', 'bark', 'white', 'water2', 'pink', 'yellow')
    rng = random.Random(31)
    for R, z, rad, col in ((2.15, 0.55, (0.95, 0.72), 'straw'), (1.9, 1.15, (0.62, 0.45), 'straw2')):
        pts, radii = [], []
        for i in range(19):
            ang = TAU * i / 18
            wob = 1 + 0.05 * math.sin(ang * 5)
            pts.append((math.cos(ang) * R * wob, math.sin(ang) * R * wob, z + 0.08 * math.sin(ang * 3)))
            radii.append(rad)
        m.loft('Root', col, pts, radii, sides=8, steps=2, smooth=False, cap_round=0.0)
    m.blob('Root', 'straw2', (0, 0, 0.25), (2.1, 2.1, 0.35), u=12, v=4, smooth=False)
    for _ in range(46):   # twigs poking out
        ang = rng.uniform(0, TAU)
        R = rng.uniform(1.9, 2.3)
        p = Vector((math.cos(ang) * R, math.sin(ang) * R, rng.uniform(0.3, 1.4)))
        d = Vector((math.cos(ang + rng.uniform(-1.3, 1.3)), math.sin(ang + rng.uniform(-1.3, 1.3)), rng.uniform(-0.4, 0.7))).normalized()
        cyl(m, rng.choice(('wood2', 'bark', 'straw2', 'straw')), tuple(p - d * 0.6), tuple(p + d * rng.uniform(0.5, 1.1)), 0.055, sides=4)
    for x, y, c in ((-0.6, 0.25, 'white'), (0.6, 0.4, 'water2'), (0.05, -0.65, 'pink')):
        m.blob('Root', c, (x, y, 1.05), (0.55, 0.55, 0.78), u=10, v=7, smooth=True)
        for _ in range(4):   # speckles
            ang = rng.uniform(0, TAU)
            m.blob('Root', 'yellow' if c != 'white' else 'pink',
                   (x + math.cos(ang) * 0.5, y + math.sin(ang) * 0.5, 1.05 + rng.uniform(-0.2, 0.35)), (0.09, 0.09, 0.09), u=6, v=3)


def pond(m):
    """irregular lily pond with a rock rim, lily pads, a flower and cattails"""
    setup(m, 'water', 'water2', 'rock', 'rock2', 'rock3', 'moss', 'moss2', 'lily', 'pink', 'yellow', 'leaf3', 'bark')
    rng = random.Random(37)
    m.blob('Root', 'water', (0, 0, 0.05), (3.6, 2.6, 0.08), u=16, v=3, smooth=False)
    m.blob('Root', 'water2', (-0.8, 0.4, 0.07), (1.4, 0.9, 0.06), u=12, v=3, smooth=False)
    for i in range(22):   # rim rocks
        ang = TAU * i / 22 + rng.uniform(-0.08, 0.08)
        r = rng.uniform(0.38, 0.62)
        rock(m, rng, (math.cos(ang) * 3.75, math.sin(ang) * 2.75, r * 0.35), (r * 1.2, r, r * 0.6))
        if rng.random() < 0.3:
            moss_cap(m, rng, (math.cos(ang) * 3.75, math.sin(ang) * 2.75, r * 0.7), r * 0.6)
    for x, y, r in ((1.2, -0.5, 0.45), (-1.6, -0.9, 0.38), (0.3, 1.1, 0.42), (1.9, 0.8, 0.32), (-0.4, -0.2, 0.3)):
        m.disc('Root', 'lily', (x, y, 0.15), (0, 0, 1), r, depth=0.04, segments=9)
    m.blob('Root', 'pink', (1.2, -0.5, 0.25), (0.18, 0.18, 0.12), u=8, v=4)
    m.blob('Root', 'yellow', (1.2, -0.5, 0.33), (0.07, 0.07, 0.05), u=6, v=3)
    for x, y in ((-3.0, 1.4), (-2.7, 1.8), (-3.3, 1.1), (2.9, -1.6)):
        h = rng.uniform(1.3, 1.9)
        cyl(m, 'leaf3', (x, y, 0), (x + 0.1, y, h), 0.04, sides=4)
        cyl(m, 'bark', (x + 0.1, y, h - 0.45), (x + 0.1, y, h - 0.05), 0.09, sides=6, cap=0.4)


def shelter(m):
    """little A-frame barn: log frame, layered thatch roof with a ridge log, plank back wall, hay
    and a water bowl inside. Opens toward -Y."""
    setup(m, 'wood', 'wood2', 'woodend', 'straw', 'straw2', 'rope', 'water', 'bark')
    rng = random.Random(41)
    for x in (-1.9, 1.9):
        for y in (-1.6, 1.6):
            log_post(m, rng, x, y, 0, 1.6, 0.18, col='wood', point=False)
    for y in (-1.6, 1.6):
        log_post(m, rng, 0, y, 0, 3.5, 0.2, col='wood2', point=False)
    for x in (-1.9, 1.9):
        cyl(m, 'wood2', (x, -2.0, 1.6), (x, 2.0, 1.6), 0.14, sides=6)
    cyl(m, 'bark', (0, -2.35, 3.62), (0, 2.35, 3.62), 0.2, sides=7)
    for s in (-1, 1):
        m.disc('Root', 'woodend', (0, 2.36 * s, 3.62), (0, s, 0), 0.17, depth=0.02, segments=7)
    # thatch: four overlapping rows a side, running down from the ridge
    top, eave = Vector((0, 0, 3.6)), Vector((2.55, 0, 1.3))
    L = (eave - top).length
    theta = math.atan2(top.z - eave.z, eave.x - top.x)
    rows = 4
    for s in (-1, 1):
        slope = Vector((s * math.cos(theta), 0, -math.sin(theta)))
        normal = Vector((s * math.sin(theta), 0, math.cos(theta)))
        for k in range(rows):
            c = top + slope * (L * (k + 0.5) / rows) + normal * (0.12 + 0.06 * k)
            m.box('Root', 'straw' if k % 2 == 0 else 'straw2', tuple(c), (L / rows * 1.35, 4.5, 0.3),
                  rot=(0, math.degrees(theta) * s, 0), bevel=0.1)
        # ragged fringe along the eave
        for j in range(9):
            y = -2.1 + 4.2 * j / 8
            tip = top + slope * (L + 0.25) + normal * 0.2 + Vector((0, y, 0))
            cyl(m, 'straw2', tuple(tip - slope * 0.4), tuple(tip + Vector((0, 0, -0.35))), 0.12, r1=0.03, sides=4)
    # plank back wall under the roof line
    x = -1.8
    while x <= 1.81:
        h = 1.6 + (1.9 - abs(x)) / 1.9 * 1.85
        m.box('Root', rng.choice(('wood', 'wood2')), (x, 1.68, h / 2), (0.42, 0.14, h), bevel=0.03)
        x += 0.45
    # hay and a water bowl inside
    m.box('Root', 'straw', (0.7, 0.6, 0.35), (1.5, 1.0, 0.7), bevel=0.18, segs=2)
    m.box('Root', 'rope', (0.7, 0.6, 0.35), (0.08, 1.04, 0.74), bevel=0.02)
    m.box('Root', 'straw2', (0.9, 0.65, 0.95), (1.2, 0.8, 0.55), rot=(0, 0, 18), bevel=0.15, segs=2)
    m.blob('Root', 'straw2', (-0.4, 0.2, 0.05), (1.6, 1.3, 0.12), u=10, v=3, smooth=False)
    cyl(m, 'wood2', (-1.0, -0.6, 0), (-1.0, -0.6, 0.35), 0.5, r1=0.55, sides=9)
    m.disc('Root', 'water', (-1.0, -0.6, 0.33), (0, 0, 1), 0.45, depth=0.02, segments=9)


def lantern_post(m):
    setup(m, 'wood', 'wood2', 'woodend', 'metal', 'lamp', 'rock', 'rock2', 'rock3')
    rng = random.Random(43)
    rock(m, rng, (0, 0, 0.25), (0.6, 0.55, 0.4))
    cyl(m, 'wood', (0, 0, 0), (0, 0, 3.6), 0.2, sides=7)
    m.disc('Root', 'woodend', (0, 0, 3.61), (0, 0, 1), 0.16, depth=0.02, segments=7)
    m.box('Root', 'wood2', (0, -0.45, 3.35), (0.14, 0.95, 0.14), bevel=0.02)
    cyl(m, 'metal', (0, -0.82, 3.28), (0, -0.82, 3.0), 0.03, sides=5)
    lantern(m, (0, -0.82, 2.62), 0.85)


def path_stones(m):
    setup(m, 'rock', 'rock2', 'rock3', 'moss')
    rng = random.Random(47)
    for x, y in ((-1.4, 0.2), (-0.3, -0.25), (0.8, 0.15), (1.8, -0.2), (0.3, 0.95), (-1.0, -1.0)):
        r = rng.uniform(0.45, 0.65)
        m.blob('Root', rng.choice(('rock', 'rock2', 'rock3')), (x, y, 0.06), (r * 1.2, r, 0.12), rot=(0, 0, rng.uniform(0, 360)), u=8, v=3, smooth=False)


PROPS = {
    'YardWall': yard_wall, 'YardPost': yard_post, 'YardGate': yard_gate, 'OakTree': oak_tree, 'PineTree': pine_tree,
    'Bush': bush, 'FlowerPatch': flower_patch, 'Mushrooms': mushrooms, 'Stump': stump, 'FallenLog': fallen_log,
    'HayBale': hay_bale, 'Trough': trough, 'Nest': nest, 'Pond': pond, 'Shelter': shelter, 'LanternPost': lantern_post,
    'PathStones': path_stones,
}


def make(name):
    m = Monster(name)
    m.static = True
    m.bone('Root', (0, 0, 0), (0, 0, 1))
    PROPS[name](m)
    return m


if NAMES == ['all']:
    NAMES = list(PROPS)

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
    out_lines = ["-- generated by monsters/yard_props.py: each prop's size and light anchors in Blender units,",
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
    out_lines.append("}")
    if not THEME:
        dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game2', 'src', 'ServerStorage', 'MonsterTools', 'YardPropData.luau')
        with open(dst, 'w') as f:
            f.write("\n".join(out_lines) + "\n")
        print("WROTE", dst)
