"""Hard-edged machines and gear (static meshes, no rig), clean glossy colours, mostly flat faces:
    FusionMachine  industrial fusion rig: three glass input pods on top feed angular copper pipes
                   into a hexagonal reactor chamber at the front; hazard-striped base, vents, console
                   with buttons and a lever, square exhaust stacks, warning lights. ~8 x 5 x 7 units.
    FrostBite      ice bat: frosted steel handle, a barrel of jagged ice crystals, snowflake pommel
    SpeedCoil      handheld speed coil: grip, a squared-off spring of neon segments, a capped tip
    blender -b --factory-startup --python machines.py -- <out_dir> <FusionMachine|FrostBite|SpeedCoil> [--live]
FusionMachine faces -Y (the reactor door). Anchor points (design units) for in-game VFX are listed in
FUSION_ANCHORS."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Monster
from mathutils import Vector, Euler

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
args = [a for a in args if a != '--live']
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
WHAT = args[1] if len(args) > 1 else 'FusionMachine'
TAU = math.tau

FUSION_ANCHORS = {
    'Pod1': (-2.3, 0.9, 5.3), 'Pod2': (0.0, 0.9, 5.3), 'Pod3': (2.3, 0.9, 5.3),
    'Core': (0.0, -1.55, 2.6), 'Stack1': (-3.3, 1.9, 7.0), 'Stack2': (3.3, 1.9, 7.0),
}


def C(m, key, hexv):
    m.color(key, hexv, dots=False)


def prism(m, col, a, b, r, sides=6):
    """flat-sided prism from a to b (no smoothing - hard edges)"""
    up = (0, 0, 1) if abs(b[2] - a[2]) < 0.9 * math.dist(a, b) else (0, -1, 0)
    m.loft('Root', col, [a, b], [(r, r), (r, r)], sides=sides, steps=1, smooth=False, cap_round=0.0, up=up)


def pipe(m, col, pts, r=0.16):
    """angular pipe: straight runs between the points, a square collar at every joint"""
    for p, q in zip(pts, pts[1:]):
        prism(m, col, p, q, r, sides=6)
    for p in pts:
        m.box('Root', 'steel_dark', p, (r * 2.6, r * 2.6, r * 2.6), bevel=0.02)


def bolts(m, center, w, h, face_y, n=4):
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box('Root', 'bolt', (center[0] + sx * w / 2, face_y, center[2] + sz * h / 2), (0.14, 0.08, 0.14), bevel=0.02)


def fusion_machine(m):
    C(m, 'steel', '#5d6679'); C(m, 'steel_dark', '#363c4c'); C(m, 'steel_light', '#8c96ab'); C(m, 'bolt', '#c9cfdb')
    C(m, 'yellow', '#ffc928'); C(m, 'black', '#1d1f27'); C(m, 'copper', '#d07a32'); C(m, 'glass', '#8fe6ff')
    C(m, 'core', '#c35bff'); C(m, 'core2', '#f3d8ff'); C(m, 'red', '#ff3b3b'); C(m, 'green', '#3bff7a')
    C(m, 'orange', '#ff9a2e'); C(m, 'vent', '#22252f')
    # base platform with hazard stripes along the front and sides
    m.box('Root', 'steel_dark', (0, 0, 0.3), (8.4, 5.4, 0.6), bevel=0.05)
    n = 14
    for i in range(n):
        x = -4.2 + (i + 0.5) * 8.4 / n
        m.box('Root', 'yellow' if i % 2 == 0 else 'black', (x, -2.72, 0.32), (8.4 / n, 0.06, 0.5), rot=(0, 25, 0), bevel=0.0)
    # main body: a big box with stepped panels
    m.box('Root', 'steel', (0, 0.4, 2.3), (6.4, 3.6, 3.4), bevel=0.06)
    m.box('Root', 'steel_light', (0, 0.4, 4.1), (6.8, 4.0, 0.3), bevel=0.04)   # top deck
    for x in (-2.4, 2.4):
        m.box('Root', 'steel_dark', (x, -1.42, 2.3), (1.2, 0.1, 2.6), bevel=0.03)   # side panels
        bolts(m, (x, 0, 2.3), 0.9, 2.2, -1.48)
        for k in range(5):   # vent slots
            m.box('Root', 'vent', (x, -1.49, 1.4 + k * 0.42), (0.9, 0.06, 0.16), bevel=0.0)
    # reactor chamber out front: a hexagonal glass housing with a diamond core
    prism(m, 'steel_dark', (0, -1.55, 0.6), (0, -1.55, 1.0), 1.25, sides=6)
    prism(m, 'glass', (0, -1.55, 1.0), (0, -1.55, 3.9), 1.0, sides=6)
    prism(m, 'steel_dark', (0, -1.55, 3.9), (0, -1.55, 4.35), 1.25, sides=6)
    for k in range(6):   # frame posts at the hexagon corners
        a = k * TAU / 6
        m.box('Root', 'steel_light', (math.cos(a) * 1.08, -1.55 + math.sin(a) * 1.08, 2.45), (0.16, 0.16, 2.95), bevel=0.02)
    m.box('Root', 'core', (0, -1.55, 2.6), (0.85, 0.85, 0.85), rot=(45, 35, 0), bevel=0.02)
    m.box('Root', 'core2', (0, -1.55, 2.6), (0.45, 0.45, 0.45), rot=(10, 45, 30), bevel=0.01)
    for z in (1.3, 3.8):   # emitter rings above and below the core
        prism(m, 'copper', (0, -1.55, z - 0.07), (0, -1.55, z + 0.07), 0.62, sides=6)
    # three input pods on the top deck
    for i, x in enumerate((-2.3, 0.0, 2.3)):
        y = 0.9
        m.box('Root', 'steel_dark', (x, y, 4.42), (1.5, 1.5, 0.35), bevel=0.04)
        prism(m, 'glass', (x, y, 4.6), (x, y, 6.0), 0.6, sides=8)
        m.box('Root', 'steel_dark', (x, y, 6.15), (1.5, 1.5, 0.3), bevel=0.04)
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.box('Root', 'steel_light', (x + sx * 0.62, y + sy * 0.62, 5.3), (0.14, 0.14, 1.5), bevel=0.02)
        m.box('Root', 'orange', (x, y, 6.38), (0.35, 0.35, 0.18), bevel=0.02)   # status light
        # pipe from the pod down into the reactor top
        pipe(m, 'copper', [(x, y - 0.75, 4.75), (x, y - 1.6, 4.75), (x * 0.35, -1.55 + 0.6, 4.75), (x * 0.35, -1.55 + 0.6, 4.35)], 0.14)
    # control console on the right side, angled
    m.box('Root', 'steel', (4.0, -0.6, 1.3), (1.4, 1.6, 1.4), bevel=0.04)
    m.box('Root', 'steel_dark', (4.0, -0.75, 2.15), (1.5, 1.4, 0.25), rot=(-25, 0, 0), bevel=0.03)
    for k, col in enumerate(('red', 'green', 'yellow', 'orange')):
        m.box('Root', col, (3.62 + k * 0.26, -0.85, 2.3), (0.16, 0.16, 0.1), rot=(-25, 0, 0), bevel=0.02)
    m.box('Root', 'steel_light', (4.45, -0.35, 2.7), (0.1, 0.1, 0.9), rot=(-20, 0, 0), bevel=0.01)   # lever
    m.box('Root', 'red', (4.45, -0.5, 3.15), (0.24, 0.24, 0.24), bevel=0.02)
    # square exhaust stacks at the back corners
    for x in (-3.3, 3.3):
        m.box('Root', 'steel_dark', (x, 1.9, 5.0), (0.8, 0.8, 4.0), bevel=0.04)
        m.box('Root', 'steel_light', (x, 1.9, 7.05), (1.0, 1.0, 0.25), bevel=0.03)
        for z in (3.6, 4.6, 5.6):
            m.box('Root', 'yellow' if z != 4.6 else 'black', (x, 1.9, z), (0.86, 0.86, 0.18), bevel=0.0)
    # warning lights on the top deck corners
    for x in (-3.2, 3.2):
        m.box('Root', 'red', (x, -1.4, 4.45), (0.3, 0.3, 0.4), bevel=0.03)
    # back cable runs
    pipe(m, 'steel_dark', [(-3.3, 1.9, 3.0), (-3.3, 2.35, 3.0), (3.3, 2.35, 3.0), (3.3, 1.9, 3.0)], 0.12)


def frost_bite(m):
    C(m, 'steel', '#9fb4cc'); C(m, 'grip', '#2d5c9e'); C(m, 'grip2', '#4f86d6'); C(m, 'ice', '#a8f0ff')
    C(m, 'ice2', '#e6fcff'); C(m, 'ice3', '#5fc8ff'); C(m, 'dark', '#2a3242')
    # snowflake pommel: a flat six-armed star
    for k in range(6):
        a = k * TAU / 6
        m.box('Root', 'ice', (0.12 * math.cos(a), 0.12 * math.sin(a), 0.05), (0.26, 0.07, 0.07), rot=(0, 0, math.degrees(a)), bevel=0.01)
    m.box('Root', 'dark', (0, 0, 0.14), (0.26, 0.26, 0.14), bevel=0.02)
    # taped grip (square section, alternating bands)
    for i in range(9):
        z = 0.2 + i * 0.11
        m.box('Root', 'grip' if i % 2 == 0 else 'grip2', (0, 0, z + 0.055), (0.24, 0.24, 0.11), rot=(0, 0, 45 * (i % 2)), bevel=0.01)
    # steel shaft flaring out (8-sided, flat faced)
    m.loft('Root', 'steel', [(0, 0, 1.2), (0, 0, 2.3), (0, 0, 3.6)], [(0.13, 0.13), (0.24, 0.24), (0.3, 0.3)], sides=8, steps=1, smooth=False, cap_round=0.0, up=(0, -1, 0))
    m.box('Root', 'dark', (0, 0, 1.2), (0.34, 0.34, 0.1), bevel=0.01)
    # jagged ice crystals bursting out of the barrel
    import random
    rng = random.Random(4)
    for k in range(16):
        a = k * TAU / 8 + (0.3 if k >= 8 else 0)
        z = 2.4 + (k // 8) * 0.6 + rng.uniform(-0.1, 0.1)
        d = (math.cos(a), math.sin(a), rng.uniform(0.2, 0.7))
        m.spike('Root', 'ice' if k % 3 else 'ice3', (0.24 * math.cos(a), 0.24 * math.sin(a), z), d, rng.uniform(0.35, 0.55), 0.13, twist=45, snap=False)
    m.spike('Root', 'ice2', (0, 0, 3.6), (0, 0, 1), 0.7, 0.26, twist=45, snap=False)
    for k in range(4):
        a = k * TAU / 4 + 0.4
        m.spike('Root', 'ice', (0.16 * math.cos(a), 0.16 * math.sin(a), 3.55), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), 0.45, 0.12, twist=45, snap=False)


def speed_coil(m):
    C(m, 'grip', '#2b2f3c'); C(m, 'metal', '#9aa3b8'); C(m, 'neon', '#5bff8f'); C(m, 'neon2', '#d6ffe4'); C(m, 'cap', '#ff4a6a')
    m.box('Root', 'metal', (0, 0, 0.08), (0.34, 0.34, 0.16), bevel=0.02)
    m.box('Root', 'grip', (0, 0, 0.6), (0.26, 0.26, 0.9), bevel=0.03)
    for z in (0.3, 0.6, 0.9):
        m.box('Root', 'metal', (0, 0, z), (0.3, 0.3, 0.05), bevel=0.0)
    m.box('Root', 'metal', (0, 0, 1.12), (0.42, 0.42, 0.14), bevel=0.02)
    m.box('Root', 'metal', (0, 0, 1.75), (0.12, 0.12, 1.3), bevel=0.01)   # core rod
    # squared-off spring: straight neon segments around a square helix
    turns, per = 5, 4
    pts = []
    for i in range(turns * per + 1):
        a = i * TAU / per + TAU / 8
        pts.append((0.32 * math.cos(a) * 1.41, 0.32 * math.sin(a) * 1.41, 1.2 + i * 1.2 / (turns * per)))
    for p, q in zip(pts, pts[1:]):
        m.loft('Root', 'neon', [p, q], [(0.05, 0.05), (0.05, 0.05)], sides=4, steps=1, smooth=False, cap_round=0.0)
    m.box('Root', 'neon2', (0, 0, 1.8), (0.2, 0.2, 0.9), rot=(0, 0, 45), bevel=0.0)
    m.box('Root', 'cap', (0, 0, 2.48), (0.46, 0.46, 0.16), bevel=0.02)
    m.spike('Root', 'cap', (0, 0, 2.56), (0, 0, 1), 0.3, 0.2, twist=45, snap=False)


def cosmic_vial(m):
    """The Cosmic Mutation vial, matched to the user's icon: dark chamfered caps with gold horn spikes and
    glowing purple tops, gold bands with big four-point gold stars set with purple gems, a glass tube
    holding a purple-pink galaxy swirl and star sparkles, a tilted glowing orbit ring and floating
    purple crystals. About 2.6 units tall, standing on Z = 0."""
    C(m, 'cap', '#1e1f33'); C(m, 'cap2', '#2c2e4a'); C(m, 'gold', '#e8b84a'); C(m, 'gold2', '#ffd978')
    C(m, 'gem', '#8a3cff'); C(m, 'gem2', '#c99cff'); C(m, 'glass', '#3a2fa8'); C(m, 'haze', '#7a3cff'); C(m, 'nebula', '#b45cff')
    C(m, 'nebula2', '#ff8ce0'); C(m, 'core', '#fff2ff'); C(m, 'star', '#ffffff'); C(m, 'ring', '#a46cff')
    C(m, 'crystal', '#6a3ae0'); C(m, 'crystal2', '#9d74ff'); C(m, 'glowtop', '#b47cff')
    zb, zt = 0.62, 2.0    # glass from zb to zt

    def cap(z0, up):
        """dark octagonal cap block + gold band + spikes + glowing end, mirrored by `up` (+1 top, -1 bottom)"""
        zc = z0 + up * 0.22
        prism(m, 'cap', (0, 0, z0), (0, 0, z0 + up * 0.44), 0.62, sides=8)
        prism(m, 'cap2', (0, 0, z0 + up * 0.44), (0, 0, z0 + up * 0.56), 0.5, sides=8)
        prism(m, 'glowtop', (0, 0, z0 + up * 0.56), (0, 0, z0 + up * 0.62), 0.34, sides=8)
        prism(m, 'gold', (0, 0, z0 - up * 0.02), (0, 0, z0 + up * 0.1), 0.66, sides=8)   # gold band at the glass edge
        for k in range(4):   # gold horn spikes at the corners, curving out
            a = k * TAU / 4 + TAU / 8
            base = (0.5 * math.cos(a), 0.5 * math.sin(a), z0 + up * 0.4)
            m.spike('Root', 'gold', base, (0.55 * math.cos(a), 0.55 * math.sin(a), up * 1.0), 0.32, 0.12, snap=False)
        # big four-point gold star ornament with a purple gem, front and back
        for y in (-1, 1):
            c = (0, y * 0.64, zc)
            for d, L in (((0, 0, 1), 0.42), ((0, 0, -1), 0.42), ((1, 0, 0), 0.34), ((-1, 0, 0), 0.34)):
                m.spike('Root', 'gold2', c, d, L, 0.16, snap=False, twist=45)
            m.box('Root', 'gold', c, (0.26, 0.1, 0.26), rot=(0, 45, 0), bevel=0.02)
            m.box('Root', 'gem', (0, y * 0.69, zc), (0.17, 0.06, 0.17), rot=(0, 45, 0), bevel=0.01)
            m.box('Root', 'gem2', (0, y * 0.72, zc + 0.03), (0.06, 0.03, 0.06), rot=(0, 45, 0), bevel=0.0)

    cap(zb, -1)
    cap(zt, 1)
    # glass tube with the galaxy inside
    prism(m, 'glass', (0, 0, zb), (0, 0, zt), 0.5, sides=12)
    zm = (zb + zt) / 2
    # spiral galaxy: two arms of glowing chips swirling round a bright core, facing the front
    m.blob('Root', 'haze', (0, -0.4, zm), (0.42, 0.06, 0.6), u=10, v=6)        # purple nebula glow
    m.blob('Root', 'nebula2', (0, -0.44, zm), (0.26, 0.05, 0.34), u=10, v=6)   # pink inner glow
    m.blob('Root', 'core', (0, -0.48, zm), (0.13, 0.04, 0.13), u=8, v=5)        # bright core
    for arm in range(2):
        for i in range(12):
            t = i / 11
            a = arm * math.pi + t * 3.4
            r = 0.08 + 0.36 * t
            x, z = r * math.cos(a), zm + r * math.sin(a) * 1.4
            m.box('Root', 'core' if i < 3 else 'nebula2' if i % 2 else 'nebula', (x, -0.5, z),
                  (0.2 * (1 - 0.55 * t), 0.03, 0.1 * (1 - 0.4 * t)), rot=(0, -math.degrees(a) - 70, 0), bevel=0.0)
    for x, z, s_ in ((-0.28, zm + 0.45, 0.1), (0.3, zm - 0.4, 0.09), (0.22, zm + 0.5, 0.07), (-0.3, zm - 0.45, 0.07), (0.05, zm + 0.62, 0.05)):
        for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):   # four-point star sparkles
            m.spike('Root', 'star', (x, -0.48, z), d, s_, s_ * 0.45, snap=False, twist=45)
    # tilted glowing orbit ring round the middle
    pts = []
    for i in range(25):
        a = i / 24 * TAU
        p = Vector((1.05 * math.cos(a), 0.55 * math.sin(a), 0))
        p.rotate(Euler((math.radians(12), math.radians(-18), 0)))
        pts.append((p.x, p.y, p.z + zm))
    m.loft('Root', 'ring', pts, [(0.045, 0.03)] * len(pts), sides=5, steps=1, smooth=False)
    # floating purple crystals
    for x, y, z, s_ in ((-0.95, -0.2, zm + 0.35, 1.0), (0.98, -0.1, zm - 0.25, 0.9), (-0.8, 0.1, zm - 0.6, 0.7),
                        (0.85, 0.2, zm + 0.6, 0.75), (-1.15, -0.3, zm - 0.05, 0.5), (1.15, -0.25, zm + 0.15, 0.45)):
        m.spike('Root', 'crystal', (x, y, z), (0, 0, 1), 0.2 * s_, 0.12 * s_, snap=False, twist=45)
        m.spike('Root', 'crystal2', (x, y, z), (0, 0, -1), 0.2 * s_, 0.12 * s_, snap=False, twist=45)


m = Monster(WHAT)
m.static = True
{'FusionMachine': fusion_machine, 'FrostBite': frost_bite, 'SpeedCoil': speed_coil, 'CosmicVial': cosmic_vial}[WHAT](m)
m.build(OUT)
