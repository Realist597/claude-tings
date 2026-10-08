"""Tusk Walrus - Uncommon Frost Peaks walrus: a huge blubbery body, front flippers it pushes along
with, a fan of rear flippers, a whiskery muzzle and long ice tusks. Galumphs: the body humps along
like a caterpillar while the front flippers push. Claps its flippers when happy. Faces -Y.
    blender -b --python walrus.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: TuskL/TuskR (tusk glints), Crystal1 (back crystals)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('TuskWalrus', {
    'body': '#9c6c5e', 'belly': '#c49a8a', 'fold': '#6e463c', 'muzzle': '#e2bfae', 'whisker': ('#3a2420', False),
    'nose': ('#2a1a18', False), 'tusk': ('#e2fbff', False), 'flipper': '#6e4a40', 'snow': '#f4f8ff',
    'ice': ('#8ff0ff', False), 'plate': ('#6fb8ea', True, True), 'scar': ('#5a3530', False), 'dark': ('#120c0c', False),
    'claw': ('#e8f4ff', False), 'eye_dark': ('#0d1222', False), 'iris': ('#3ff0ff', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.35, eye=1.5), 'Teen': dict(head=1.12, eye=1.2)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
HEAD = (0, -2.65, 2.1)


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0.5, 0), (0, 0.5, 1))
m.bone('Hips', (0, 1.8, 1.3), (0, 0.2, 1.6), 'MonsterRoot')
m.bone('Chest', (0, 0.2, 1.6), (0, -1.6, 2.0), 'Hips')
m.bone('Head', (0, -1.6, 2.0), Hd(0, -0.9, -0.1), 'Chest')
m.bone('Tail', (0, 1.8, 1.25), (0, 3.0, 0.7), 'Hips')
for side, s in SIDES:
    m.bone(f'FlipperF{side}', (1.3 * s, -1.2, 1.3), (1.9 * s, -1.65, 0.12), 'Chest')
    m.bone(f'FlipperB{side}', (0.4 * s, 3.0, 0.65), (1.0 * s, 3.95, 0.15), 'Tail')

# ---------------- body ----------------
# chunky style: a huge chiselled studded body, a blocky head with a heavy brow over glowing eyes,
# massive faceted ice tusks, bristly muzzle, ice armour plates and a crystal ridge down the back
m.loft(['Tail', 'Hips', 'Chest', 'Head'], 'body',
       [(0, 3.0, 0.75), (0, 2.2, 1.0), (0, 1.0, 1.35), (0, -0.2, 1.6), (0, -1.2, 1.8), (0, -1.9, 2.0), Hd(0, 0.05, 0)],
       [(0.58, 0.44), (1.2, 0.98), (1.82, 1.4), (1.92, 1.55), (1.68, 1.5), (1.2, 1.12), (0.98 * h, 0.92 * h)],
       sides=7, steps=3, smooth=False)
m.blob(['Hips', 'Chest'], 'belly', (0, 0.2, 0.55), (1.5, 2.4, 0.5), u=7, v=4, smooth=False)
# blubber folds round the neck
for k, y in enumerate((-1.45, -1.05)):
    m.loft('Chest', 'fold', [(-1.3 + 0.15 * k, y, 1.2), (0, y - 0.15, 3.15 - 0.15 * k), (1.3 - 0.15 * k, y, 1.2)],
           [(0.16, 0.16)] * 3, sides=4, steps=3, smooth=False)
# head: a big block with a heavy brow, square muzzle pads and a dark nose
m.box('Head', 'body', Hd(0, -0.05, 0.08), (2.0 * h, 1.9 * h, 1.75 * h), bevel=0.28 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.9, 0.85)))
m.box('Head', 'fold', Hd(0, -0.88, 0.62), (1.9 * h, 0.36 * h, 0.34 * h), rot=(-12, 0, 0), bevel=0.06 * h)
for side, s in SIDES:
    m.box('Head', 'muzzle', Hd(0.38 * s, -0.85, -0.32), (0.78 * h, 0.7 * h, 0.75 * h), bevel=0.14 * h)
    for i in range(6):
        m.spike('Head', 'whisker', Hd((0.3 + 0.16 * (i % 3)) * s, -1.18, -0.15 - 0.2 * (i // 3)), (0.6 * s, -1, -0.2), 0.32 * h, 0.05 * h, snap=False)
    m.box('Head', 'dark', Hd(0.52 * s, -0.98, 0.32), (0.5 * h, 0.12 * h, 0.38 * h), bevel=0.04 * h)
    m.eye('Head', Hd(0.52 * s, -1.04, 0.32), (0.3 * s, -1, 0.1), 0.22 * h * st['eye'])
    # massive faceted tusks sheathed in ice
    L = (0.8 + 1.6 * g) * h
    base = Hd(0.32 * s, -1.0, -0.62)
    pts = [base, add(base, (0.04 * s * L, -0.12 * L, -0.5 * L)), add(base, (0.1 * s * L, -0.12 * L, -1.0 * L))]
    m.loft('Head', 'tusk', pts, [(0.2 * h, 0.2 * h), (0.16 * h, 0.16 * h), (0.02, 0.02)], sides=5, steps=3, smooth=False)
    m.spike('Head', 'ice', add(base, (0.06 * s * L, -0.15 * L, -0.45 * L)), (0.8 * s, -0.4, 0.1), 0.25 * h * (0.5 + g), 0.12 * h, twist=45)
    m.socket(f'Tusk{side}', 'Head', pts[-1])
m.box('Head', 'nose', Hd(0, -1.2, 0.12), (0.5 * h, 0.2 * h, 0.24 * h), bevel=0.05 * h)
m.box('Head', 'scar', Hd(0.55, -0.4, 0.95), (0.08 * h, 0.7 * h, 0.06 * h), rot=(0, 0, 30), bevel=0.0)
# ice armour on the back with a crystal ridge, and snow drifts
for y, x, r, rz in ((-0.6, 0.35, 0.8, 15), (0.5, -0.45, 0.7, -10), (1.4, 0.25, 0.55, 20)):
    bone = ['Hips', 'Chest'][int(y < 0)]
    m.box(bone, 'snow', (x, y, 2.85 - 0.25 * abs(y)), (r * 1.6, r * 1.4, 0.3), rot=(0, 0, rz), bevel=0.08)
for side, s in SIDES:
    for y, z in ((-0.8, 2.45), (0.4, 2.3)):
        bone = ['Hips', 'Chest'][int(y < 0)]
        m.box(bone, 'plate', (1.25 * s, y, z), (0.9, 1.1, 0.24), rot=(0, 38 * s, 0), bevel=0.06)
if g > 0.25:
    for y, k in ((-0.6, 1.0), (0.2, 0.8), (1.0, 0.65), (1.7, 0.5)):
        bone = ['Hips', 'Chest'][int(y < 0)]
        for d, kk in (((0, 0.1, 1), 1.0), ((0.5, 0.2, 1), 0.6), ((-0.5, 0.0, 1), 0.6)):
            m.spike(bone, 'ice', (0, y, 2.9 - 0.2 * abs(y)), d, (0.75 * g + 0.2) * k * kk, 0.3 * k * kk, twist=45)
    m.socket('Crystal1', 'Chest', (0, -0.55, 3.9))

# flippers: the front ones stand under the shoulders (with claws), the back ones fan out flat behind
for side, s in SIDES:
    m.loft(f'FlipperF{side}', 'flipper', [(1.3 * s, -1.2, 1.3), (1.65 * s, -1.4, 0.6), (1.9 * s, -1.7, 0.14)],
           [(0.22, 0.52), (0.18, 0.5), (0.11, 0.58)], sides=4, steps=3, smooth=False, up=(0, -1, 0))
    for dx in (-0.25, 0.0, 0.25):
        m.spike(f'FlipperF{side}', 'claw', (1.9 * s + dx, -1.95, 0.1), (0, -1, -0.2), 0.22, 0.09, snap=False)
    m.loft(f'FlipperB{side}', 'flipper', [(0.35 * s, 2.95, 0.65), (0.7 * s, 3.5, 0.3), (1.05 * s, 4.0, 0.12)],
           [(0.42, 0.15), (0.52, 0.13), (0.64, 0.08)], sides=4, steps=3, smooth=False, up=(0, 0, 1))


# ---------------- animation ----------------
WALK = dict(stride=1.4, frames=34)
RUN = dict(stride=2.3, frames=22)


def flippers(pose, sweep_l, sweep_r, out=0.0):
    for (side, s), sw in zip(SIDES, (sweep_l, sweep_r)):
        pose[f'FlipperF{side}'] = ((sw, -out * s, 0), (0, 0, 0))


def galumph(t_, gait, amp):
    u = t_ % 1.0
    p = TAU * u
    # the hump travels from the chest back to the hips: chest lifts first, then the rear
    chest_up = max(0.0, math.sin(p)) * amp
    hip_up = max(0.0, math.sin(p - 1.6)) * amp * 0.8
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.12 * S * E * max(0.0, math.sin(p)))),
        'Hips': ((6 * amp * math.sin(p - 1.6), 0, 0), (0, 0, 0.25 * S * hip_up)),
        'Chest': ((-12 * amp * math.sin(p), 0, 2 * math.sin(p * 0.5)), (0, 0, 0.3 * S * chest_up)),
        'Head': ((10 * amp * math.sin(p + 0.4), 0, 4 * math.sin(p)), (0, 0, 0)),
        'Tail': ((-14 * amp * math.sin(p - 2.4), 0, 0), (0, 0, 0)),
    }
    # both front flippers push together while the chest is down, then swing forward
    push = -28 + 56 * smooth01((u - 0.5) / 0.45) if u >= 0.5 else 28 - 56 * smooth01(u / 0.5)
    flippers(pose, push, push, 8)
    for side, s in SIDES:
        pose[f'FlipperB{side}'] = ((-10 * math.sin(p - 2.4), 0, 8 * s * math.sin(p)), (0, 0, 0))
    return pose


def idle(t_):
    p = TAU * t_
    sniff = math.sin(TAU * 8 * t_) * envelope(t_, 0.55, 0.7, 0.8)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0.03 * S * math.sin(p))),
        'Chest': ((-2 * math.sin(p), 0, 0), (0, 0, 0.05 * S * math.sin(p))),
        'Head': ((-6 * envelope(t_, 0.5, 0.85) + 2 * sniff, 0, 8 * E * math.sin(p * 0.5)), (0, 0, 0)),
        'Tail': ((4 * math.sin(p), 0, 0), (0, 0, 0)),
    }
    flippers(pose, 3 * math.sin(p), 3 * math.sin(p + 1))
    for side, s in SIDES:
        pose[f'FlipperB{side}'] = ((0, 0, 10 * s * math.sin(p + s)), (0, 0, 0))
    return pose


def happy(t_):
    # sits up a bit and claps its front flippers
    e = envelope(t_, 0.12, 0.8)
    clap = abs(math.sin(TAU * 3 * t_)) * e
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0)),
        'Chest': ((-22 * e, 0, 0), (0, 0, 0.35 * S * e)),
        'Head': ((-15 * e, 0, 10 * math.sin(TAU * 2 * t_) * e), (0, 0, 0)),
        'Tail': ((-10 * e, 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        pose[f'FlipperF{side}'] = ((-60 * e, 30 * s * clap, -25 * s * e), (0, 0, 0))
    return pose


def sleep(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 0, 0), (0, 0, -0.15 * S + 0.04 * S * math.sin(p))),
        'Chest': ((10, 0, 0), (0, 0, -0.2 * S)),
        'Head': ((22, 0, 15), (0, 0, 0)),
    }
    flippers(pose, -15, -15, 30)
    return pose


def bellow(t_):
    e = envelope(t_, 0.2, 0.75)
    shake = math.sin(TAU * 7 * t_) * e
    pose = {
        'Chest': ((-25 * e, 0, 0), (0, 0, 0.3 * S * e)),
        'Head': ((-35 * e, 0, 8 * shake), (0, 0, 0)),
    }
    flippers(pose, -30 * e, -30 * e, 20 * e)
    return pose


m.anim('Idle', 72, True, idle, key_step=3)
m.anim('Walk', WALK['frames'], True, lambda t_: galumph(t_, WALK, 1.0 * E), key_step=2)
m.anim('Run', RUN['frames'], True, lambda t_: galumph(t_, RUN, 1.5 * E), key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 54, False, bellow, key_step=3)
m.anim('Attack', 30, False, bellow, key_step=2)
m.anim('Happy', 40, False, happy, key_step=2)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
