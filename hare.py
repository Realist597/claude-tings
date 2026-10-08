"""Snow Hare - Common Frost Peaks hare with its own body plan: big springy hind legs with long feet,
little front legs, tall ears tipped with ice crystals, a puffball tail. Moves in real hops (crouch,
launch, front paws land, back feet land). Faces -Y.
    blender -b --python hare.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: FrostL/FrostR (ear crystals), Crystal1 (back crystals)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creature import setup, ik, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('SnowHare', {
    'body': '#eef3fb', 'belly': '#ffffff', 'fluff': '#cddbf0', 'ear_in': '#f4a6c0', 'nose': ('#ee7aa0', False),
    'tooth': ('#ffffff', False), 'ice': ('#8ff0ff', False), 'plate': ('#7cc4f2', True, True), 'pad': '#c9b6d0',
    'claw': ('#dff2ff', False), 'dark': ('#141b30', False),
    'eye_dark': ('#0d1222', False), 'iris': ('#2ee8ff', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.35, eye=1.4), 'Teen': dict(head=1.12, eye=1.15)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
HEAD = (0, -1.5, 2.3)


def Hd(x, y, z):
    """head-relative point, scaled by the stage's head size"""
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0.3, 0), (0, 0.3, 1))
m.bone('Hips', (0, 0.8, 1.4), (0, -0.5, 1.6), 'MonsterRoot')
m.bone('Chest', (0, -0.5, 1.6), (0, -1.1, 2.05), 'Hips')
m.bone('Head', (0, -1.1, 2.05), Hd(0, -0.8, 0.1), 'Chest')
m.bone('Tail', (0, 1.45, 1.5), (0, 1.85, 1.65), 'Hips')
for side, s in SIDES:
    m.bone(f'Ear{side}', Hd(0.3 * s, 0.15, 0.55), Hd(0.48 * s, 0.55, 2.1 + 0.4 * g), 'Head')
    x = 0.66 * s
    m.bone(f'Thigh{side}', (x, 0.75, 1.2), (x, 0.0, 0.72), 'Hips')
    m.bone(f'Shin{side}', (x, 0.0, 0.72), (x, 0.95, 0.3), f'Thigh{side}')
    m.bone(f'Foot{side}', (x, 0.95, 0.3), (x, -0.25, 0.07), f'Shin{side}')
    x = 0.45 * s
    m.bone(f'UpperF{side}', (x, -0.75, 1.15), (x, -0.68, 0.62), 'Chest')
    m.bone(f'LowerF{side}', (x, -0.68, 0.62), (x, -0.8, 0.16), f'UpperF{side}')
    m.bone(f'FootF{side}', (x, -0.8, 0.16), (x, -1.1, 0.05), f'LowerF{side}')

# ---------------- body ----------------
# chunky style: a chiselled studded body, a boxy skull with an angry ice brow and glowing eyes, big
# buck teeth, spiky fur ruff and cheeks, ice-armoured haunches, crystal-tipped ears, claws
m.loft(['Tail', 'Hips', 'Chest', 'Head'], 'body',
       [(0, 1.5, 1.5), (0, 0.8, 1.45), (0, 0.0, 1.5), (0, -0.6, 1.62), (0, -1.0, 1.95), Hd(0, 0.2, -0.05)],
       [(0.32, 0.32), (1.12, 1.05), (1.02, 0.98), (0.9, 0.9), (0.62, 0.64), (0.55 * h, 0.55 * h)],
       sides=6, steps=3, smooth=False)
m.blob(['Hips', 'Chest'], 'belly', (0, -0.15, 1.02), (0.78, 1.2, 0.45), u=6, v=4, smooth=False)
# spiky fur ruff round the neck
for i in range(7):
    a = math.radians(-70 + 140 * i / 6)
    m.spike('Chest', 'fluff' if i % 2 else 'belly', (0.7 * math.sin(a), -1.0 - 0.25 * math.cos(a), 1.55 - 0.35 * math.cos(a)),
            (math.sin(a), -0.6, -0.5 * math.cos(a)), 0.6, 0.34, 0.14)
# head: boxy skull, muzzle, nose, buck teeth
m.box('Head', 'body', Hd(0, -0.05, 0), (1.75 * h, 1.8 * h, 1.55 * h), bevel=0.24 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.84, 0.86)))
m.box('Head', 'belly', Hd(0, -0.82, -0.25), (0.9 * h, 0.5 * h, 0.6 * h), bevel=0.12 * h)
m.box('Head', 'nose', Hd(0, -1.08, -0.04), (0.28 * h, 0.12 * h, 0.18 * h), bevel=0.04 * h)
m.box('Head', 'dark', Hd(0, -1.07, -0.42), (0.5 * h, 0.08 * h, 0.12 * h), bevel=0.02 * h)
for side, s in SIDES:
    m.box('Head', 'tooth', Hd(0.09 * s, -1.06, -0.55), (0.16 * h, 0.08 * h, 0.32 * h), bevel=0.02 * h)
    m.spike('Head', 'fluff', Hd(0.72 * s, -0.4, -0.38), (s, 0.15, -0.35), 0.6 * h, 0.34 * h, 0.14 * h)
    m.spike('Head', 'belly', Hd(0.7 * s, -0.25, -0.12), (s, 0.4, 0.1), 0.45 * h, 0.26 * h, 0.12 * h)
    # glowing eye in a dark socket, an ice brow slanting down to the front (angry)
    m.box('Head', 'dark', Hd(0.8 * s, -0.5, 0.18), (0.14 * h, 0.62 * h, 0.5 * h), bevel=0.04 * h)
    m.eye('Head', Hd(0.88 * s, -0.52, 0.18), (1 * s, -0.4, 0.08), 0.31 * h * st['eye'])
    m.box('Head', 'plate', Hd(0.74 * s, -0.58, 0.5), (0.24 * h, 0.78 * h, 0.15 * h), rot=(18, 0, 0), bevel=0.03 * h)
    # ears: chiselled, pink inside, a jagged crystal half way up and a big one on the tip
    base, mid, tip = Hd(0.3 * s, 0.15, 0.55), Hd(0.4 * s, 0.32, 1.35 + 0.2 * g), Hd(0.48 * s, 0.55, 2.1 + 0.4 * g)
    m.loft(f'Ear{side}', 'body', [base, mid, tip], [(0.3 * h, 0.11 * h), (0.34 * h, 0.12 * h), (0.12 * h, 0.07 * h)],
           sides=4, steps=3, smooth=False, up=(0, -1, 0))
    m.loft(f'Ear{side}', 'ear_in', [add(base, (0, -0.08 * h, 0.15 * h)), add(mid, (0, -0.1 * h, 0)), add(tip, (0, -0.06 * h, -0.25 * h))],
           [(0.18 * h, 0.05 * h), (0.22 * h, 0.05 * h), (0.07 * h, 0.04 * h)], sides=4, steps=3, smooth=False, up=(0, -1, 0))
    m.spike(f'Ear{side}', 'ice', tip, (0.15 * s, 0.25, 1), (0.4 + 0.4 * g) * h, 0.26 * h, twist=45, snap=False)
    m.spike(f'Ear{side}', 'ice', add(mid, (0.12 * s * h, 0.05 * h, 0)), (0.9 * s, 0.2, 0.5), (0.2 + 0.25 * g) * h, 0.14 * h, twist=45)
    m.socket(f'Frost{side}', f'Ear{side}', add(tip, (0.05 * s, 0.1 * h, 0.5 * h)))

# hind legs: big armoured haunch, long clawed foot
for side, s in SIDES:
    x = 0.66 * s
    m.blob(f'Thigh{side}', 'body', (0.55 * s, 0.55, 1.05), (0.58, 0.95, 0.75), u=7, v=5, smooth=False)
    m.box(f'Thigh{side}', 'plate', (0.98 * s, 0.5, 1.2), (0.2, 0.85, 0.62), rot=(0, -22 * s, 0), bevel=0.05)
    m.box(f'Thigh{side}', 'plate', (0.9 * s, 0.98, 1.05), (0.18, 0.4, 0.42), rot=(0, -18 * s, 0), bevel=0.04)
    m.loft([f'Thigh{side}', f'Shin{side}'], 'body', [(x, 0.7, 1.15), (x, 0.05, 0.72), (x, 0.92, 0.33)],
           [(0.45, 0.5), (0.3, 0.3), (0.2, 0.2)], sides=5, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'Foot{side}', 'body', (x, 0.38, 0.12), (0.44, 1.3, 0.24), bevel=0.06,
          taper=dict(axis='y', end=-1, scale=(1.1, 0.8)))
    m.box(f'Foot{side}', 'pad', (x, 0.4, 0.015), (0.3, 1.0, 0.03), bevel=0.0)
    for dx in (-0.13, 0.0, 0.13):
        m.spike(f'Foot{side}', 'claw', (x + dx, -0.24, 0.1), (0, -1, -0.25), 0.24, 0.09, snap=False)
    x = 0.45 * s
    m.loft([f'UpperF{side}', f'LowerF{side}', f'FootF{side}'], 'body', [(x, -0.75, 1.2), (x, -0.68, 0.62), (x, -0.8, 0.18)],
           [(0.25, 0.25), (0.18, 0.18), (0.16, 0.16)], sides=5, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'FootF{side}', 'body', (x, -0.92, 0.08), (0.32, 0.42, 0.16), bevel=0.05)
    for dx in (-0.09, 0.09):
        m.spike(f'FootF{side}', 'claw', (x + dx, -1.1, 0.07), (0, -1, -0.2), 0.16, 0.07, snap=False)
# spiky puffball tail and a cluster of ice crystals on the back
m.blob('Tail', 'fluff', (0, 1.8, 1.7), (0.45, 0.45, 0.45), u=7, v=5, smooth=False)
for d in ((0, 1, 0.4), (0.7, 0.6, 0.3), (-0.7, 0.6, 0.3), (0, 0.6, 1), (0, 0.5, -0.6)):
    m.spike('Tail', 'belly', (0, 1.85, 1.72), d, 0.4, 0.24, 0.12)
if g > 0.25:
    for d, k in (((0, 0.2, 1), 1.0), ((0.5, 0.3, 1), 0.7), ((-0.5, 0.1, 1), 0.65), ((0.25, -0.4, 1), 0.5), ((-0.25, 0.6, 1), 0.5)):
        m.spike('Hips', 'ice', (0, 0.25, 2.35), d, 0.8 * k * g + 0.22, 0.28 * k, twist=45)
    m.socket('Crystal1', 'Hips', (0, 0.3, 3.1))


# ---------------- animation ----------------
BACK = ('Thigh', 'Shin', 'Foot')
FRONT = ('UpperF', 'LowerF', 'FootF')
PIVOT = (0.8 * S, 1.4 * S)   # Hips head
WALK = dict(stride=1.6, frames=28, hop=0.55)
RUN = dict(stride=3.4, frames=18, hop=0.9)


def curve(u, keys):
    """smooth piecewise curve through (u, value) keys, wrapping at 1"""
    keys = keys + [(keys[0][0] + 1, keys[0][1])]
    for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
        if u0 <= u < u1:
            return v0 + (v1 - v0) * smooth01((u - u0) / (u1 - u0))
    return keys[0][1]


def foot_track(u, land, lift, stride, height):
    """(dy, dz) of a foot that is on the ground from `land` to `lift` (cycle fractions, may wrap)"""
    contact = (lift - land) % 1.0
    since = (u - land) % 1.0
    if since < contact:   # planted: slides back as the body travels forward
        return -stride * contact / 2 + stride * since, 0.0
    q = (since - contact) / (1 - contact)
    return stride * contact / 2 - stride * smooth01(q), height * math.sin(math.pi * q)


def hop_pose(t_, gait):
    u = t_ % 1.0
    D, hopH = gait['stride'] * S, gait['hop'] * S * E
    air = 0.32 <= u < 0.72
    bz = hopH * math.sin(math.pi * (u - 0.32) / 0.4) if air else -0.12 * S * math.sin(math.pi * ((u - 0.72) % 1.0) / 0.6)
    # nose-up amount through the hop (crouch nose-down, launch nose-up, land nose-down)
    pitch = -curve(u, [(0.0, -5), (0.22, -12), (0.34, 14), (0.55, 0), (0.7, -14), (0.85, -6)])
    pose = {
        'Hips': ((pitch, 0, 0), (0, 0, bz)),
        'Head': ((-pitch * 0.7 + 3 * math.sin(TAU * u * 2), 0, 0), (0, 0, 0)),
        'Tail': ((10 * math.sin(TAU * u), 0, 0), (0, 0, 0)),
    }
    trail = curve(u, [(0.0, -10), (0.3, -15), (0.45, -45), (0.7, -30), (0.85, -15)])
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((trail + 4 * s * math.sin(TAU * u), 0, 6 * s), (0, 0, 0))
    for chain, land, lift, hgt in ((BACK, 0.8, 0.34, 0.5), (FRONT, 0.7, 0.05, 0.35)):
        for side, _ in SIDES:
            names = tuple(f'{b}{side}' for b in chain)
            dy, dz = foot_track(u, land, lift, D, hgt * S)
            ay, az = m.rest_ankle(names[1])
            ik(m, pose, names, (ay + dy, az + dz), shift=(0, bz), pitch=pitch, pivot=PIVOT,
               tilt=-25 * math.sin(math.pi * max(0.0, dz) / max(hgt * S, 1e-6)))
    return pose


def planted(pose, bz=0.0, pitch=0.0):
    for chain in (BACK, FRONT):
        for side, _ in SIDES:
            names = tuple(f'{b}{side}' for b in chain)
            ik(m, pose, names, m.rest_ankle(names[1]), shift=(0, bz), pitch=pitch, pivot=PIVOT)


def idle(t_):
    p = TAU * t_
    twitch = math.sin(TAU * 12 * t_) * envelope(t_, 0.3, 0.45, 0.55)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0.025 * S * math.sin(p))),
        'Head': ((3 * math.sin(p) + 3 * twitch, 0, 12 * E * math.sin(p * 0.5) * envelope(t_, 0.6, 0.9)), (0, 0, 0)),
        'Tail': ((0, 0, 15 * math.sin(3 * p)), (0, 0, 0)),
    }
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((-6 + 8 * math.sin(p + s), 0, 8 * s * math.sin(p * 2 + s)), (0, 0, 0))
    planted(pose, 0.025 * S * math.sin(p))
    return pose


def happy(t_):
    # a binky: big jump with a twist
    hop = math.sin(math.pi * smooth01(t_ / 0.55)) if t_ < 0.55 else 0.0
    twist = 35 * math.sin(math.pi * smooth01(t_ / 0.55)) if t_ < 0.55 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, twist), (0, 0, 1.1 * S * E * hop)),
        'Head': ((-10 * hop, 0, -twist * 0.5), (0, 0, 0)),
        'Tail': ((0, 0, 30 * math.sin(TAU * 4 * t_)), (0, 0, 0)),
    }
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((-25 * hop, 0, 15 * s * hop), (0, 0, 0))
    planted(pose)
    return pose


def sleep(t_):
    p = TAU * t_
    drop = -0.55 * S + 0.03 * S * math.sin(p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, drop)),
        'Head': ((12, 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((-70, 0, 10 * s), (0, 0, 0))   # ears laid flat along the back
    for chain in (BACK, FRONT):
        for side, _ in SIDES:
            names = tuple(f'{b}{side}' for b in chain)
            ay, az = m.rest_ankle(names[1])
            ik(m, pose, names, (ay, max(az + drop * 0.2, 0.05 * S)), shift=(0, drop))
    return pose


def thump(t_):
    # angry foot thump (roar / attack)
    e = envelope(t_, 0.15, 0.8)
    stomp = abs(math.sin(TAU * 3 * t_)) * e
    pose = {
        'Hips': ((8 * e, 0, 0), (0, 0, 0.1 * S * e)),
        'Head': ((-15 * e, 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((15 * e, 0, -10 * s * e), (0, 0, 0))
    planted(pose, 0.1 * S * e, 8 * e)
    for side, _ in SIDES:
        names = tuple(f'{b}{side}' for b in BACK)
        ay, az = m.rest_ankle(names[1])
        ik(m, pose, names, (ay, az + 0.3 * S * stomp), shift=(0, 0.1 * S * e), pitch=8 * e, pivot=PIVOT)
    return pose


m.anim('Idle', 72, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, lambda t_: hop_pose(t_, WALK), key_step=1)
m.anim('Run', RUN['frames'], True, lambda t_: hop_pose(t_, RUN), key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, thump, key_step=2)
m.anim('Attack', 30, False, thump, key_step=2)
m.anim('Happy', 36, False, happy, key_step=2)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
