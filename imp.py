"""Imp - Common Mythic imp: a pot-bellied little crimson devil with a big grinning head, big dark curled
horns, pointed ears, glowing ember eyes in dark sockets and fangs, glowing hellfire cracks across its
dark belly, gold arm cuffs, dark bat wings that flutter, a whippy tail ending in a glowing spade, goat
hooves, and a little trident with glowing prongs in its hand. Walks with a bouncy strut, hovers flapping when it runs
and twirls the trident when happy. Faces -Y.
    blender -b --python imp.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Trident (prong glint), WingTipL/R, Eyes (ember glow)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, ik, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('Imp', {
    'skin': '#b8222c', 'skin2': ('#6a1018', True, True), 'belly': '#3a1a1e', 'horn': ('#1a1214', False, True), 'hoof': ('#1a1214', False),
    'wing': ('#2e0e16', True, True), 'bone': '#160a0c', 'fang': ('#f6f0e2', False), 'mouth': '#1e0709', 'tongue': '#ff6a7a',
    'gold': ('#ffcf3a', False, True), 'shaft': '#2a1a14', 'glow': ('#ff9a2a', False), 'dark': ('#0c0506', False),
    'eye_dark': ('#120709', False), 'iris': ('#ffb02a', False),
    'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.3, eye=1.3), 'Teen': dict(head=1.12, eye=1.12)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
HEAD = (0, -0.1, 3.35 + 0.3 * (h - 1))


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0, 1.35), (0, 0, 2.1), 'MonsterRoot')
m.bone('Chest', (0, 0, 2.1), (0, -0.05, 2.75), 'Hips')
m.bone('Head', (0, -0.05, 2.75), Hd(0, -1.0, 0.2), 'Chest')
m.bone('Jaw', Hd(0, -0.2, -0.35), Hd(0, -0.95, -0.45), 'Head')
TAIL = [(0, 0.55, 1.45), (0, 1.2, 1.25), (0, 1.75, 1.45), (0, 2.15, 1.9)]
for i in range(3):
    m.bone(f'Tail{i + 1}', TAIL[i], TAIL[i + 1], 'Hips' if i == 0 else f'Tail{i}')
for side, s in SIDES:
    m.bone(f'Arm{side}', (0.78 * s, -0.05, 2.6), (1.05 * s, -0.25, 1.95), 'Chest')
    m.bone(f'Fore{side}', (1.05 * s, -0.25, 1.95), (1.05 * s, -0.75, 1.55), f'Arm{side}')
    m.bone(f'Wing{side}', (0.35 * s, 0.45, 2.65), (1.2 * s, 0.85, 3.3), 'Chest')
    m.bone(f'WingTip{side}', (1.2 * s, 0.85, 3.3), (2.0 * s, 1.05, 2.9), f'Wing{side}')
    m.bone(f'Thigh{side}', (0.38 * s, 0, 1.35), (0.42 * s, -0.35, 0.8), 'Hips')
    m.bone(f'Shin{side}', (0.42 * s, -0.35, 0.8), (0.42 * s, 0.1, 0.28), f'Thigh{side}')
    m.bone(f'Foot{side}', (0.42 * s, 0.1, 0.28), (0.42 * s, -0.3, 0.05), f'Shin{side}')

# ---------------- body ----------------
m.loft(['Hips', 'Chest', 'Head'], 'skin', [(0, 0.05, 1.15), (0, -0.05, 1.7), (0, -0.05, 2.3), (0, 0, 2.75), Hd(0, 0.05, -0.4)],
       [(0.6, 0.55), (0.95, 0.92), (0.82, 0.78), (0.55, 0.52), (0.4, 0.4)], sides=9, steps=2, smooth=False, up=(0, -1, 0))
m.blob(['Hips', 'Chest'], 'belly', (0, -0.42, 1.75), (0.72, 0.6, 0.62), u=10, v=7)
# hellfire cracks glowing across the belly
for (x, z, rot) in ((-0.22, 1.9, 30), (0.0, 1.72, -35), (0.24, 1.9, 25), (-0.12, 1.52, -20), (0.16, 1.5, 40)):
    # sit each crack on the belly's surface (an ellipsoid round (0, -0.42, 1.75))
    nx, nz = x / 0.72, (z - 1.75) / 0.62
    y = -0.42 - 0.6 * math.sqrt(max(0.0, 1 - nx * nx - nz * nz)) + 0.02
    m.box('Chest' if z > 1.7 else 'Hips', 'glow', (x, y, z), (0.06, 0.06, 0.26), rot=(0, rot, 0), bevel=0.0)
# big grinning head
m.blob('Head', 'skin', Hd(0, -0.15, 0.15), (0.95 * h, 0.88 * h, 0.82 * h), u=12, v=9)
m.blob('Head', 'skin2', Hd(0, -0.62, 0.42), (0.75 * h, 0.35 * h, 0.15 * h), u=8, v=5)   # brow
m.blob('Head', 'skin', Hd(0, -0.98, 0.0), (0.18 * h, 0.16 * h, 0.15 * h), u=8, v=5)   # nose
m.loft('Head', 'mouth', [Hd(-0.6, -0.55, -0.22), Hd(-0.3, -0.85, -0.38), Hd(0, -0.92, -0.42), Hd(0.3, -0.85, -0.38), Hd(0.6, -0.55, -0.22)],
       [(0.06 * h, 0.08 * h)] * 5, sides=5, steps=3, smooth=False)
m.blob('Jaw', 'skin2', Hd(0, -0.6, -0.48), (0.45 * h, 0.35 * h, 0.15 * h), u=8, v=5)
m.socket('Eyes', 'Head', Hd(0, -0.9, 0.2))
for side, s in SIDES:
    m.spike('Head', 'fang', Hd(0.22 * s, -0.86, -0.36), (0, -0.1, -1), 0.22 * h, 0.1 * h, snap=False)
    m.eye('Head', Hd(0.36 * s, -0.98, 0.25), (0.4 * s, -1, 0.1), 0.26 * h * st['eye'])
    # pointed ears and curled horns
    m.spike('Head', 'skin2', Hd(0.85 * s, -0.1, 0.1), (1 * s, 0.3, 0.45), 0.7 * h, 0.35 * h, 0.12 * h)
    prev = Hd(0.4 * s, -0.25, 0.7)
    for j in range(4):
        a = j * 0.55
        d = (0.55 * s, 0.2 + 0.5 * math.sin(a), math.cos(a))
        seg = (0.38 - 0.05 * j) * h * (0.5 + 0.5 * g)
        m.spike('Head', 'horn', prev, d, seg * 1.6, (0.28 - 0.05 * j) * h, snap=False)
        prev = (prev[0] + d[0] * seg, prev[1] + d[1] * seg, prev[2] + d[2] * seg)

# arms, hands, the trident
for side, s in SIDES:
    m.loft([f'Arm{side}', f'Fore{side}'], 'skin', [(0.78 * s, -0.05, 2.6), (1.05 * s, -0.25, 1.95), (1.05 * s, -0.75, 1.55)],
           [(0.22, 0.22), (0.17, 0.17), (0.15, 0.15)], sides=6, steps=2, smooth=False, up=(0, -1, 0))
    m.blob(f'Fore{side}', 'skin2', (1.05 * s, -0.8, 1.52), (0.2, 0.2, 0.2), u=8, v=5)
    m.loft(f'Fore{side}', 'gold', [(1.05 * s, -0.5, 1.72), (1.05 * s, -0.62, 1.64)], [(0.2, 0.2), (0.2, 0.2)], sides=6, steps=1, smooth=False)   # arm cuff
    for k in range(3):
        m.spike(f'Fore{side}', 'horn', (1.05 * s + (k - 1) * 0.08, -0.95, 1.5), (0, -1, -0.4), 0.15, 0.06, snap=False)
grip = (-1.05, -0.8, 1.52)
m.loft('ForeR', 'shaft', [add(grip, (0, 0, -1.0)), add(grip, (0, 0, 1.6))], [(0.06, 0.06), (0.06, 0.06)], sides=6, steps=1, smooth=False)
top = add(grip, (0, 0, 1.6))
m.loft('ForeR', 'gold', [add(top, (-0.35, 0, 0)), add(top, (0.35, 0, 0))], [(0.07, 0.07)] * 2, sides=5, steps=1, smooth=False)
for dx in (-0.35, 0.0, 0.35):
    ln = 0.55 if dx == 0 else 0.42
    m.spike('ForeR', 'gold', add(top, (dx, 0, 0)), (0, 0, 1), ln, 0.13, snap=False)
    m.spike('ForeR', 'glow', add(top, (dx, 0, ln * 0.55)), (0, 0, 1), ln * 0.6, 0.09, snap=False)   # glowing prong tips
m.socket('Trident', 'ForeR', add(top, (0, 0, 0.6)))

# bat wings
for side, s in SIDES:
    sh, el, tip = (0.35 * s, 0.45, 2.65), (1.2 * s, 0.85, 3.3), (2.0 * s, 1.05, 2.9)
    bones_ = [f'Wing{side}', f'WingTip{side}']
    lead = [sh, add(sh, ((el[0] - sh[0]) * 0.5, 0.2, 0.33)), el, add(el, ((tip[0] - el[0]) * 0.5, 0.1, -0.1)), tip]
    trail = [(sh[0], sh[1] + 0.1, sh[2] - 0.6), (lead[1][0], 0.95, 2.45), (el[0] * 0.95, 1.05, 2.35), (lead[3][0] * 0.95, 1.1, 2.4), tip]
    m.strip(bones_, 'wing', lead, trail, thickness=0.06)
    m.loft(bones_, 'bone', [sh, el, tip], [(0.07, 0.07), (0.06, 0.06), (0.03, 0.03)], sides=5, steps=2, smooth=False)
    m.spike(bones_[0], 'horn', el, (0.2 * s, 0, 1), 0.2, 0.07, snap=False)
    m.socket(f'WingTip{side}', bones_[1], tip)

# tail with a spade, legs with hooves
m.loft(['Hips', 'Tail1', 'Tail2', 'Tail3'], 'skin2', TAIL, [(0.12, 0.12), (0.08, 0.08), (0.06, 0.06), (0.05, 0.05)], sides=5, steps=3, smooth=False)
m.box('Tail3', 'skin2', add(TAIL[3], (0, 0.08, 0.2)), (0.1, 0.45, 0.45), rot=(45, 0, 0), bevel=0.03)
m.box('Tail3', 'glow', add(TAIL[3], (0, 0.08, 0.2)), (0.14, 0.28, 0.28), rot=(45, 0, 0), bevel=0.02)   # glowing spade core
for side, s in SIDES:
    m.loft([f'Thigh{side}', f'Shin{side}', f'Foot{side}'], 'skin', [(0.38 * s, 0, 1.35), (0.42 * s, -0.35, 0.8), (0.42 * s, 0.1, 0.3)],
           [(0.28, 0.28), (0.18, 0.18), (0.13, 0.13)], sides=6, steps=2, smooth=False, up=(0, -1, 0))
    m.box(f'Foot{side}', 'hoof', (0.42 * s, -0.12, 0.12), (0.3, 0.42, 0.24), bevel=0.06)


# ---------------- animation ----------------
LEGS = {side: (f'Thigh{side}', f'Shin{side}', f'Foot{side}') for side, _ in SIDES}
WALK = dict(stride=0.9, lift=0.35, duty=0.55, frames=22)
RUN = dict(stride=3.5, frames=18)


def wings(pose, beat, spread=0.0):
    for side, s in SIDES:
        pose[f'Wing{side}'] = ((0, -(beat + spread) * s, 0), (0, 0, 0))
        pose[f'WingTip{side}'] = ((0, -beat * 0.6 * s, 0), (0, 0, 0))


def tail(pose, p, amp):
    for i in range(3):
        pose[f'Tail{i + 1}'] = ((6 * math.sin(p + i), 0, amp * (1 + 0.4 * i) * math.sin(p - 0.7 * i)), (0, 0, 0))


def arms(pose, swing, raise_r=0.0):
    pose['ArmL'] = ((-swing, 0, 0), (0, 0, 0))
    pose['ArmR'] = ((swing - raise_r, 0, 0), (0, 0, 0))


def legs(pose, t_, bob=0.0):
    for (side, _), ph in zip(SIDES, (0.0, 0.5)):
        u = (t_ + ph) % 1.0
        D = WALK['stride'] * S
        if u < WALK['duty']:
            dy, dz = -D / 2 + D * u / WALK['duty'], 0.0
        else:
            q = (u - WALK['duty']) / (1 - WALK['duty'])
            dy, dz = D / 2 - D * smooth01(q), WALK['lift'] * S * math.sin(math.pi * q)
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay + dy, az + dz), shift=(0, bob))


def planted(pose, bob=0.0):
    for side, _ in SIDES:
        ik(m, pose, LEGS[side], m.rest_ankle(LEGS[side][1]), shift=(0, bob))


def idle(t_):
    p = TAU * t_
    bob = 0.05 * S * math.sin(2 * p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, bob)),
        'Chest': ((2 * math.sin(p), 0, 4 * math.sin(p)), (0, 0, 0)),
        'Head': ((4 * math.sin(p + 1), 0, 12 * math.sin(p * 0.5)), (0, 0, 0)),
        'Jaw': ((6 + 6 * math.sin(4 * p), 0, 0), (0, 0, 0)),
    }
    wings(pose, 10 * math.sin(4 * p))
    tail(pose, p * 2, 15)
    arms(pose, 5 * math.sin(p), 10 * abs(math.sin(p * 2)))
    planted(pose, bob)
    return pose


def walk(t_):
    p = TAU * t_
    bob = 0.12 * S * abs(math.sin(p))
    pose = {
        'Hips': ((0, 6 * math.sin(p), 0), (0, 0, bob)),
        'Chest': ((-4, -4 * math.sin(p), 6 * math.sin(p)), (0, 0, 0)),
        'Head': ((3 * math.cos(2 * p), 3 * math.sin(p), -4 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((8, 0, 0), (0, 0, 0)),
    }
    wings(pose, 8 * math.sin(4 * p))
    tail(pose, p * 2, 20)
    arms(pose, 25 * math.sin(p))
    legs(pose, t_, bob)
    return pose


def fly(t_):
    p = TAU * t_
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (0.9 + 0.15 * math.sin(2 * p)) * S)),
        'Hips': ((30, 0, 0), (0, 0, 0)),
        'Head': ((-25, 0, 0), (0, 0, 0)),
        'Jaw': ((15, 0, 0), (0, 0, 0)),
    }
    wings(pose, 45 * math.sin(2 * p), 20)
    tail(pose, p * 2, 10)
    arms(pose, -20)
    for side, _ in SIDES:
        pose[f'Thigh{side}'] = ((25, 0, 0), (0, 0, 0))
        pose[f'Shin{side}'] = ((-40, 0, 0), (0, 0, 0))
    return pose


def happy(t_):
    e = envelope(t_, 0.1, 0.8)
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 360 * smooth01(t_ / 0.6) if t_ < 0.6 else 0), (0, 0, 0.8 * S * hop)),
        'Head': ((-15 * e, 0, 0), (0, 0, 0)),
        'Jaw': ((25 * e, 0, 0), (0, 0, 0)),
        'ForeR': ((0, 0, 720 * smooth01(t_)), (0, 0, 0)),   # trident twirl
    }
    wings(pose, 30 * math.sin(TAU * 4 * t_) * e, 20 * e)
    tail(pose, TAU * 3 * t_, 25 * e)
    arms(pose, 0, 120 * e)
    planted(pose)
    return pose


def sleep(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 0, 0), (0, 0, -0.45 * S)),
        'Chest': ((15 + 2 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((20, 0, 15), (0, 0, 0)),
    }
    wings(pose, -15)
    tail(pose, 0, 0)
    arms(pose, -10)
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - 0.3 * S, az), shift=(0, -0.45 * S))
    return pose


def cackle(t_):
    e = envelope(t_, 0.15, 0.8)
    pose = {
        'Chest': ((-12 * e, 0, 0), (0, 0, 0)),
        'Head': ((-20 * e + 6 * math.sin(TAU * 8 * t_) * e, 0, 0), (0, 0, 0)),
        'Jaw': ((30 * e * (0.6 + 0.4 * math.sin(TAU * 8 * t_)), 0, 0), (0, 0, 0)),
    }
    wings(pose, 15 * math.sin(TAU * 6 * t_) * e, 35 * e)
    tail(pose, TAU * 4 * t_, 20 * e)
    arms(pose, -40 * e, 60 * e)
    planted(pose)
    return pose


m.anim('Idle', 72, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, walk, key_step=1)
m.anim('Run', RUN['frames'], True, fly, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, cackle, key_step=2)
m.anim('Attack', 30, False, cackle, key_step=2)
m.anim('Happy', 42, False, happy, key_step=1)
m.refs = {'Walk': WALK['stride'] * S / (WALK['duty'] * WALK['frames'] / 30), 'Run': RUN['stride'] * S / (RUN['frames'] / 30)}
m.build(OUT)
