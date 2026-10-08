"""Candle Bat - Common Haunted monster (Haunted Pumpkin featured egg): a gaunt dark-furred bat that
never lands. A cluster of three melting candles is fused into its skull, wax dripping down its head,
the tallest burning with a live flame. Tall notched ears, a snarling snout with long fangs, ember
eyes glowing under angry brows, a shaggy chest ruff, a spiked iron collar, big tattered wings on
bony four-finger arms with thumb claws, and taloned feet dangling as it hovers. Faces -Y.
    blender -b --python candlebat.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Candle (flame), EyeL/EyeR (ember glow), WingTipL/R."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, envelope, smooth01, add, TAU

m, st, OUT = setup('CandleBat', {
    'fur': '#3d2c4a', 'fur2': ('#7a5a8c', True, True), 'belly': '#5e4468', 'ear_in': '#b8405e',
    'wing': ('#5a1428', True, True), 'bone': ('#e2d8c6', False, True), 'claw': ('#e9e0d0', False),
    'fang': ('#f4eee2', False), 'mouth': '#1a0608', 'tongue': '#b8304a', 'nose': ('#140a10', False),
    'wax': ('#efe6d2', True, True), 'wick': ('#1a1210', False), 'flame': ('#ffb23a', False), 'glow': ('#ff8a1a', False),
    'iron': ('#33313c', False, True), 'dark': ('#0c0608', False), 'gold': ('#d8a838', False, True),
    'vein': ('#ff6a1a', False), 'skull': ('#e8dfca', False, True),
    'eye_dark': ('#0c0608', False), 'iris': ('#ff8a1a', False), 'eye_glint': ('#ffe9b0', False),
}, {'Child': dict(head=1.35, eye=1.3), 'Teen': dict(head=1.12, eye=1.12)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
HOVER = 2.3                     # body height above the ground
BODY = (0, 0.1, HOVER)
HEAD = (0, -0.55, HOVER + 0.85 + 0.15 * (h - 1))


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


span = 0.6 + 0.4 * g            # wings grow with the monster
WING = {}
for side, s in SIDES:
    sh = (0.55 * s, 0.05, HOVER + 0.45)
    el = (sh[0] + 1.2 * span * s, 0.35, sh[2] + 0.75 * span)
    wr = (el[0] + 1.0 * span * s, 0.6, el[2] - 0.15 * span)
    WING[side] = (sh, el, wr)

# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Body', (0, 0.45, HOVER - 0.4), (0, -0.2, HOVER + 0.55), 'MonsterRoot')
m.bone('Head', (0, -0.2, HOVER + 0.55), Hd(0, -1.0, 0.05), 'Body')
m.bone('Jaw', Hd(0, -0.35, -0.3), Hd(0, -0.95, -0.4), 'Head')
for side, s in SIDES:
    sh, el, wr = WING[side]
    m.bone(f'Wing{side}', sh, el, 'Body')
    m.bone(f'WingTip{side}', el, wr, f'Wing{side}')
    m.bone(f'Leg{side}', (0.3 * s, 0.25, HOVER - 0.45), (0.3 * s, 0.3, HOVER - 1.15), 'Body')
    m.bone(f'Ear{side}', Hd(0.42 * s, -0.25, 0.45), Hd(0.62 * s, -0.15, 1.2), 'Head')

# ---------------- body ----------------
m.blob('Body', 'fur', BODY, (0.72, 0.62, 0.82), u=10, v=7)
m.blob('Body', 'belly', add(BODY, (0, -0.4, -0.1)), (0.5, 0.3, 0.6), u=8, v=6)
# shaggy chest ruff: rows of outlined fur shards round the neck
for row, (z, r, n) in enumerate(((0.55, 0.62, 9), (0.32, 0.7, 11))):
    for i in range(n):
        a = math.pi + math.pi * (i + 0.5) / n          # the front half
        p = (math.cos(a) * r, 0.1 + math.sin(a) * r * 0.8, HOVER + z)
        d = (math.cos(a) * 0.6, math.sin(a) * 0.6 - 0.2, -0.8)
        m.spike('Body', 'fur2' if (i + row) % 2 else 'fur', p, d, 0.55 - 0.1 * row, 0.3, 0.12)
# back tufts
for i in range(4):
    m.spike('Body', 'fur2', (0, 0.55 + 0.1 * i, HOVER + 0.5 - 0.3 * i), (0, 1, 0.6 - 0.3 * i), 0.45, 0.28, 0.1)
# spiked iron collar
nc = (0, -0.15, HOVER + 0.62)
ring = [(math.cos(TAU * i / 14) * 0.52, nc[1] + math.sin(TAU * i / 14) * 0.45, nc[2]) for i in range(15)]
m.loft('Body', 'iron', ring, [(0.09, 0.11)] * len(ring), sides=6, steps=1, smooth=False, cap_round=0.0)
for i in range(7):
    a = TAU * i / 7
    m.spike('Body', 'iron', (math.cos(a) * 0.56, nc[1] + math.sin(a) * 0.49, nc[2]), (math.cos(a), math.sin(a), 0.15), 0.28, 0.12, 0.08, snap=False)

# a chain hanging off the collar with a skull pendant, its sockets lit
link = (0, nc[1] - 0.47, nc[2] - 0.05)
for k in range(4):
    m.box('Body', 'iron', add(link, (0, -0.02 * k, -0.13 * k)), (0.05 if k % 2 else 0.12, 0.12 if k % 2 else 0.05, 0.14), bevel=0.0)
sk = add(link, (0, -0.1, -0.62))
m.blob('Body', 'skull', sk, (0.17, 0.15, 0.17), u=7, v=5)
m.box('Body', 'skull', add(sk, (0, -0.04, -0.15)), (0.18, 0.15, 0.08), bevel=0.02)
for e in (-1, 1):
    m.blob('Body', 'vein', add(sk, (0.065 * e, -0.13, 0.02)), (0.045, 0.03, 0.05), u=5, v=3)
m.socket('Pendant', 'Body', add(sk, (0, -0.18, 0)))
# bone spikes down the spine, between the tufts
for i in range(5):
    m.spike('Body', 'bone', (0, 0.62 + 0.06 * i, HOVER + 0.7 - 0.32 * i), (0, 0.8, 0.9 - 0.35 * i), 0.38 - 0.04 * i, 0.14, 0.12, snap=False)

# ---------------- head ----------------
m.blob('Head', 'fur', Hd(0, -0.45, 0.1), (0.68 * h, 0.62 * h, 0.58 * h), u=10, v=7)
m.box('Head', 'fur', Hd(0, -0.98, -0.08), (0.52 * h, 0.48 * h, 0.4 * h), bevel=0.12 * h, taper=dict(axis='y', end=-1, scale=(0.75, 0.8)))
# leaf nose (bats have a spade-shaped nose leaf)
m.spike('Head', 'nose', Hd(0, -1.2, 0.0), (0, -0.25, 1), 0.38 * h, 0.24 * h, 0.06 * h, snap=False)
m.blob('Head', 'nose', Hd(0, -1.22, -0.06), (0.12 * h, 0.07 * h, 0.08 * h), u=6, v=4)
# snarl: dark mouth, long upper fangs, little lower teeth on the jaw
m.box('Head', 'mouth', Hd(0, -0.95, -0.28), (0.44 * h, 0.4 * h, 0.08 * h), bevel=0.0)
m.box('Jaw', 'fur', Hd(0, -0.82, -0.38), (0.42 * h, 0.42 * h, 0.12 * h), bevel=0.04 * h, taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
for side, s in SIDES:
    m.spike('Head', 'fang', Hd(0.15 * s, -1.12, -0.24), (0.05 * s, -0.15, -1), 0.38 * h, 0.1 * h, snap=False)
    m.spike('Jaw', 'fang', Hd(0.13 * s, -1.0, -0.36), (0, -0.1, 1), 0.14 * h, 0.06 * h, snap=False)
    # ember eyes in dark sockets under angry brows
    m.blob('Head', 'dark', Hd(0.3 * s, -0.95, 0.2), (0.17 * h, 0.08 * h, 0.15 * h), u=6, v=4)
    m.eye('Head', Hd(0.31 * s, -1.0, 0.2), (0.45 * s, -1, 0.15), 0.19 * h * st['eye'])
    m.box('Head', 'fur2', Hd(0.28 * s, -0.98, 0.38), (0.3 * h, 0.16 * h, 0.08 * h), rot=(10, 0, -28 * s), bevel=0.02 * h)
    m.socket(f'Eye{side}', 'Head', Hd(0.31 * s, -1.06, 0.2))
    # tall notched ears with dark inner skin
    e0 = Hd(0.42 * s, -0.25, 0.45)
    m.spike(f'Ear{side}', 'fur', e0, (0.32 * s, 0.12, 1), 0.95 * h, 0.5 * h, 0.14 * h, snap=False)
    m.spike(f'Ear{side}', 'ear_in', add(e0, (0, -0.06, 0.05)), (0.32 * s, 0.12, 1), 0.72 * h, 0.3 * h, 0.05 * h, snap=False)
    for k in range(2):  # gold hoops pierced through the ear
        ec = add(e0, (0.12 * s * h + 0.05 * s * k, 0.0, (0.22 + 0.16 * k) * h))
        hoop = [add(ec, (math.cos(TAU * q / 8) * 0.0, math.sin(TAU * q / 8) * 0.11 * h, math.cos(TAU * q / 8) * 0.11 * h - 0.11 * h)) for q in range(9)]
        hoop = [add(q_, (0.12 * s * h, 0, 0)) for q_ in hoop]
        m.loft(f'Ear{side}', 'gold', hoop, [(0.025 * h, 0.025 * h)] * 9, sides=4, steps=1, smooth=False, cap_round=0.0)
    for k in range(2):  # notches
        m.spike(f'Ear{side}', 'fur', add(e0, (0.12 * s + 0.08 * s * k, 0.0, 0.25 * h + 0.22 * h * k)), (s, 0.1, 0.3), 0.18 * h, 0.12 * h, 0.06 * h, snap=False)
# the candles fused into its skull: three melting pillars, dripping wax, the tallest one lit
CANDLES = ((0.0, 0.05, 0.85), (-0.24, 0.12, 0.55), (0.26, 0.0, 0.62))
for i, (cx, cy, height) in enumerate(CANDLES):
    height *= 0.6 + 0.4 * g
    base = Hd(cx, -0.35 + cy, 0.5)
    top = add(base, (0, 0, height * h))
    m.loft('Head', 'wax', [base, top], [(0.13 * h, 0.13 * h), (0.11 * h, 0.11 * h)], sides=7, steps=1, smooth=False, cap_round=0.15)
    m.blob('Head', 'wax', add(top, (0, 0, -0.02)), (0.12 * h, 0.12 * h, 0.05 * h), u=7, v=4)
    for k, ang in enumerate((0.3, 2.2, 4.1)):  # drips running down the side
        d0 = add(top, (math.cos(ang) * 0.11 * h, math.sin(ang) * 0.11 * h, -0.02))
        L = (0.25 + 0.2 * ((i + k) % 3)) * h
        m.loft('Head', 'wax', [d0, add(d0, (0, 0, -L))], [(0.035 * h, 0.035 * h), (0.045 * h, 0.045 * h)], sides=5, steps=1, smooth=False)
    m.loft('Head', 'wick', [top, add(top, (0, 0, 0.1 * h))], [(0.015, 0.015), (0.012, 0.012)], sides=4, steps=1, smooth=False)
    m.spike('Head', 'flame', add(top, (0, 0, 0.08 * h)), (0, 0, 1), (0.5 if i == 0 else 0.34) * h, 0.17 * h, snap=False)
    if i == 0:
        m.socket('Candle', 'Head', add(top, (0, 0, 0.22 * h)))
# wax pooled over the crown, running down the back of the head
for k, (x, y, z) in enumerate(((0.0, -0.3, 0.52), (-0.25, -0.15, 0.46), (0.22, -0.2, 0.46), (0.05, 0.05, 0.4))):
    m.blob('Head', 'wax', Hd(x, y, z), (0.2 * h, 0.17 * h, 0.06 * h), u=7, v=4)
m.loft('Head', 'wax', [Hd(0.1, 0.0, 0.42), Hd(0.15, 0.1, 0.15), Hd(0.12, 0.12, -0.15)], [(0.05 * h, 0.05 * h)] * 3, sides=5, steps=2, smooth=False)

# ---------------- wings ----------------
for side, s in SIDES:
    sh, el, wr = WING[side]
    bones_ = [f'Wing{side}', f'WingTip{side}']
    m.loft(bones_, 'bone', [sh, el, wr], [(0.11, 0.11), (0.09, 0.09), (0.06, 0.06)], sides=6, steps=2, smooth=False)
    m.blob(['Body', bones_[0]], 'fur', sh, (0.3, 0.3, 0.3), u=7, v=5)
    m.spike(bones_[0], 'claw', el, (0.2 * s, -0.4, 1), 0.32 * span, 0.1, snap=False)   # thumb claw
    # four bony fingers fanning down from the wrist; membrane between, scalloped at the edge
    tips = []
    for k in range(4):
        f = k / 3
        tips.append(add(wr, ((0.9 - 0.75 * f) * span * s, 0.15 + 0.35 * f, (-0.1 - 1.55 * f) * span)))
    for tip in tips:
        m.loft([bones_[1]], 'bone', [wr, tip], [(0.05, 0.05), (0.025, 0.025)], sides=4, steps=1, smooth=False)
    edges = [el] + [wr] + tips
    for a_, b_ in zip(tips, tips[1:]):
        mid = add(tuple((p + q) / 2 for p, q in zip(a_, b_)), (0, 0, 0))
        sag = tuple(mm + (w - mm) * 0.32 for mm, w in zip(mid, wr))
        m.strip([bones_[1]], 'wing', [wr, a_, a_], [wr, sag, b_], thickness=0.05)
    # inner membrane: from the body down the arm to the last finger
    m.strip(bones_, 'wing', [add(sh, (0, 0, -0.55)), sh, el, wr], [add(sh, (0, 0.15, -0.85)), add(el, (-0.3 * s, 0.1, -0.9 * span)),
            add(wr, (-0.1 * s, 0.25, -1.1 * span)), tips[-1]], thickness=0.05)
    m.socket(f'WingTip{side}', bones_[1], tips[0])
    # molten veins branching through the membrane, on both faces
    for a_, b_ in zip(tips, tips[1:]):
        mid = tuple((p + q) / 2 for p, q in zip(a_, b_))
        v1 = tuple(w + (mm - w) * 0.45 for w, mm in zip(wr, mid))
        v2 = tuple(w + (mm - w) * 0.8 for w, mm in zip(wr, mid))
        for face in (-1, 1):
            off = (0, 0.05 * face, 0)
            m.loft([bones_[1]], 'vein', [add(wr, off), add(v1, off), add(v2, off)], [(0.03, 0.03), (0.025, 0.025), (0.012, 0.012)], sides=4, steps=1, smooth=False)
            br = tuple(x + (y - x) * 0.6 for x, y in zip(v1, a_))
            m.loft([bones_[1]], 'vein', [add(v1, off), add(br, off)], [(0.02, 0.02), (0.01, 0.01)], sides=4, steps=1, smooth=False)
    for face in (-1, 1):   # and one down the inner membrane
        off = (0, 0.05 * face, 0)
        a0 = add(el, (-0.15 * s, 0.05, -0.3 * span))
        m.loft(bones_, 'vein', [add(add(sh, (0.1 * s, 0.05, -0.3)), off), add(a0, off), add(add(wr, (-0.2 * s, 0.2, -0.75 * span)), off)],
               [(0.03, 0.03), (0.025, 0.025), (0.012, 0.012)], sides=4, steps=1, smooth=False)
    # a little candle stub melted onto each wrist, lit
    cb = add(wr, (0, 0, 0.06))
    m.loft([bones_[1]], 'wax', [cb, add(cb, (0, 0, 0.26 * span))], [(0.07, 0.07), (0.06, 0.06)], sides=6, steps=1, smooth=False, cap_round=0.15)
    m.loft([bones_[1]], 'wax', [add(cb, (0.06, 0, 0.2 * span)), add(cb, (0.07, 0, 0.0))], [(0.025, 0.025), (0.03, 0.03)], sides=4, steps=1, smooth=False)
    m.spike(bones_[1], 'flame', add(cb, (0, 0, 0.28 * span)), (0, 0, 1), 0.24 * span, 0.09, snap=False)
    m.socket(f'WristCandle{side}', bones_[1], add(cb, (0, 0, 0.4 * span)))

# ---------------- legs ----------------
for side, s in SIDES:
    hip, foot = (0.3 * s, 0.25, HOVER - 0.45), (0.3 * s, 0.3, HOVER - 1.15)
    m.loft(f'Leg{side}', 'fur', [hip, foot], [(0.14, 0.14), (0.08, 0.08)], sides=5, steps=1, smooth=False)
    for k in (-1, 0, 1):
        m.spike(f'Leg{side}', 'claw', foot, (0.25 * k, -0.6, -0.8), 0.28, 0.07, snap=False)


# ---------------- animation ----------------
def wings(pose, flap, fold=0.0, tipk=0.7):
    for side, s in SIDES:
        pose[f'Wing{side}'] = ((0, -flap * s, fold * s), (0, 0, 0))
        pose[f'WingTip{side}'] = ((0, -flap * tipk * s, fold * 0.6 * s), (0, 0, 0))


def ears(pose, a):
    for side, s in SIDES:
        pose[f'Ear{side}'] = ((0, a * s, 0), (0, 0, 0))


def legs(pose, swing):
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((swing, 0, 0), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    beat = math.sin(p * 3)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (0.12 * math.sin(p * 3 - 0.8) + 0.05 * math.sin(p)) * S)),
        'Body': ((4 * math.sin(p), 0, 3 * math.sin(p * 0.5)), (0, 0, 0)),
        'Head': ((-3 * math.sin(p * 3 - 1.2), 0, 10 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((4 + 3 * math.sin(p * 2), 0, 0), (0, 0, 0)),
    }
    wings(pose, 35 * beat - 5)
    ears(pose, 4 * math.sin(p * 2))
    legs(pose, 8 * math.sin(p * 3 - 1.5))
    return pose


def walk(t_):   # gliding along: tilted forward, steady strong flaps
    p = TAU * t_
    beat = math.sin(p * 2)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (0.18 * math.sin(p * 2 - 0.8) + 0.1) * S)),
        'Body': ((14, 0, 4 * math.sin(p)), (0, 0, 0)),
        'Head': ((-12 - 4 * math.sin(p * 2 - 1.2), 0, 4 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((6, 0, 0), (0, 0, 0)),
    }
    wings(pose, 45 * beat)
    ears(pose, -8)
    legs(pose, 25)
    return pose


def run(t_):
    p = TAU * t_
    beat = math.sin(p * 3)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (0.22 * math.sin(p * 3 - 0.8) + 0.2) * S)),
        'Body': ((24, 0, 0), (0, 0, 0)),
        'Head': ((-20, 0, 0), (0, 0, 0)),
        'Jaw': ((10, 0, 0), (0, 0, 0)),
    }
    wings(pose, 55 * beat)
    ears(pose, -18)
    legs(pose, 45)
    return pose


def sleep(t_):   # settles low and wraps itself in its wings
    p = TAU * t_
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (-HOVER + 1.25 + 0.03 * math.sin(p)) * S)),
        'Body': ((4 + 2 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((22, 0, 0), (0, 0, 0)),
        'Jaw': ((0, 0, 0), (0, 0, 0)),
    }
    wings(pose, -40, -70, 1.3)
    ears(pose, 12)
    legs(pose, -10)
    return pose


def roar(t_):    # screech: wings flung wide, head thrown up, jaw open, shaking
    e = envelope(t_, 0.2, 0.75)
    sh = math.sin(TAU * 9 * t_) * envelope(t_, 0.25, 0.7, 0.8)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0.15 * S * e, 0.25 * S * e)),
        'Body': ((-14 * e, 0, 0), (0, 0, 0)),
        'Head': ((-26 * e, 0, 7 * sh), (0, 0, 0)),
        'Jaw': ((42 * e, 0, 0), (0, 0, 0)),
    }
    wings(pose, 30 * e + 6 * sh, -25 * e)
    ears(pose, -20 * e)
    legs(pose, -15 * e)
    return pose


def attack(t_):  # wind up, then dive at the target
    w = envelope(t_, 0.3, 0.32, 0.45)
    d = smooth01((t_ - 0.32) / 0.15) if t_ < 0.6 else 1 - smooth01((t_ - 0.6) / 0.4)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, (0.3 * w - 1.1 * d) * S, (0.4 * w - 0.6 * d) * S)),
        'Body': ((-12 * w + 30 * d, 0, 0), (0, 0, 0)),
        'Head': ((10 * w - 15 * d, 0, 0), (0, 0, 0)),
        'Jaw': ((10 * w + 35 * d, 0, 0), (0, 0, 0)),
    }
    wings(pose, 50 * w - 30 * d, 0, 0.7)
    legs(pose, 40 * d - 20 * w)
    return pose


def happy(t_):   # a loop-the-loop
    e = envelope(t_, 0.08, 0.85)
    flip = 360 * smooth01(t_ / 0.85) if t_ < 0.85 else 360
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.9 * S * math.sin(math.pi * min(1.0, t_ / 0.85)))),
        'Body': ((-flip, 0, 0), (0, 0, 0)),
        'Jaw': ((20 * e, 0, 0), (0, 0, 0)),
    }
    wings(pose, 40 * math.sin(TAU * 4 * t_) * e)
    ears(pose, 10 * math.sin(TAU * 4 * t_))
    return pose


m.anim('Idle', 60, True, idle, key_step=2)
m.anim('Walk', 30, True, walk, key_step=1)
m.anim('Run', 20, True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, roar, key_step=2)
m.anim('Attack', 36, False, attack, key_step=2)
m.anim('Happy', 42, False, happy, key_step=1)
m.refs = {'Walk': 2.6 * S / (30 / 30), 'Run': 4.2 * S / (20 / 30)}
m.build(OUT)
