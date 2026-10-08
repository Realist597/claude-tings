"""Frost Penguin - Common Frost Peaks penguin: an upright waddler with flippers, orange beak and
feet, a red knitted scarf and a tuft of ice crystals. Chicks are fluffy and grey. Waddles when it
walks and belly-slides when it runs. Faces -Y.
    blender -b --python penguin.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Crest (ice tuft sparkle)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('FrostPenguin', {
    'body': '#232b42', 'belly': '#f4f7ff', 'fluff': '#8f99ad', 'cheek': '#ffcf4a', 'beak': '#ff9a2e', 'beak2': ('#d8641a', True, True),
    'foot': ('#ff8a2a', False), 'scarf': '#e2413f', 'scarf2': '#ffffff', 'ice': ('#8ff0ff', False),
    'plate': ('#6fb8ea', True, True), 'tooth': ('#ffffff', False), 'dark': ('#0d1222', False),
    'eye_dark': ('#0d1222', False), 'iris': ('#2ee8ff', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.35, eye=1.5), 'Teen': dict(head=1.12, eye=1.2)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
chick = st['stage'] == 'Child'
SIDES = (('L', 1), ('R', -1))
coat = 'fluff' if chick else 'body'

# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0, 0.6), (0, 0, 2.0), 'MonsterRoot')
m.bone('Chest', (0, 0, 2.0), (0, 0, 3.1), 'Hips')
headZ = 3.4 + 0.45 * (h - 1)
m.bone('Head', (0, 0, 3.1), (0, -0.9, headZ + 0.4), 'Chest')
m.bone('Tail', (0, 0.9, 0.6), (0, 1.5, 0.35), 'Hips')
for side, s in SIDES:
    m.bone(f'Flipper{side}', (1.12 * s, 0, 2.75), (1.55 * s, 0.1, 1.35), 'Chest')
    m.bone(f'Foot{side}', (0.5 * s, 0, 0.35), (0.5 * s, -0.75, 0.08), 'Hips')

# ---------------- body ----------------
# chunky style: a chiselled studded body, a boxy head with an angry ice brow and glowing eyes, a big
# toothy beak, an ice crown, ice-armour shoulder pads and blade-edged flippers
m.loft(['Hips', 'Chest', 'Head'], coat,
       [(0, 0.05, 0.3), (0, 0.05, 1.1), (0, 0.0, 2.0), (0, -0.05, 2.85), (0, -0.05, headZ + 0.2)],
       [(0.78, 0.68), (1.32, 1.15), (1.4, 1.24), (1.12, 1.0), (0.85 * h, 0.82 * h)],
       sides=7, steps=3, smooth=False, up=(0, -1, 0))
m.blob(['Hips', 'Chest'], 'belly', (0, -0.48, 1.7), (1.1, 0.85, 1.5), u=7, v=5, smooth=False)
# head
m.box('Head', coat, (0, -0.1, headZ + 0.35), (1.8 * h, 1.7 * h, 1.6 * h), bevel=0.26 * h, segs=1,
      taper=dict(axis='z', end=1, scale=(0.86, 0.9)))
for side, s in SIDES:
    m.box('Head', 'belly', (0.38 * s * h, -0.82 * h, headZ + 0.4), (0.62 * h, 0.12 * h, 0.6 * h), bevel=0.05 * h)
    if not chick:
        m.box('Head', 'cheek', (0.86 * s * h, -0.3 * h, headZ + 0.12), (0.12 * h, 0.5 * h, 0.4 * h), bevel=0.04 * h)
    m.box('Head', 'dark', (0.4 * s * h, -0.88 * h, headZ + 0.45), (0.5 * h, 0.06 * h, 0.42 * h), bevel=0.03 * h)
    m.eye('Head', (0.4 * s * h, -0.92 * h, headZ + 0.45), (0.3 * s, -1, 0.05), 0.24 * h * st['eye'])
    # angry ice brow: low over the inner corner
    m.box('Head', 'plate', (0.42 * s * h, -0.92 * h, headZ + 0.76), (0.62 * h, 0.16 * h, 0.15 * h), rot=(0, -20 * s, 0), bevel=0.03 * h)
# big beak with a row of little teeth along the upper half
m.box('Head', 'beak', (0, -1.25 * h, headZ + 0.14), (0.8 * h, 0.85 * h, 0.32 * h), bevel=0.06 * h,
      taper=dict(axis='y', end=-1, scale=(0.45, 0.6)))
m.box('Head', 'beak2', (0, -1.18 * h, headZ - 0.12), (0.66 * h, 0.7 * h, 0.2 * h), bevel=0.05 * h,
      taper=dict(axis='y', end=-1, scale=(0.45, 0.6)))
m.spike('Head', 'beak', (0, -1.62 * h, headZ + 0.16), (0, -0.5, -1), 0.22 * h, 0.16 * h, 0.1 * h, snap=False)
for i in range(3):
    for side, s in SIDES:
        m.spike('Head', 'tooth', ((0.12 + 0.1 * i) * s * h, (-1.4 + 0.18 * i) * h, headZ + 0.0), (0, 0, -1), 0.14 * h, 0.07 * h, snap=False)
# a crown of ice crystals
for i, (x, y, k) in enumerate(((0, 0, 1.0), (-0.3, 0.05, 0.75), (0.3, 0.05, 0.75), (-0.5, 0.2, 0.5), (0.5, 0.2, 0.5))):
    m.spike('Head', 'ice', (x * h, y, headZ + 1.0 * h), (x * 1.4, 0.35, 1), (0.35 + 0.45 * g) * k * h, 0.24 * h, twist=45)
m.socket('Crest', 'Head', (0, 0.1, headZ + 1.7 * h))

if chick:
    # fluffy down poking out everywhere
    for a in range(10):
        ang = a * TAU / 10
        z = 1.1 + 0.8 * (a % 3)
        m.spike(['Hips', 'Chest'][a % 2], 'fluff', (math.cos(ang) * 1.2, math.sin(ang) * 1.05, z),
                (math.cos(ang), math.sin(ang), 0.4), 0.4, 0.3, 0.2)
else:
    # knitted scarf with stripes and a dangling end
    ring = []
    for i in range(9):
        ang = i * TAU / 8
        ring.append((math.cos(ang) * 1.04, math.sin(ang) * 0.96 - 0.03, 2.8))
    m.loft('Chest', 'scarf', ring, [(0.24, 0.22)] * len(ring), sides=4, steps=1, smooth=False, cap_round=0.0)
    m.box('Chest', 'scarf', (0.55, 0.64, 2.3), (0.42, 0.14, 0.95), rot=(8, 0, -15), bevel=0.04)
    for z in (2.05, 2.4):
        m.box('Chest', 'scarf2', (0.55, 0.68, z), (0.44, 0.16, 0.1), rot=(8, 0, -15), bevel=0.0)
    # ice shoulder pads
    for side, s in SIDES:
        m.box('Chest', 'plate', (0.95 * s, 0.0, 2.6), (0.6, 0.95, 0.24), rot=(0, 28 * s, 0), bevel=0.06)
        m.spike('Chest', 'ice', (1.25 * s, 0.0, 2.65), (0.8 * s, 0.1, 0.6), 0.45 * g + 0.1, 0.18, twist=45)

# flippers with an ice blade down the outer edge, clawed feet, tail
for side, s in SIDES:
    m.loft(f'Flipper{side}', coat, [(1.1 * s, 0, 2.75), (1.42 * s, 0.05, 2.05), (1.58 * s, 0.12, 1.3)],
           [(0.13, 0.4), (0.12, 0.38), (0.06, 0.13)], sides=4, steps=3, smooth=False, up=(0, -1, 0))
    if not chick:
        m.loft(f'Flipper{side}', 'ice', [(1.2 * s, 0.38, 2.6), (1.5 * s, 0.42, 1.95), (1.66 * s, 0.3, 1.25)],
               [(0.05, 0.1), (0.05, 0.12), (0.02, 0.04)], sides=4, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'Foot{side}', 'foot', (0.5 * s, -0.38, 0.09), (0.64, 0.95, 0.16), bevel=0.05,
          taper=dict(axis='y', end=-1, scale=(1.25, 0.8)))
    for dx in (-0.2, 0.0, 0.2):
        m.spike(f'Foot{side}', 'foot', (0.5 * s + dx, -0.82, 0.08), (dx, -1, 0), 0.22, 0.14, 0.1, snap=False)
m.spike('Tail', coat, (0, 0.85, 0.65), (0, 1, -0.4), 0.6, 0.55, 0.2)


# ---------------- animation ----------------
WALK = dict(stride=1.25, frames=26)
RUN = dict(stride=6.0, frames=24)   # belly slide


def flap(pose, up, fwd=0.0):
    for side, s in SIDES:
        pose[f'Flipper{side}'] = ((fwd, -up * s, 0), (0, 0, 0))


def feet(pose, t_, stride, lift, roll_side_lift=True):
    for (side, s), ph in zip(SIDES, (0.0, 0.5)):
        u = (t_ + ph) % 1.0
        if u < 0.5:   # planted, sliding back as the body waddles forward
            dy = stride / 2 - stride * (u / 0.5)
            dz, tilt = 0.0, 0.0
        else:
            q = (u - 0.5) / 0.5
            dy = -stride / 2 + stride * smooth01(q)
            dz = lift * math.sin(math.pi * q)
            tilt = -18 * math.sin(math.pi * q)
        pose[f'Foot{side}'] = ((tilt, 0, 0), (0, -dy * S, dz * S))


def idle(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 3 * E * math.sin(p), 0), (0, 0, 0.03 * S * math.sin(2 * p))),
        'Chest': ((1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((4 * math.sin(p + 0.5), 0, 14 * E * math.sin(p * 0.5 + 1) * envelope(t_, 0.2, 0.8)), (0, 0, 0)),
        'Tail': ((0, 0, 12 * math.sin(2 * p)), (0, 0, 0)),
    }
    flap(pose, 6 + 5 * math.sin(2 * p))
    return pose


def walk(t_):
    p = TAU * t_
    roll = 11 * E * math.sin(p)
    pose = {
        'Hips': ((0, roll, 0), (0, 0, 0.1 * S * abs(math.sin(p)))),
        'Chest': ((-3, -roll * 0.35, 4 * math.sin(p)), (0, 0, 0)),
        'Head': ((2 * math.sin(2 * p), -roll * 0.3, -3 * math.sin(p)), (0, 0, 0)),
        'Tail': ((0, 0, 18 * math.sin(p + 0.8)), (0, 0, 0)),
    }
    flap(pose, 22 + 10 * math.sin(2 * p))
    feet(pose, t_, WALK['stride'], 0.25)
    return pose


def run(t_):
    # belly slide: tipped forward onto the belly, flippers back, feet trailing, a little wobble
    p = TAU * t_
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, -0.35 * S)),
        'Hips': ((78, 2 * math.sin(p), 0), (0, 0, 1.05 * S + 0.04 * S * math.sin(2 * p))),
        'Chest': ((-4, 0, 3 * math.sin(p)), (0, 0, 0)),
        'Head': ((-50, 0, 4 * math.sin(p)), (0, 0, 0)),
        'Tail': ((10, 0, 0), (0, 0, 0)),
    }
    flap(pose, -10 + 6 * math.sin(2 * p), fwd=45)
    for side, s in SIDES:
        pose[f'Foot{side}'] = ((-60 + 10 * math.sin(p + s), 0, 0), (0, 0, 0))
    return pose


def happy(t_):
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    settle = envelope(t_, 0.1, 0.6, 1.0)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.7 * S * E * hop)),
        'Chest': ((-6 * settle, 0, 0), (0, 0, 0)),
        'Head': ((-14 * settle, 0, 10 * math.sin(TAU * 2 * t_) * settle), (0, 0, 0)),
        'Tail': ((0, 0, 25 * math.sin(TAU * 4 * t_) * settle), (0, 0, 0)),
    }
    flap(pose, 20 + 55 * settle * (0.5 + 0.5 * math.sin(TAU * 4 * t_)))
    return pose


def sleep(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 0, 0), (0, 0, -0.1 * S + 0.03 * S * math.sin(p))),
        'Chest': ((6 + 1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((28, 0, 25), (0, 0, 0)),   # beak tucked into the shoulder
    }
    flap(pose, 0)
    return pose


def roar(t_):
    e = envelope(t_, 0.2, 0.75)
    pose = {
        'Chest': ((-12 * e, 0, 0), (0, 0, 0)),
        'Head': ((-30 * e, 0, 6 * math.sin(TAU * 8 * t_) * e), (0, 0, 0)),
    }
    flap(pose, 70 * e + 15 * math.sin(TAU * 6 * t_) * e)
    return pose


m.anim('Idle', 72, True, idle, key_step=3)
m.anim('Walk', WALK['frames'], True, walk, key_step=2)
m.anim('Run', RUN['frames'], True, run, key_step=2)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, roar, key_step=3)
m.anim('Attack', 30, False, roar, key_step=3)
m.anim('Happy', 36, False, happy, key_step=2)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
