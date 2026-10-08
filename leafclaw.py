"""Leafclaw - Uncommon forest raptor (two legs): leaf crest, leaf-feathered arms and tail,
sickle claw. Faces -Y. Same stage system as quadruped.py:
    blender -b --python leafclaw.py -- <out_dir> [Child|Teen|Adult] [--live]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import envelope, smooth01
from quadruped import Scaled, STAGE_DEFAULTS, lighten, add, TAU

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
STAGE = args[1] if len(args) > 1 else 'Adult'
st = dict(STAGE_DEFAULTS[STAGE])
st.update({'Child': dict(head=1.5, legL=0.8), 'Teen': dict(legL=1.12)}.get(STAGE, {}))
S, E, g = st['S'], st['energy'], st['grow']
h, L, T, t = st['head'], st['legL'], st['legT'], st['tail']
bL, bW, bH = st['bL'], st['bW'], st['bH']
m = Scaled('Leafclaw' if STAGE == 'Adult' else f'Leafclaw_{STAGE}', S)

for key, val in {
    'body': '#4f9e3e', 'stripe': ('#1d4220', True, True), 'belly': '#efe4b4', 'leaf': ('#2f8f2c', False, True),
    'leaf2': ('#a6e04a', False, True), 'foot': '#24361c', 'claw': ('#f3efe2', False), 'tooth': ('#fbf7ee', False),
    'dark': ('#0e120b', False), 'mouth': ('#5a1e22', False), 'tongue': '#d6405c',
    'eye_dark': ('#0e120b', False), 'iris': ('#ff8a1a', False), 'eye_glint': ('#ffffff', False),
}.items():
    hexv, dots, edges = (val, True, False) if isinstance(val, str) else (tuple(val) + (False,))[:3]
    m.color(key, lighten(hexv, st['tint']) if dots else hexv, dots=dots, edges=edges)

# ---------------- anchors (adult-design units) ----------------
hipZ = 2.6 * L
ankZ = 0.55 * T
kneeZ = ankZ + (hipZ - ankZ) * 0.5
hips = (0, 0.55 * bL, hipZ + 0.1)
chest = (0, -0.25 * bL, hipZ + 0.2 * bH)
neckStart = (0, -1.3 * bL, hipZ + 0.6 * bH)
hp = add(neckStart, (0, -0.6 * (0.8 + 0.2 * h), 0.85 * (0.8 + 0.2 * h)))


def H(dx, dy, dz):
    return add(hp, (dx * h, dy * h, dz * h))


SIDES = (('L', 1), ('R', -1))

# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0.4 * bL, 0), (0, 0.4 * bL, 1))
m.bone('Hips', hips, chest, 'MonsterRoot')
m.bone('Chest', chest, neckStart, 'Hips')
m.bone('Neck', neckStart, hp, 'Chest')
m.bone('Head', hp, H(0, -1.7, -0.1), 'Neck')
m.bone('Jaw', H(0, -0.2, -0.4), H(0, -1.6, -0.55), 'Head')
t1 = add(hips, (0, 1.3 * t, -0.1 * t))
t2 = add(t1, (0, 1.3 * t, -0.2 * t))
t3 = add(t2, (0, 1.3 * t, -0.2 * t))
m.bone('Tail1', hips, t1, 'Hips')
m.bone('Tail2', t1, t2, 'Tail1')
m.bone('Tail3', t2, t3, 'Tail2')
for side, s in SIDES:
    x = 0.65 * bW * s
    hipP, knee, ank, toe = (x, 0.5 * bL, hipZ), (x * 1.05, -0.1 * bL - 0.15 * L, kneeZ), (x * 1.05, 0.5 * bL, ankZ), (x * 1.05, -0.35 * T, 0.12 * T)
    m.bone(f'Thigh{side}', hipP, knee, 'Hips')
    m.bone(f'Shin{side}', knee, ank, f'Thigh{side}')
    m.bone(f'Foot{side}', ank, toe, f'Shin{side}')
    sh = (0.55 * bW * s, -1.05 * bL, hipZ + 0.15 * bH)
    el = (0.75 * bW * s, -1.45 * bL, hipZ - 0.45 * bH)
    hand = (0.7 * bW * s, -1.9 * bL, hipZ - 0.35 * bH)
    m.bone(f'Arm{side}', sh, el, 'Chest')
    m.bone(f'Hand{side}', el, hand, f'Arm{side}')

# ---------------- body ----------------
m.loft(['Tail3', 'Tail2', 'Tail1', 'Hips', 'Chest', 'Neck'], 'body',
       [add(t3, (0, 0.35 * t, 0)), t2, t1, add(hips, (0, 0.3, 0)), chest, add(chest, (0, -0.85 * bL, 0.25 * bH)),
        add(neckStart, (0, -0.25, 0.4)), H(0, -0.35, 0.05)],
       [(0.1, 0.1), (0.32 * bW, 0.34 * bH), (0.58 * bW, 0.6 * bH), (0.98 * bW, 1.02 * bH), (0.95 * bW, 1.02 * bH),
        (0.72 * bW, 0.76 * bH), (0.5 * max(bW, 0.7 * h), 0.52 * max(bH, 0.7 * h)), (0.46 * h, 0.46 * h)],
       sides=6, steps=1, smooth=False)
m.box(['Hips', 'Chest'], 'belly', add(chest, (0, 0.25, -0.66 * bH)), (1.2 * bW, 1.9 * bL, 0.35 * bH), bevel=0.08)
# dark stripe-plates down the back and tail
for i, (bone, p, w) in enumerate((('Chest', add(chest, (0, -0.7 * bL, 0.98 * bH)), 0.8), ('Chest', add(chest, (0, -0.1, 1.02 * bH)), 0.9),
                                  ('Hips', add(hips, (0, -0.15, 1.0 * bH)), 0.85), ('Hips', add(hips, (0, 0.45, 0.88 * bH)), 0.75),
                                  ('Tail1', add(t1, (0, -0.4, 0.55 * bH)), 0.6), ('Tail2', add(t2, (0, -0.5, 0.33)), 0.45))):
    m.box(bone, 'stripe', p, (w, 0.55 * w, 0.14), rot=(14, 0, 0), bevel=0.04)
    if g > 0.4:
        m.spike(bone, 'leaf2', add(p, (0, 0.05, 0.08)), (0, 0.55, 1), 0.5 * w * (0.5 + 0.5 * g), 0.26 * w, 0.06)

# ---------------- head: a big wedge with a jaw full of teeth ----------------
m.box('Head', 'body', H(0, -0.85, 0.05), (1.3 * h, 2.15 * h, 1.1 * h), bevel=0.1 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.72, 0.66)))
for side, s in SIDES:
    m.box('Head', 'stripe', H(0.42 * s, -0.75, 0.5), (0.5 * h, 1.0 * h, 0.2 * h), rot=(-8, -14 * s, 0), bevel=0.03 * h)   # brow ridges
m.box('Head', 'mouth', H(0, -0.95, -0.42), (1.05 * h, 1.8 * h, 0.12 * h), bevel=0.0)
m.box('Jaw', 'belly', H(0, -0.95, -0.58), (1.05 * h, 1.8 * h, 0.3 * h), bevel=0.06 * h,
      taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
m.box('Jaw', 'mouth', H(0, -0.9, -0.44), (0.88 * h, 1.5 * h, 0.1 * h), bevel=0.0)
m.box('Jaw', 'tongue', H(0, -1.05, -0.4), (0.35 * h, 0.9 * h, 0.07 * h), bevel=0.02 * h)
for side, s in SIDES:
    for k in range(5):   # jagged square teeth, top and bottom
        m.box('Head', 'tooth', H(0.42 * s * (1 - 0.06 * k), -1.75 + k * 0.3, -0.5), (0.13 * h, 0.13 * h, 0.22 * h), rot=(0, 0, 45), bevel=0.01)
        m.box('Jaw', 'tooth', H(0.38 * s * (1 - 0.06 * k), -1.6 + k * 0.3, -0.42), (0.12 * h, 0.12 * h, 0.2 * h), rot=(0, 0, 45), bevel=0.01)
    m.box('Head', 'dark', H(0.6 * s, -0.6, 0.27), (0.14 * h, 0.5 * h, 0.4 * h), bevel=0.03 * h)   # socket
    m.eye('Head', H(0.68 * s, -0.62, 0.27), (1 * s, -0.3, 0.1), 0.38 * h * st['eye'])
    m.box('Head', 'dark', H(0.17 * s, -1.85, 0.14), (0.1 * h, 0.06 * h, 0.08 * h), bevel=0.0)
# crest of big outlined leaf blades sweeping back off the skull
for i, (x, k, yaw) in enumerate(((0, 1.0, 0), (-0.28, 0.85, -18), (0.28, 0.85, 18), (-0.5, 0.65, -32), (0.5, 0.65, 32))):
    if g < 0.5 and i >= 3:
        continue
    L_ = (0.8 + 1.1 * g) * k * h
    base = H(x * 0.5, -0.5, 0.5)
    d = (x * 0.35, 1.0, 0.8)
    n = math.sqrt(sum(v * v for v in d))
    d = tuple(v / n for v in d)
    # the blade's long (Y) axis points along d: back and up, rooted in the skull
    m.box('Head', 'leaf' if i % 2 == 0 else 'leaf2', add(base, tuple(v * L_ * 0.45 for v in d)), (0.09 * h, 1.15 * L_, 0.34 * h * k),
          rot=(math.degrees(math.atan2(d[2], d[1])), 0, yaw * 1.4), bevel=0.02)
# leaf ruff round the neck
for i in range(7):
    a = -1.5 + i * 0.5
    p = add(neckStart, (math.sin(a) * 0.62 * bW, -0.15, 0.3 + math.cos(a) * 0.5 * bH))
    m.box('Neck', 'leaf' if i % 2 else 'leaf2', p, (0.12, 0.5, 0.55 * (0.6 + 0.4 * g)), rot=(30, 0, math.degrees(a) * 0.6), bevel=0.02)

# leaf fan off the tail tip
for i, (yaw, k) in enumerate(((0, 1.0), (-0.45, 0.85), (0.45, 0.85), (-0.85, 0.65), (0.85, 0.65))):
    if g < 0.5 and i >= 3:
        continue
    L_ = (0.6 + 0.95 * g) * k
    m.box('Tail3', 'leaf2' if i % 2 else 'leaf', add(t3, (yaw * 0.35 * L_, 0.45 * L_, 0.05)), (0.36 * k, 1.0 * L_, 0.08),
          rot=(-5, 0, -math.degrees(yaw) * 0.6), bevel=0.02)

# ---------------- legs & arms ----------------
for side, s in SIDES:
    x = 0.65 * bW * s
    m.loft([f'Thigh{side}', f'Shin{side}', f'Foot{side}'], 'body',
           [(x, 0.55 * bL, hipZ + 0.15), (x * 1.05, -0.1 * bL - 0.15 * L, kneeZ), (x * 1.05, 0.5 * bL, ankZ + 0.05)],
           [(0.72 * T, 0.85 * T), (0.4 * T, 0.42 * T), (0.26 * T, 0.26 * T)], sides=6, steps=1, smooth=False, up=(0, -1, 0))
    m.box(f'Thigh{side}', 'stripe', (x * 1.25, 0.25 * bL, hipZ - 0.3), (0.2, 0.8 * T, 0.6 * T), rot=(20, 0, 0), bevel=0.03)   # thigh plate
    fy = 0.05 * bL - 0.1
    m.box(f'Foot{side}', 'foot', (x * 1.05, fy, 0.28 * T), (0.66 * T, 1.15 * T, 0.56 * T), bevel=0.06 * T,
          taper=dict(axis='y', end=-1, scale=(1.15, 0.8)))
    for dx in (-0.22, 0.0, 0.22):
        m.spike(f'Foot{side}', 'claw', (x * 1.05 + dx * T, fy - 0.58 * T, 0.16 * T), (0, -1, -0.3), 0.3 * T, 0.15 * T)
    # the big sickle claw, held up off the ground
    sc = (x * 1.05 - 0.28 * s * T, fy - 0.2 * T, 0.42 * T)
    k = (0.35 + 0.45 * g) * T
    m.loft(f'Foot{side}', 'claw', [sc, add(sc, (0, -0.15 * k, 0.6 * k)), add(sc, (0, -0.65 * k, 0.95 * k)), add(sc, (0, -1.1 * k, 0.75 * k))],
           [(0.12 * T, 0.12 * T), (0.1 * T, 0.1 * T), (0.06 * T, 0.06 * T), (0.01, 0.01)], sides=5, steps=2, smooth=False)
    sh = (0.55 * bW * s, -1.05 * bL, hipZ + 0.15 * bH)
    el = (0.75 * bW * s, -1.45 * bL, hipZ - 0.45 * bH)
    hand = (0.7 * bW * s, -1.9 * bL, hipZ - 0.35 * bH)
    m.loft([f'Arm{side}', f'Hand{side}'], 'body', [sh, el, hand], [(0.28, 0.3), (0.2, 0.2), (0.17, 0.17)],
           sides=6, steps=1, smooth=False, up=(0, -1, 0))
    for dz in (-0.12, 0.0, 0.12):
        m.spike(f'Hand{side}', 'claw', add(hand, (0, -0.08, dz)), (0, -1, -0.5), 0.3, 0.09)
    m.box(f'Arm{side}', 'leaf', add(el, (0.12 * s, 0.25, 0.1)), (0.08, 0.75 * (0.5 + 0.5 * g), 0.32), rot=(15, 0, 10 * s), bevel=0.02)
    m.box(f'Arm{side}', 'leaf2', add(el, (0.16 * s, 0.4, 0.28)), (0.08, 0.6 * (0.5 + 0.5 * g), 0.26), rot=(25, 0, 14 * s), bevel=0.02)

# ---------------- animation ----------------
LEGS = {side: (f'Thigh{side}', f'Shin{side}', f'Foot{side}') for side, _ in SIDES}
WALK = dict(stride=1.5 * L, lift=0.5 * L, duty=0.6, frames=28)
RUN = dict(stride=2.8 * L, lift=0.8 * L, duty=0.36, frames=18)


def step(u, stride, lift, duty):
    u %= 1.0
    if u < duty:
        s = u / duty
        roll = smooth01((s - 0.7) / 0.3)
        return -stride / 2 + stride * s, 0.12 * S * roll, 25 * roll
    s = (u - duty) / (1 - duty)
    dz = lift * math.sin(math.pi * s) ** 0.8 + 0.12 * S * (1 - smooth01(s / 0.25))
    tilt = 25 * (1 - smooth01(s / 0.6)) - 10 * math.sin(math.pi * smooth01((s - 0.5) / 0.5))
    return stride / 2 - stride * smooth01(s), dz, tilt


def legs(pose, t_, gait, shift=(0, 0), phase=(0.0, 0.5)):
    for (side, _), ph in zip(SIDES, phase):
        dy, dz, tilt = step(t_ + ph, gait['stride'] * S, gait['lift'] * S, gait['duty'])
        ay, az = m.rest_ankle(LEGS[side][1])
        m.ik_leg(pose, *LEGS[side], (ay + dy, az + dz), shift, tilt)


def planted(pose, shift=(0, 0)):
    for side, _ in SIDES:
        m.ik_leg(pose, *LEGS[side], m.rest_ankle(LEGS[side][1]), shift)


def arms(pose, swing, fold=0.0):
    for side, s in SIDES:
        pose[f'Arm{side}'] = ((swing * s - fold, 0, 0), (0, 0, 0))
        pose[f'Hand{side}'] = ((-fold * 0.8, 0, 0), (0, 0, 0))


def tail(pose, p, amp, lift=0.0):
    for i, b in enumerate(('Tail1', 'Tail2', 'Tail3')):
        pose[b] = ((lift * (1 - 0.3 * i), 0, amp * E * (1 + 0.4 * i) * math.sin(p - 0.6 * (i + 1))), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    bob = 0.04 * S * E * math.sin(2 * p)
    # quick bird-like head glances: hold, snap, hold
    glance = 14 * E * (smooth01((t_ - 0.2) / 0.06) - smooth01((t_ - 0.55) / 0.06) - smooth01((t_ - 0.7) / 0.06) + smooth01((t_ - 0.9) / 0.06))
    pose = {
        'Hips': ((0, 0, 0), (0, 0, bob)),
        'Chest': ((1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Neck': ((3 * math.sin(p + 0.4), 0, glance * 0.4), (0, 0, 0)),
        'Head': ((2 * math.sin(p + 1), 0, glance * 0.6), (0, 0, 0)),
        'Jaw': ((3 + 2 * math.sin(2 * p), 0, 0), (0, 0, 0)),
    }
    tail(pose, p, 5)
    arms(pose, 0, 6 + 4 * math.sin(p))
    planted(pose, (0, bob))
    return pose


def walk(t_):
    p = TAU * t_
    bob = -0.09 * S * E * math.cos(2 * p)
    roll = 4 * math.sin(p)
    pose = {
        'Hips': ((3, roll, 4 * math.sin(p)), (0.06 * S * math.cos(p), 0, bob)),
        'Chest': ((0, -roll * 0.6, -6 * math.sin(p)), (0, 0, 0)),
        'Neck': ((-3 + 3 * E * math.cos(2 * p + 0.6), 0, 3 * math.sin(p)), (0, 0, 0)),
        'Head': ((2 * E * math.cos(2 * p + 1), 0, -2 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((4, 0, 0), (0, 0, 0)),
    }
    tail(pose, p + math.pi, 7)
    arms(pose, 8 * math.sin(p), 10)
    legs(pose, t_, WALK, (0, bob))
    return pose


def run(t_):
    p = TAU * t_
    bob = (-0.16 * math.cos(2 * p) + 0.05) * S * E
    pose = {
        'Hips': ((12, 3 * math.sin(p), 3 * math.sin(p)), (0, 0, bob)),
        'Chest': ((4, 0, -4 * math.sin(p)), (0, 0, 0)),
        'Neck': ((-14, 0, 0), (0, 0, 0)),
        'Head': ((-6 + 3 * math.sin(2 * p), 0, 0), (0, 0, 0)),
        'Jaw': ((14, 0, 0), (0, 0, 0)),
    }
    tail(pose, p + math.pi, 3, lift=-10)
    arms(pose, 0, 35)
    legs(pose, t_, RUN, (0, bob))
    return pose


def sleep(t_):
    p = TAU * t_
    drop = -(hipZ - 1.0 * L) * S + 0.04 * S * math.sin(p)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, drop)),
        'Hips': ((-4, 0, 0), (0, 0, 0)),
        'Chest': ((1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Neck': ((25, 0, 55), (0, 0, 0)),       # head tucked round to rest on the body
        'Head': ((10 + 2 * math.sin(p + 0.5), 0, 20), (0, 0, 0)),
        'Tail1': ((-10, 0, 30), (0, 0, 0)),
        'Tail2': ((0, 0, 35), (0, 0, 0)),
        'Tail3': ((0, 0, 40), (0, 0, 0)),
    }
    arms(pose, 0, 40)
    for side, s in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        m.ik_leg(pose, *LEGS[side], (ay - 0.4 * S * L, 0.3 * S * T), (0, drop))
    return pose


def roar(t_):
    e = envelope(t_, 0.22, 0.75)
    shake = math.sin(TAU * 8 * t_) * envelope(t_, 0.3, 0.7, 0.8)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0.2 * S * e, 0)),
        'Hips': ((-12 * e, 0, 0), (0, 0, 0)),
        'Chest': ((-10 * e, 0, 0), (0, 0, 0)),
        'Neck': ((-18 * e, 0, 0), (0, 0, 0)),
        'Head': ((-14 * e, 0, 10 * shake), (0, 0, 0)),
        'Jaw': ((45 * e, 0, 0), (0, 0, 0)),
    }
    tail(pose, TAU * 3 * t_, 4 * e, lift=12 * e)
    for side, s in SIDES:
        pose[f'Arm{side}'] = ((-30 * e, -25 * e * s, 0), (0, 0, 0))
        pose[f'Hand{side}'] = ((-20 * e, 0, 0), (0, 0, 0))
    planted(pose, (0.2 * S * e, 0))
    return pose


def attack(t_):
    w = envelope(t_, 0.28, 0.28, 0.42)
    s = smooth01((t_ - 0.3) / 0.14) if t_ < 0.58 else 1 - smooth01((t_ - 0.58) / 0.42)
    dy = (0.4 * w - 1.3 * s) * S
    snap = math.sin(math.pi * smooth01((t_ - 0.3) / 0.25)) if 0.3 < t_ < 0.55 else 0
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, dy, 0)),
        'Hips': ((-6 * w + 14 * s, 0, 0), (0, 0, 0)),
        'Chest': ((-4 * w + 8 * s, 0, 0), (0, 0, 0)),
        'Neck': ((-12 * w + 10 * s, 0, 0), (0, 0, 0)),
        'Head': ((-8 * w + 6 * s, 0, 0), (0, 0, 0)),
        'Jaw': ((15 * w + 40 * snap, 0, 0), (0, 0, 0)),
    }
    tail(pose, 0, 0, lift=-12 * s)
    for side, sd in SIDES:
        pose[f'Arm{side}'] = ((-50 * s, -10 * s * sd, 0), (0, 0, 0))
        pose[f'Hand{side}'] = ((-30 * s, 0, 0), (0, 0, 0))
    planted(pose, (dy, 0))
    return pose


def happy(t_):
    hop = math.sin(math.pi * smooth01(t_ / 0.45)) if t_ < 0.45 else 0.0
    settle = envelope(t_, 0.1, 0.55, 1.0)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.7 * S * E * hop)),
        'Chest': ((-8 * settle, 0, 0), (0, 0, 0)),
        'Neck': ((-14 * settle, 0, 0), (0, 0, 0)),
        'Head': ((-8 * settle, 0, 12 * math.sin(TAU * 2 * t_) * settle), (0, 0, 0)),
        'Jaw': ((30 * settle, 0, 0), (0, 0, 0)),
    }
    tail(pose, TAU * 2 * t_, 12 * settle, lift=8 * settle)
    arms(pose, 0, -25 * settle)
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        m.ik_leg(pose, *LEGS[side], (ay, az + 0.2 * S * hop), (0, 0.7 * S * E * hop))
    return pose


m.anim('Idle', 72, True, idle, key_step=3)
m.anim('Walk', WALK['frames'], True, walk, key_step=2)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 54, False, roar, key_step=3)
m.anim('Attack', 30, False, attack, key_step=2)
m.anim('Happy', 36, False, happy, key_step=2)
m.refs = {k: gg['stride'] * S / (gg['duty'] * gg['frames'] / 30) for k, gg in (('Walk', WALK), ('Run', RUN))}
m.build(OUT)
