"""Treadmills, take two: five tiers in the game's chunky, studded, toy-brick style, upgrading in
material and decoration (same deck anatomy every tier so the game's moving belt lines up):
    1 Wooden Jogger    plank deck, log rails, rope-wrapped handlebar, a lantern, leafy tufts
    2 Stone Strider    mossy brick deck and pillars, ivy, rubble round the base
    3 Golden Runner    gold-trimmed brick deck, green vines curling round it, purple-grey rocks
    4 Crystal Dash     frosted silver deck with glowing crystal clusters growing off it
    5 Mythic Inferno   obsidian deck split by lava cracks, horns, fire spikes and a molten core
Every tier has a console up front with a screen and chunky coloured buttons, handlebars, and a rear
roller. Runner faces -Y toward the console; deck 3 wide x 5.6 long; belt marker as in gear.py.
    blender -b --factory-startup --python treadmills.py -- <out_dir> <Treadmill1..5|TreadmillBelt|all> [--live]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True
from mathutils import Vector
from kit import Monster, _view3d_override

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LIVE = '--live' in args
args = [a for a in args if a != '--live']
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export', 'treadmills')
NAMES = args[1:] or ['all']
TAU = math.tau
BELT = dict(center=(0, 0.45, 0.66), size=(2.2, 4.5, 0.06))   # same as gear.py


def col(m, key, hexv, dots=True):
    m.color(key, hexv, dots=dots)


def cyl(m, c, a, b, r, sides=8, r1=None):
    a, b = Vector(a), Vector(b)
    up = (0, 0, 1) if abs(b.z - a.z) < 0.9 * (b - a).length else (0, -1, 0)
    r1 = r if r1 is None else r1
    m.loft('Root', c, [tuple(a), tuple(b)], [(r, r), (r1, r1)], sides=sides, steps=1, smooth=False, up=up)


def tube(m, c, pts, r, sides=6):
    m.loft('Root', c, pts, [(r, r)] * len(pts), sides=sides, steps=2, smooth=False)


# ------------------------------------------------------------------ shared anatomy

def deck(m, main, trim, recess, rail, bricks=None, rng=None):
    """the plinth, the belt recess, side rails with caps, the rear roller"""
    m.box('Root', main, (0, 0.3, 0.3), (3.1, 5.7, 0.5), bevel=0.08)
    m.box('Root', trim, (0, 0.3, 0.04), (3.3, 5.9, 0.12), bevel=0.04)          # foot plate
    m.box('Root', recess, (0, 0.45, 0.6), (2.25, 4.6, 0.04), bevel=0.0)
    for s in (-1, 1):
        m.box('Root', rail, (1.38 * s, 0.42, 0.68), (0.44, 4.7, 0.3), bevel=0.06)
        m.box('Root', trim, (1.38 * s, 0.42, 0.86), (0.5, 4.8, 0.08), bevel=0.02)
        for y in (-1.8, 2.65):   # chunky corner caps
            m.box('Root', trim, (1.38 * s, y, 0.9), (0.6, 0.5, 0.22), bevel=0.05)
    cyl(m, trim, (-1.12, 2.82, 0.52), (1.12, 2.82, 0.52), 0.18, sides=8)
    for s in (-1, 1):   # raised toy-brick studs along the rail tops
        for k in range(8):
            cyl(m, trim, (1.38 * s, -1.55 + k * 0.6, 0.9), (1.38 * s, -1.55 + k * 0.6, 1.0), 0.11, sides=8)
    if bricks:   # brick courses along the plinth's sides and back
        for s in (-1, 1):
            for row, z in enumerate((0.18, 0.42)):
                y = -2.5 + (0.32 if row else 0)
                while y < 3.0:
                    w = 0.62
                    m.box('Root', rng.choice(bricks), (1.56 * s, y + w / 2, z), (0.06, w - 0.06, 0.2), bevel=0.0)
                    y += w


def console(m, frame, panel, screen, buttons, post=None, z=2.35):
    """two posts, a slanted panel with a glowing screen and a grid of chunky coloured buttons"""
    post = post or frame
    for s in (-1, 1):
        m.box('Root', post, (1.2 * s, -2.35, 1.35), (0.34, 0.34, 2.0), rot=(-8, 0, 0), bevel=0.06)
    m.box('Root', frame, (0, -2.55, z), (2.9, 0.75, 0.95), rot=(28, 0, 0), bevel=0.12)
    m.box('Root', screen, (0, -2.43, z + 0.12), (1.1, 0.06, 0.5), rot=(28, 0, 0), bevel=0.0)
    for i, b in enumerate(buttons):
        x = -1.05 + 0.3 * (i % 3) if i < 3 else 0.45 + 0.3 * ((i - 3) % 3)
        row = 0 if i in (0, 1, 2, 3, 4, 5) else 1
        m.box('Root', b, (x if i < 3 else x, -2.47 + 0.0 * row, z - 0.08 + 0.05 * (i % 2)), (0.27, 0.16, 0.24), rot=(28, 0, 0), bevel=0.04)
    m.box('Root', panel, (0, -2.75, z - 0.42), (2.7, 0.5, 0.18), bevel=0.04)
    for k in range(4):   # studs along the console's top edge
        cyl(m, frame, (-1.05 + k * 0.7, -2.72, z + 0.42), (-1.05 + k * 0.7, -2.72, z + 0.53), 0.12, sides=8)


def handles(m, bar, grip, y=-2.0, z=2.55, half=1.38):
    tube(m, bar, [(-half, y, z), (half, y, z)], 0.09)
    for s in (-1, 1):
        tube(m, bar, [(half * s, y, z), (half * s, y + 1.2, z - 0.25), (half * s, y + 1.35, 1.0)], 0.09)
        cyl(m, grip, (half * s, y + 0.15, z - 0.03), (half * s, y + 0.9, z - 0.18), 0.13, sides=8)


def rocks(m, rng, cols, n=7, r=(0.35, 0.6), ring=(2.0, 3.1)):
    for i in range(n):
        s = -1 if i % 2 else 1
        x = s * rng.uniform(1.75, 2.15)
        y = rng.uniform(-2.6, 3.1)
        rr = rng.uniform(r[0] * 1.2, r[1] * 1.3)
        m.blob('Root', rng.choice(cols), (x, y, rr * 0.45), (rr * 1.1, rr * 1.2, rr * 0.75),
               rot=(0, 0, rng.uniform(0, 360)), u=6, v=4, smooth=False)


def vine(m, rng, leaf, stem, start, length=6, step=0.5, wobble=0.35, up=0.1):
    p = Vector(start)
    pts = [tuple(p)]
    a = rng.uniform(0, TAU)
    for i in range(length):
        a += rng.uniform(-1.1, 1.1)
        p = p + Vector((math.cos(a) * wobble, step * (1 if start[1] < 0.5 else -1) * rng.uniform(0.4, 1), up + rng.uniform(-0.05, 0.12)))
        side = 1 if start[0] >= 0 else -1   # keep off the belt: hug the outside of the rails
        if abs(p.x) < 1.6 and abs(p.y - 0.45) < 2.4:
            p = Vector((1.6 * side, p.y, p.z))
        pts.append(tuple(p))
        if i % 2 == 1:
            m.spike('Root', leaf, tuple(p), (math.cos(a + 1.5), math.sin(a + 1.5), 0.4), 0.38, 0.22, 0.03)
    tube(m, stem, pts, 0.05, sides=4)


# ------------------------------------------------------------------ the five tiers

def wooden(m):
    for k, v in dict(wood='#c18a52', wood2='#9c6a3a', wood3='#7a4f2a', rope='#d9c08a', leaf='#6cbf3a', leaf2='#8ad84e',
                     screen='#9ae6ff', iron='#4a4652', lamp='#ffd27a', red='#e6453a', yellow='#ffd23a', green='#5ad24a', recess='#3a2a1e').items():
        col(m, k, v)
    rng = random.Random(1)
    deck(m, 'wood2', 'wood3', 'recess', 'wood')
    for i in range(9):   # planks across the plinth top, gaps between
        m.box('Root', 'wood' if i % 2 else 'wood2', (0, -2.4 + i * 0.62, 0.56), (3.05, 0.54, 0.06), rot=(0, rng.uniform(-1.5, 1.5), 0), bevel=0.02)
    for s in (-1, 1):   # log rails with end rings
        cyl(m, 'wood', (1.38 * s, -2.0, 0.9), (1.38 * s, 2.8, 0.9), 0.2, sides=8)
        for y in (-2.0, 2.8):
            m.box('Root', 'wood3', (1.38 * s, y, 0.9), (0.3, 0.06, 0.3), bevel=0.0)
    console(m, 'wood', 'wood3', 'screen', ['red', 'yellow', 'green', 'green', 'red', 'yellow'], post='wood2')
    handles(m, 'wood3', 'rope')
    for s in (-1, 1):   # rope wraps
        for k in range(4):
            cyl(m, 'rope', (1.38 * s, -1.75 + k * 0.22, 2.48 - k * 0.05), (1.38 * s, -1.65 + k * 0.22, 2.46 - k * 0.05), 0.12, sides=6)
    # a little lantern hung off the console
    m.box('Root', 'iron', (1.6, -2.7, 2.7), (0.08, 0.08, 0.5), bevel=0.0)
    m.box('Root', 'lamp', (1.6, -2.7, 2.25), (0.28, 0.28, 0.36), bevel=0.04)
    m.box('Root', 'iron', (1.6, -2.7, 2.48), (0.36, 0.36, 0.08), bevel=0.02)
    for x, y in ((-1.7, 2.9), (1.6, 3.0), (-1.75, -1.0)):
        for k in range(5):
            a = k * TAU / 5
            m.spike('Root', 'leaf' if k % 2 else 'leaf2', (x, y, 0.1), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), 0.55, 0.25, 0.04)


def stone(m):
    for k, v in dict(stone='#9a9aa6', stone2='#7e7e8c', stone3='#b4b4c0', moss='#6aa83a', moss2='#86c24e', ivy='#4f8f2e',
                     screen='#7af0d0', red='#e6453a', yellow='#ffd23a', blue='#4aa8ff', recess='#3a3a46', rock='#8c8a96', rock2='#6c6a78').items():
        col(m, k, v)
    rng = random.Random(2)
    deck(m, 'stone2', 'stone', 'recess', 'stone3', bricks=['stone', 'stone2', 'stone3'], rng=rng)
    console(m, 'stone3', 'stone2', 'screen', ['red', 'yellow', 'blue', 'blue', 'red', 'yellow'], post='stone')
    handles(m, 'stone2', 'moss2')
    for s in (-1, 1):   # square pillars beside the console, capped with moss
        m.box('Root', 'stone', (1.7 * s, -2.4, 1.1), (0.55, 0.55, 2.2), bevel=0.06)
        m.box('Root', 'stone3', (1.7 * s, -2.4, 2.28), (0.7, 0.7, 0.18), bevel=0.04)
        m.blob('Root', 'moss', (1.7 * s, -2.4, 2.42), (0.38, 0.38, 0.12), u=7, v=3)
    for _ in range(6):   # moss patches on the deck edge
        m.blob('Root', rng.choice(('moss', 'moss2')), (rng.uniform(-1.5, 1.5), rng.uniform(-2.5, 2.9), 0.58), (0.3, 0.25, 0.08), u=6, v=3)
    for start in ((1.6, -2.2, 0.2), (-1.6, 2.6, 0.2), (1.55, 1.2, 0.3)):
        vine(m, rng, 'ivy', 'ivy', start, length=5)
    rocks(m, rng, ['rock', 'rock2'], n=8)


def golden(m):
    for k, v in dict(gold='#ffc21f', gold2='#e8a010', gold3='#ffd95a', brick='#d89a2a', brick2='#c08020', vine='#3fbf3a',
                     leaf='#5ae04a', leaf2='#2f9f2e', screen='#ff5a8a', red='#ff4a4a', yellow='#ffe14a', green='#4ad24a',
                     recess='#5a3a12', rock='#9c96b4', rock2='#7c7894').items():
        col(m, k, v)
    rng = random.Random(3)
    deck(m, 'gold2', 'gold3', 'recess', 'gold', bricks=['brick', 'brick2', 'gold2'], rng=rng)
    console(m, 'gold', 'gold2', 'screen', ['red', 'yellow', 'green', 'red', 'green', 'yellow'], post='gold2')
    handles(m, 'gold3', 'gold2')
    for s in (-1, 1):   # gold studs along the rails
        for k in range(6):
            m.box('Root', 'gold3', (1.38 * s, -1.5 + k * 0.8, 0.98), (0.2, 0.2, 0.08), bevel=0.02)
    for start in ((1.55, -2.3, 0.3), (-1.55, -2.3, 0.4), (1.6, 2.9, 0.2), (-1.6, 2.9, 0.25)):
        vine(m, rng, rng.choice(('leaf', 'leaf2')), 'vine', start, length=7, up=0.05 if start[2] < 1 else -0.2)
    for x in (-1.2, 1.2):   # vines curling up the console posts
        pts = [(x + 0.22 * math.cos(i), -2.35 + 0.22 * math.sin(i), 0.4 + i * 0.25) for i in range(9)]
        tube(m, 'vine', pts, 0.05, sides=4)
    rocks(m, rng, ['rock', 'rock2'], n=9)


def crystal(m):
    for k, v in dict(silver='#dfe8f5', silver2='#b8c6dc', frost='#c8f0ff', ice='#9ee0ff', crystal='#7af2ff', crystal2='#c49aff',
                     crystal3='#ffffff', screen='#9afff0', blue='#3a9aff', pink='#ff7ad8', white='#ffffff', recess='#2a3a5a').items():
        col(m, k, v)
    rng = random.Random(4)
    deck(m, 'silver2', 'silver', 'recess', 'frost', bricks=['ice', 'frost', 'silver'], rng=rng)
    console(m, 'silver', 'silver2', 'screen', ['blue', 'pink', 'white', 'pink', 'blue', 'white'], post='frost')
    handles(m, 'silver', 'ice')
    # crystal clusters growing off the corners and the console top
    for (x, y, z, k) in ((1.75, 2.9, 0.1, 1.2), (-1.75, 2.8, 0.1, 1.0), (1.8, -2.0, 0.1, 0.9), (-1.8, -1.9, 0.1, 1.1), (0, -2.75, 2.85, 0.8)):
        for i in range(5):
            a = rng.uniform(0, TAU)
            d = (math.cos(a) * 0.45, math.sin(a) * 0.45, 1)
            m.spike('Root', rng.choice(('crystal', 'crystal2', 'crystal')), (x + math.cos(a) * 0.15, y + math.sin(a) * 0.15, z),
                    d, (0.7 + 0.5 * rng.random()) * k, 0.26 * k, twist=rng.uniform(0, 45), snap=False)
        m.spike('Root', 'crystal3', (x, y, z), (0, 0, 1), 0.9 * k, 0.16 * k, snap=False)
    for s in (-1, 1):   # frosted icicles hanging off the rails
        for k in range(5):
            m.spike('Root', 'ice', (1.6 * s, -1.6 + k * 1.0, 0.55), (0, 0, -1), 0.35, 0.1, snap=False)


def mythic(m):
    for k, v in dict(obsidian='#2a2236', obsidian2='#3c3050', obsidian3='#1c1626', lava='#ff6a1a', lava2='#ffc23a',
                     horn='#e8dcc8', ember='#ff3a2a', screen='#ff8a2a', red='#ff3a2a', orange='#ff9a1a', yellow='#ffe14a',
                     recess='#140c18', rock='#3a2a3a').items():
        col(m, k, v)
    rng = random.Random(5)
    deck(m, 'obsidian2', 'obsidian', 'recess', 'obsidian3', bricks=['obsidian', 'obsidian2', 'obsidian3'], rng=rng)
    # lava cracks running over the plinth and up the rails
    for s in (-1, 1):
        pts = [(1.57 * s, y, 0.3 + 0.12 * math.sin(y * 3)) for y in (-2.6, -1.6, -0.6, 0.4, 1.4, 2.4, 3.0)]
        tube(m, 'lava', pts, 0.06, sides=4)
        pts = [(1.38 * s + 0.12 * math.sin(y * 4), y, 0.97) for y in (-1.8, -0.8, 0.2, 1.2, 2.2)]
        tube(m, 'lava2', pts, 0.04, sides=4)
    console(m, 'obsidian2', 'obsidian3', 'screen', ['red', 'orange', 'yellow', 'orange', 'red', 'yellow'], post='obsidian')
    handles(m, 'obsidian', 'lava')
    for s in (-1, 1):   # curling horns off the console and fire spikes at the back corners
        pts = [(1.45 * s, -2.6, 2.6), (1.9 * s, -2.4, 3.2), (2.1 * s, -2.0, 3.6), (1.9 * s, -1.7, 3.8)]
        m.loft('Root', 'horn', pts, [(0.2, 0.2), (0.15, 0.15), (0.09, 0.09), (0.03, 0.03)], sides=6, steps=2, smooth=False)
        for k in range(3):
            m.spike('Root', 'lava' if k % 2 else 'lava2', (1.4 * s, 2.7, 0.9), ((0.5 - 0.5 * k) * s, 0.3, 1), 0.9 + 0.3 * k, 0.24, snap=False)
    # a molten core on the console, and glowing rubble
    m.blob('Root', 'lava2', (0, -2.7, 3.0), (0.32, 0.32, 0.32), u=8, v=6)
    m.blob('Root', 'lava', (0, -2.7, 3.0), (0.42, 0.42, 0.42), u=8, v=6)
    for _ in range(7):
        a, d = rng.uniform(0, TAU), rng.uniform(2.0, 3.0)
        p = (math.cos(a) * d * 0.62, 0.3 + math.sin(a) * d, 0.2)
        m.blob('Root', 'rock', p, (0.45, 0.4, 0.3), rot=(0, 0, rng.uniform(0, 360)), u=6, v=4)
        m.blob('Root', 'ember', (p[0], p[1], 0.42), (0.18, 0.18, 0.08), u=5, v=3)


TIERS = {'Treadmill1': wooden, 'Treadmill2': stone, 'Treadmill3': golden, 'Treadmill4': crystal, 'Treadmill5': mythic}


def make(name):
    m = Monster(name)
    m.static = True
    m.bone('Root', (0, 0, 0), (0, 0, 1))
    if name == 'TreadmillBelt':
        m.color('belt', '#2a2c3a')
        m.box('Root', 'belt', BELT['center'], BELT['size'], bevel=0.0)
    else:
        TIERS[name](m)
    return m


if NAMES == ['all']:
    NAMES = list(TIERS) + ['TreadmillBelt']

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
                    return 2.5
    bpy.app.timers.register(tick, first_interval=1.5)
else:
    os.makedirs(OUT, exist_ok=True)
    for name in NAMES:
        make(name).build(OUT, live=False)
        print("BUILT", name)
