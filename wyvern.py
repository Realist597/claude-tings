"""Infernal Wyvern - Legendary Underworld wyvern: walks upright on two clawed legs, its arms ARE its
wings (3-bone wing arms with a leathery membrane, glowing veins and wrist claws). Obsidian armour
plates with lava glowing between them, segmented molten belly plates, a crown of swept-back horns,
a fanged jaw that breathes fire, spikes down the spine, a chain wound round its tail and a spiked
blade on the tail tip. Faces -Y.
    blender -b --python wyvern.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Mouth (fire breath), Crown, Lava1-4 (embers), WingTipL/R + WingTrailL/R, TailBlade."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from mathutils import Vector
from creature import setup, ik, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('InfernalWyvern', {
    'body': '#433440', 'plate': ('#5c4650', True, True), 'plate2': ('#73565c', True, True), 'belly': '#c2561f', 'lava': ('#ff5a14', False),
    'lava2': ('#ffb02a', False), 'wing': ('#5a1620', True, True), 'vein': ('#ff6a1e', False), 'horn': ('#3b3036', False),
    'horn2': ('#d9c6a8', False), 'fang': ('#f6f0e2', False), 'claw': ('#191416', False), 'iron': '#4a4d56',
    'mouth': '#3a0f12', 'tongue': '#c2303c', 'eye_dark': ('#120709', False), 'iris': ('#ffb02a', False),
    'eye_glint': ('#ffe9b0', False),
}, {'Child': dict(head=1.35, eye=1.4), 'Teen': dict(head=1.12, eye=1.15)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
span = 0.55 + 0.45 * g

# ---------------- rig ----------------
HIP = (0, 0.6, 3.2)
CHEST = (0, -0.9, 3.65)
NECK0 = (0, -2.0, 4.3)
NECK1 = (0, -2.65, 5.25)
HEAD = (0, -3.15, 5.95)
m.bone('MonsterRoot', (0, 0.3, 0), (0, 0.3, 1))
m.bone('Hips', HIP, CHEST, 'MonsterRoot')
m.bone('Chest', CHEST, NECK0, 'Hips')
m.bone('Neck1', NECK0, NECK1, 'Chest')
m.bone('Neck2', NECK1, HEAD, 'Neck1')


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


m.bone('Head', HEAD, Hd(0, -1.7, 0.0), 'Neck2')
m.bone('Jaw', Hd(0, -0.25, -0.45), Hd(0, -1.75, -0.6), 'Head')
TAIL = [(0, 0.9, 3.05), (0, 2.4, 2.75), (0, 3.9, 2.35), (0, 5.3, 1.95), (0, 6.6, 1.7)]
for i in range(4):
    m.bone(f'Tail{i + 1}', TAIL[i], TAIL[i + 1], 'Hips' if i == 0 else f'Tail{i}')
WING = {}
for side, s in SIDES:
    sh = (1.0 * s, -1.25, 4.15)
    el = (sh[0] + 1.6 * span * s, -0.75, 4.15 + 1.25 * span)
    wr = (el[0] + 1.9 * span * s, -1.05, el[2] - 0.4 * span)
    tip = (wr[0] + 2.2 * span * s, 0.15, wr[2] - 0.75 * span)
    WING[side] = (sh, el, wr, tip)
    m.bone(f'Wing{side}', sh, el, 'Chest')
    m.bone(f'Fore{side}', el, wr, f'Wing{side}')
    m.bone(f'Hand{side}', wr, tip, f'Fore{side}')
    x = 0.95 * s
    m.bone(f'Thigh{side}', (x, 0.5, 3.0), (x * 1.08, -0.65, 1.85), 'Hips')
    m.bone(f'Shin{side}', (x * 1.08, -0.65, 1.85), (x * 1.08, 0.55, 0.75), f'Thigh{side}')
    m.bone(f'Foot{side}', (x * 1.08, 0.55, 0.75), (x * 1.08, -0.75, 0.12), f'Shin{side}')

# ---------------- body ----------------
body_pts = [TAIL[4], TAIL[3], TAIL[2], TAIL[1], (0, 1.0, 3.15), (0, -0.2, 3.5), (0, -1.3, 3.85), NECK0, NECK1, Hd(0, 0.1, -0.05)]
body_r = [(0.12, 0.12), (0.4, 0.38), (0.62, 0.58), (0.85, 0.8), (1.28, 1.2), (1.35, 1.3), (1.15, 1.12), (0.78, 0.78), (0.6, 0.62),
          (0.55 * h, 0.56 * h)]
m.loft(['Tail4', 'Tail3', 'Tail2', 'Tail1', 'Hips', 'Hips', 'Chest', 'Neck1', 'Neck2', 'Head'], 'body', body_pts, body_r,
       sides=9, steps=2, smooth=False)
# segmented molten belly plates under the chest, belly and neck
for i, (y, z, w) in enumerate(((-1.6, 3.15, 0.9), (-0.9, 2.65, 1.05), (-0.2, 2.35, 1.1), (0.5, 2.3, 1.05), (1.2, 2.45, 0.9))):
    m.box(['Chest', 'Hips'][int(y > -0.5)], 'belly', (0, y, z), (w * 1.6, 0.62, 0.2), rot=(-12, 0, 0), bevel=0.08)
for i, t in enumerate((0.25, 0.6)):
    p = Vector(NECK0).lerp(Vector(NECK1), t)
    m.box('Neck1', 'belly', tuple(p + Vector((0, -0.45, -0.35))), (0.9, 0.5, 0.18), rot=(-50, 0, 0), bevel=0.06)
# obsidian armour plates down the back with lava glowing in the seams, spikes on each plate
lava_k = 0
for i, (ya, za, w) in enumerate(((-1.5, 4.9, 0.9), (-0.7, 4.75, 1.15), (0.1, 4.6, 1.2), (0.9, 4.35, 1.1), (1.7, 3.95, 0.85),
                                 (2.6, 3.55, 0.7), (3.5, 3.1, 0.55), (4.4, 2.65, 0.42))):
    bone = 'Chest' if ya < -0.4 else 'Hips' if ya < 1.0 else 'Tail1' if ya < 2.4 else 'Tail2' if ya < 3.9 else 'Tail3'
    m.box(bone, 'plate' if i % 2 else 'plate2', (0, ya, za - 0.15), (w * 1.5, 0.75, 0.3), rot=(10, 0, 0), bevel=0.1)
    m.box(bone, 'lava', (0, ya + 0.42, za - 0.22), (w * 1.4, 0.14, 0.26), rot=(10, 0, 0), bevel=0.0)
    m.spike(bone, 'horn', (0, ya, za - 0.05), (0, 0.4, 1), (0.5 + 0.5 * g) * w, 0.36 * w, snap=False)
    if i in (1, 3, 5, 6):
        lava_k += 1
        m.socket(f'Lava{lava_k}', bone, (0, ya + 0.45, za))
# lava cracks running down the flanks
for side, s in SIDES:
    pts = [(s * 1.28, y, 3.2 + (0.25 if k % 2 else -0.2)) for k, y in enumerate((-0.9, -0.5, -0.1, 0.3, 0.7))]
    m.loft(['Chest', 'Hips'], 'lava', pts, [(0.12, 0.12)] * len(pts), sides=4, steps=1, smooth=False)

# head: long wedge skull, fanged jaw, burning eyes and a crown of swept-back horns
m.box('Head', 'body', Hd(0, -0.75, 0.12), (1.4 * h, 1.9 * h, 1.15 * h), bevel=0.28 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.78, 0.8)))
m.box('Head', 'plate', Hd(0, -1.75, 0.0), (0.92 * h, 1.2 * h, 0.7 * h), bevel=0.16 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.68, 0.7)))
m.box('Head', 'plate2', Hd(0, -0.95, 0.66), (1.2 * h, 0.4 * h, 0.2 * h), rot=(-12, 0, 0), bevel=0.06 * h)
m.box('Head', 'mouth', Hd(0, -1.5, -0.36), (0.85 * h, 1.7 * h, 0.12 * h), bevel=0.0)
m.box('Jaw', 'plate', Hd(0, -1.45, -0.55), (0.9 * h, 1.75 * h, 0.3 * h), bevel=0.08 * h, taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
m.box('Jaw', 'tongue', Hd(0, -1.4, -0.4), (0.38 * h, 1.1 * h, 0.08 * h), bevel=0.03 * h)
m.socket('Mouth', 'Head', Hd(0, -2.5, -0.3))
for side, s in SIDES:
    for k in range(4):
        m.spike('Head', 'fang', Hd(0.36 * s, -2.1 + 0.32 * k, -0.4), (0, 0, -1), (0.32 if k == 0 else 0.18) * h, 0.1 * h, snap=False)
        m.spike('Jaw', 'fang', Hd(0.34 * s, -2.0 + 0.32 * k, -0.45), (0, 0, 1), 0.16 * h, 0.08 * h, snap=False)
    m.eye('Head', Hd(0.55 * s, -1.05, 0.3), (0.85 * s, -0.55, 0.2), 0.24 * h * st['eye'])
    m.blob('Head', 'lava2', Hd(0.48 * s, -2.42, 0.18), (0.08 * h, 0.05 * h, 0.05 * h), u=6, v=4)   # glowing nostrils
    # horn crown: two big swept horns and three smaller ones behind each
    L = (0.6 + 1.6 * g) * h
    m.spike('Head', 'horn2', Hd(0.45 * s, -0.55, 0.62), (0.35 * s, 1.0, 0.45), L, 0.36 * h, snap=False)
    for k, (dx, dz, f) in enumerate(((0.65, 0.35, 0.6), (0.72, 0.0, 0.5), (0.68, -0.3, 0.4))):
        m.spike('Head', 'horn', Hd(dx * s, -0.25 + 0.05 * k, dz), (0.8 * s, 1.0, 0.1 - 0.2 * k), L * f, 0.24 * h, snap=False)
    # spiked cheek frills
    m.spike('Jaw', 'horn', Hd(0.48 * s, -0.5, -0.55), (0.7 * s, 0.6, -0.4), 0.45 * h * (0.5 + 0.5 * g), 0.2 * h, snap=False)
m.socket('Crown', 'Head', Hd(0, 0.6, 1.0))

# wings: leathery membrane from the arm to the body, glowing veins, a wrist claw
for side, s in SIDES:
    sh, el, wr, tip = WING[side]
    bones = [f'Wing{side}', f'Fore{side}', f'Hand{side}']
    lead, trail = [], []
    n = 15
    for i in range(n):
        u = i / (n - 1)
        if u <= 0.3:
            a, b, f = sh, el, u / 0.3
        elif u <= 0.6:
            a, b, f = el, wr, (u - 0.3) / 0.3
        else:
            a, b, f = wr, tip, (u - 0.6) / 0.4
        p = tuple(x + (y - x) * f for x, y in zip(a, b))
        lead.append(p)
        chord = (3.1 * (1 - u) ** 0.7 + 0.2) * span * (0.78 + 0.22 * abs(math.cos(u * 3.5 * math.pi)))
        trail.append(add(p, (0.15 * s * chord, chord * 0.92, -0.45 * chord)))
    m.strip(bones, 'wing', lead, trail, thickness=0.1)
    m.loft(bones, 'plate', [sh, el, wr, tip], [(0.22, 0.22), (0.17, 0.17), (0.12, 0.12), (0.05, 0.05)], sides=6, steps=3, smooth=False)
    for j in (5, 9, 12):   # glowing finger veins from the wrist
        m.loft([bones[2]] if j > 9 else bones[1:], 'vein', [wr, trail[j]], [(0.11, 0.11), (0.05, 0.05)], sides=4, steps=1, smooth=False)
    m.loft(bones[:2], 'vein', [el, trail[3]], [(0.11, 0.11), (0.05, 0.05)], sides=4, steps=1, smooth=False)
    m.spike(bones[2], 'claw', wr, (0.3 * s, -0.6, 0.6), 0.45 * span, 0.16, snap=False)
    m.socket(f'WingTip{side}', bones[2], tip)
    m.socket(f'WingTrail{side}', bones[2], trail[-3])
    m.blob(['Chest', bones[0]], 'body', sh, (0.5, 0.5, 0.45), u=8, v=5)

# legs: armoured thighs, digitigrade shins, big black talons
for side, s in SIDES:
    x = 0.95 * s
    m.loft([f'Thigh{side}', f'Shin{side}', f'Foot{side}'], 'body', [(x, 0.5, 3.05), (x * 1.08, -0.65, 1.85), (x * 1.08, 0.55, 0.8)],
           [(0.72, 0.8), (0.42, 0.42), (0.26, 0.26)], sides=8, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'Thigh{side}', 'plate', (x * 1.25, -0.1, 2.6), (0.25, 1.0, 0.9), rot=(25, 0, 0), bevel=0.08)
    m.loft([f'Shin{side}', f'Foot{side}'], 'body', [(x * 1.08, 0.55, 0.85), (x * 1.08, 0.35, 0.5), (x * 1.08, 0.0, 0.32)],
           [(0.28, 0.28), (0.3, 0.3), (0.32, 0.28)], sides=7, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'Foot{side}', 'plate', (x * 1.08, -0.2, 0.28), (0.75, 1.3, 0.52), bevel=0.14, taper=dict(axis='y', end=-1, scale=(1.1, 0.75)))
    for dx in (-0.25, 0.0, 0.25):
        m.spike(f'Foot{side}', 'claw', (x * 1.08 + dx, -0.8, 0.2), (dx, -1, -0.4), 0.45, 0.17, snap=False)
    m.spike(f'Foot{side}', 'claw', (x * 1.08, 0.45, 0.35), (0, 1, -0.5), 0.35, 0.15, snap=False)

# a chain wound round the tail and a spiked blade on the tip
for i in range(9):
    t = i / 8
    p = Vector(TAIL[1]).lerp(Vector(TAIL[3]), t)
    r = 0.88 - 0.3 * t
    ang = t * TAU * 1.5
    c = p + Vector((math.cos(ang) * r, 0, math.sin(ang) * r))
    ring = [tuple(c + Vector((math.cos(TAU * k / 6) * 0.14, math.sin(TAU * k / 6) * 0.14 if i % 2 else 0,
                              math.sin(TAU * k / 6) * 0.14 if i % 2 == 0 else 0))) for k in range(7)]
    m.loft('Tail2' if t < 0.5 else 'Tail3', 'iron', ring, [(0.045, 0.045)] * 7, sides=4, steps=1, smooth=False, cap_round=0.0)
m.spike('Tail4', 'horn2', TAIL[4], (0, 1, 0.1), 1.3 * (0.5 + 0.5 * g), 0.75, 0.16, snap=False)
for s in (-1, 1):
    m.spike('Tail4', 'horn', add(TAIL[4], (0, -0.3, 0)), (s, 0.6, 0.2), 0.6 * (0.5 + 0.5 * g), 0.22, snap=False)
m.socket('TailBlade', 'Tail4', add(TAIL[4], (0, 0.8, 0)))


# ---------------- animation ----------------
LEGS = {side: (f'Thigh{side}', f'Shin{side}', f'Foot{side}') for side, _ in SIDES}
WALK = dict(stride=1.7, lift=0.55, duty=0.62, frames=36)
RUN = dict(stride=3.2, lift=0.9, duty=0.4, frames=24)
PIVOT = (HIP[1] * S, HIP[2] * S)


def step(u, stride, lift, duty):
    u %= 1.0
    if u < duty:
        q = u / duty
        return -stride / 2 + stride * q, 0.0, 22 * smooth01((q - 0.7) / 0.3)
    q = (u - duty) / (1 - duty)
    return stride / 2 - stride * smooth01(q), lift * math.sin(math.pi * q), 20 * (1 - smooth01(q / 0.6))


def legs(pose, t_, gait, bz=0.0, pitch=0.0):
    for (side, _), ph in zip(SIDES, (0.0, 0.5)):
        dy, dz, tilt = step(t_ + ph, gait['stride'] * S, gait['lift'] * S, gait['duty'])
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay + dy, az + dz), shift=(0, bz), pitch=pitch, pivot=PIVOT, tilt=tilt)


def planted(pose, bz=0.0, pitch=0.0):
    for side, _ in SIDES:
        ik(m, pose, LEGS[side], m.rest_ankle(LEGS[side][1]), shift=(0, bz), pitch=pitch, pivot=PIVOT)


def wings(pose, spread, flap=0.0, fold=0.0):
    """spread: 0 half-folded rest pose, + opens the wings up and out; flap adds a beat"""
    for side, s in SIDES:
        pose[f'Wing{side}'] = ((-spread * 0.2, -(spread + flap) * s * 0.6, -fold * s), (0, 0, 0))
        pose[f'Fore{side}'] = ((0, -(spread * 0.4 + flap * 0.5) * s, fold * 0.5 * s), (0, 0, 0))
        pose[f'Hand{side}'] = ((0, -flap * 0.4 * s, -fold * 0.8 * s), (0, 0, 0))


def tail(pose, p, amp, lift=0.0):
    for i in range(4):
        pose[f'Tail{i + 1}'] = ((lift * (1 - 0.2 * i), 0, amp * E * (1 + 0.35 * i) * math.sin(p - 0.6 * (i + 1))), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    breathe = math.sin(p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0.04 * S * breathe)),
        'Chest': ((-1.5 * breathe, 0, 0), (0, 0, 0)),
        'Neck1': ((3 * math.sin(p + 0.5), 0, 6 * E * math.sin(p * 0.5)), (0, 0, 0)),
        'Neck2': ((3 * math.sin(p + 1), 0, 4 * math.sin(p * 0.5 + 0.5)), (0, 0, 0)),
        'Head': ((4 * math.sin(p + 1.5), 0, 0), (0, 0, 0)),
        'Jaw': ((4 + 4 * math.sin(2 * p), 0, 0), (0, 0, 0)),
    }
    tail(pose, p, 6)
    wings(pose, 4 * breathe, fold=10)
    planted(pose, 0.04 * S * breathe)
    return pose


def walk(t_, gait=WALK, flap=0.0):
    p = TAU * t_
    bob = -0.12 * S * E * math.cos(2 * p)
    pitch = 4 * math.sin(2 * p)
    pose = {
        'Hips': ((pitch, 3 * math.sin(p), 4 * math.sin(p)), (0, 0, bob)),
        'Chest': ((-pitch, -2 * math.sin(p), -5 * math.sin(p)), (0, 0, 0)),
        'Neck1': ((-3 + 3 * math.cos(2 * p + 0.6), 0, 4 * math.sin(p)), (0, 0, 0)),
        'Neck2': ((2 * math.cos(2 * p + 1), 0, -2 * math.sin(p)), (0, 0, 0)),
        'Head': ((3 * math.cos(2 * p + 1.4), 0, -3 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((5, 0, 0), (0, 0, 0)),
    }
    tail(pose, p + math.pi, 9)
    wings(pose, 6 + flap * 0.4, flap * math.sin(2 * p), fold=12)
    legs(pose, t_, gait, bob, pitch)
    return pose


def roar(t_):
    e = envelope(t_, 0.22, 0.78)
    shake = math.sin(TAU * 7 * t_) * envelope(t_, 0.3, 0.7, 0.8)
    pose = {
        'Hips': ((-10 * e, 0, 0), (0, 0, 0.25 * S * e)),
        'Chest': ((-10 * e, 0, 0), (0, 0, 0)),
        'Neck1': ((-15 * e, 0, 0), (0, 0, 0)),
        'Neck2': ((-12 * e, 0, 0), (0, 0, 0)),
        'Head': ((-10 * e, 0, 8 * shake), (0, 0, 0)),
        'Jaw': ((40 * e, 0, 0), (0, 0, 0)),
    }
    tail(pose, TAU * 3 * t_, 6 * e, lift=10 * e)
    wings(pose, 70 * e, 10 * shake * e, fold=-15 * e)
    planted(pose, 0.25 * S * e, -10 * e)
    return pose


def happy(t_):
    e = envelope(t_, 0.1, 0.75)
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.6 * S * E * hop)),
        'Neck1': ((-10 * e, 0, 0), (0, 0, 0)),
        'Head': ((-8 * e, 0, 14 * math.sin(TAU * 2 * t_) * e), (0, 0, 0)),
        'Jaw': ((25 * e, 0, 0), (0, 0, 0)),
    }
    tail(pose, TAU * 2 * t_, 12 * e, lift=8 * e)
    wings(pose, 45 * e, 35 * e * math.sin(TAU * 3 * t_))
    planted(pose)
    return pose


def sleep(t_):
    p = TAU * t_
    drop = -(HIP[2] - 1.6) * S + 0.04 * S * math.sin(p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, drop)),
        'Chest': ((8, 0, 0), (0, 0, 0)),
        'Neck1': ((35, 0, 40), (0, 0, 0)),
        'Neck2': ((20, 0, 30), (0, 0, 0)),
        'Head': ((10, 0, 20), (0, 0, 0)),
    }
    tail(pose, 0, 0)
    for i in range(4):
        pose[f'Tail{i + 1}'] = ((0, 0, 25), (0, 0, 0))
    wings(pose, -10, fold=30)
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - 0.5 * S, 0.35 * S), shift=(0, drop))
    return pose


def bite(t_):
    w = envelope(t_, 0.28, 0.28, 0.42)
    s_ = smooth01((t_ - 0.3) / 0.14) if t_ < 0.58 else 1 - smooth01((t_ - 0.58) / 0.42)
    pose = {
        'Chest': ((-6 * w + 10 * s_, 0, 0), (0, 0, 0)),
        'Neck1': ((-14 * w + 18 * s_, 0, 0), (0, 0, 0)),
        'Neck2': ((-8 * w + 12 * s_, 0, 0), (0, 0, 0)),
        'Jaw': ((30 * w * (1 - s_) + 5, 0, 0), (0, 0, 0)),
    }
    tail(pose, 0, 0, lift=-8 * s_)
    wings(pose, 30 * w)
    planted(pose)
    return pose


m.anim('Idle', 96, True, idle, key_step=3)
m.anim('Walk', WALK['frames'], True, walk, key_step=2)
m.anim('Run', RUN['frames'], True, lambda t_: walk(t_, RUN, 40), key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 60, False, roar, key_step=2)
m.anim('Attack', 32, False, bite, key_step=2)
m.anim('Happy', 40, False, happy, key_step=2)
m.refs = {k: gg['stride'] * S / (gg['duty'] * gg['frames'] / 30) for k, gg in (('Walk', WALK), ('Run', RUN))}
m.build(OUT)
