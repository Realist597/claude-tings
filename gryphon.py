"""Gryphon - Uncommon Mythic storm gryphon: a white eagle's head with a huge hooked gold beak, glowing
cyan eyes in dark sockets under angry gold brow plates and a tall spiky crest, on a dark slate lion
body in outlined gold armour (helm, breastplate with a gem, shoulder guards, knee plates). Big dark
wings crackle with glowing cyan lightning zigzags and cyan-tipped primaries; the tufted tail ends in a
glowing storm orb. Faces -Y. Wings: Wing/WingTip bones per side.
Sockets: WingTipL/R + WingTrailL/R (flap trails), Gem, TailOrb."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, TAU
from kit import envelope


def lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def bones(c):
    m, bW, bL, bH, g = c.m, c.bW, c.bL, c.bH, c.grow
    span = 0.55 + 0.45 * g
    for side, s in c.SIDES:
        sh = (0.75 * bW * s, -0.65 * bL, c.bodyZ + 1.0 * bH)
        el = (sh[0] + 1.9 * span * s, sh[1] + 0.6, sh[2] + 1.6 * span)
        tip = (el[0] + 2.1 * span * s, el[1] + 1.4, el[2] + 0.3 * span)
        m.bone(f'Wing{side}', sh, el, 'Chest')
        m.bone(f'WingTip{side}', el, tip, f'Wing{side}')
        c.__dict__[f'wing{side}'] = (sh, el, tip)


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    m.box('Head', 'feather', H(0, -0.8, 0.15), (1.5 * h, 1.7 * h, 1.45 * h), bevel=0.4 * h, segs=1)
    # big hooked gold beak: a deep upper bill curling down over a short lower one
    m.box('Head', 'beak', H(0, -1.8, 0.0), (0.75 * h, 1.05 * h, 0.85 * h), bevel=0.15 * h, taper=dict(axis='y', end=-1, scale=(0.55, 0.7)))
    m.spike('Head', 'beak', H(0, -2.3, 0.2), (0, -0.5, -1), 0.95 * h, 0.5 * h, 0.38 * h, snap=False)
    m.box('Head', 'beak2', H(0, -1.75, 0.38), (0.5 * h, 0.8 * h, 0.12 * h), bevel=0.04 * h, taper=dict(axis='y', end=-1, scale=(0.5, 1)))
    m.box('Jaw', 'beak', H(0, -1.6, -0.5), (0.55 * h, 0.9 * h, 0.22 * h), bevel=0.06 * h, taper=dict(axis='y', end=-1, scale=(0.6, 0.8)))
    for side, s in c.SIDES:
        # glowing eyes in dark sockets, under angry gold brow plates
        m.box('Head', 'dark', H(0.72 * s, -1.05, 0.33), (0.14 * h, 0.55 * h, 0.42 * h), rot=(0, 0, 10 * s), bevel=0.03 * h)
        m.eye('Head', H(0.8 * s, -1.05, 0.33), (0.85 * s, -0.5, 0.1), 0.24 * h * c.eye)
        m.box('Head', 'gold', H(0.6 * s, -1.1, 0.72), (0.5 * h, 0.62 * h, 0.14 * h), rot=(18, 0, -22 * s), bevel=0.03 * h)
        # swept feather crest: white blades with dark tips, getting longer towards the back
        for k in range(4):
            m.spike('Head', 'feather' if k % 2 == 0 else 'feather2', H(0.3 * s, -0.4 + 0.18 * k, 0.75 - 0.12 * k),
                    (0.35 * s, 1.0, 0.55 - 0.15 * k), (0.7 + 0.55 * g) * h * (1 - 0.1 * k), 0.32 * h, 0.08 * h)
    # gold helm down the forehead with a glowing storm gem, and a glowing centre crest blade
    m.box('Head', 'gold', H(0, -0.75, 0.82), (0.55 * h, 1.0 * h, 0.2 * h), rot=(-8, 0, 0), bevel=0.05 * h)
    m.box('Head', 'glow', H(0, -1.15, 0.9), (0.24 * h, 0.14 * h, 0.24 * h), rot=(0, 45, 0), bevel=0.03 * h)
    m.spike('Head', 'glow', H(0, -0.3, 0.85), (0, 0.9, 0.8), (0.8 + 0.6 * g) * h, 0.3 * h, 0.08 * h)


def decor(c):
    m, g = c.m, c.grow
    # white feather ruff where the eagle meets the lion
    for i in range(10):
        a = math.pi * (i / 9)
        x = math.cos(a) * 1.1 * c.bW
        z = c.neckStart[2] - 0.2 + math.sin(a) * 0.9
        m.spike('Neck', 'feather', (x, c.neckStart[1] + 0.2, z), (x * 0.4, 0.8, math.sin(a) * 0.6 - 0.4), 0.85 * (0.6 + 0.4 * g), 0.45, 0.1)
    # gold collar, a breastplate hanging from it with a glowing gem, and shoulder guards
    nc = c.add(c.neckStart, (0, 0.05, -0.05))
    ring = [(math.cos(TAU * i / 16) * 1.05 * c.bW, nc[1], nc[2] + math.sin(TAU * i / 16) * 0.95 * c.bH) for i in range(17)]
    m.loft('Chest', 'gold', ring, [(0.14, 0.2)] * len(ring), sides=6, steps=1, smooth=False, cap_round=0.0)
    chest = (0, nc[1] - 0.25, nc[2] - 0.75 * c.bH)
    m.box('Chest', 'gold', chest, (0.95 * c.bW, 0.25, 0.85), rot=(12, 0, 0), bevel=0.06)
    m.box('Chest', 'glow', (0, chest[1] - 0.15, chest[2]), (0.28, 0.12, 0.34), rot=(12, 0, 45), bevel=0.03)
    m.socket('Gem', 'Chest', (0, chest[1] - 0.3, chest[2]))
    for side, s in c.SIDES:
        p = c.body_pt(-1.0, 3.5)
        m.box('Chest', 'gold', (1.0 * c.bW * s, p[1], p[2] - 0.2), (0.75, 0.85, 0.2), rot=(0, 55 * s, 0), bevel=0.05)
        m.box('Chest', 'body2', (1.05 * c.bW * s, p[1] - 0.05, p[2] - 0.17), (0.45, 0.5, 0.2), rot=(0, 55 * s, 0), bevel=0.03)
    # tufted lion tail ending in a glowing storm orb
    m.blob('Tail3', 'tuft', c.tailEnd, (0.42, 0.55, 0.42), u=8, v=6)
    for d in ((0, 1, 0.3), (0.5, 0.9, 0), (-0.5, 0.9, 0), (0, 0.8, -0.5)):
        m.spike('Tail3', 'tuft', c.tailEnd, d, 0.55, 0.3, 0.15)
    orb = c.add(c.tailEnd, (0, 0.75, 0.2))
    m.blob('Tail3', 'glow', orb, (0.38, 0.38, 0.38), u=8, v=6)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):   # little gold clasp spikes round the orb
        m.spike('Tail3', 'gold', c.add(orb, (0, -0.25, 0)), d, 0.3, 0.14, 0.08)
    m.socket('TailOrb', 'Tail3', orb)
    # dark feathered wings with cyan lightning crackling across them
    span = 0.55 + 0.45 * g
    for side, s in c.SIDES:
        sh, el, tip = c.__dict__[f'wing{side}']
        bones_ = [f'Wing{side}', f'WingTip{side}']
        lead, trail = [], []
        n = 12
        for i in range(n):
            u = i / (n - 1)
            a, b, f = (sh, el, u / 0.45) if u <= 0.45 else (el, tip, (u - 0.45) / 0.55)
            p = lerp(a, b, f)
            lead.append(p)
            chord = (2.3 * (1 - u) ** 0.6 + 0.4) * span
            trail.append((p[0] + 0.1 * s * chord, p[1] + chord, p[2] - 0.45 * chord))
        m.strip(bones_, 'feather2', lead, trail, thickness=0.14)
        m.strip(bones_, 'body2', lead, [lerp(lead[i], trail[i], 0.4) for i in range(n)], thickness=0.18)
        # lightning: a zigzag band across the wing, glowing through both faces
        zig, zig2 = [], []
        for i in range(1, n - 1):
            f = 0.55 + (0.12 if i % 2 else -0.12)
            q = lerp(lead[i], trail[i], f)
            zig.append(q)
            zig2.append(lerp(lead[i], trail[i], f + 0.07))
        m.strip(bones_, 'glow', zig, zig2, thickness=0.22)
        m.loft(bones_, 'gold', [sh, el, tip], [(0.2, 0.2), (0.15, 0.15), (0.07, 0.07)], sides=6, steps=3, smooth=False)
        # long primaries off the tip, every other one glowing
        for k, u in enumerate((0.55, 0.65, 0.75, 0.85, 0.95)):
            i = min(n - 1, int(u * (n - 1)))
            d = (0.25 * s, 1.0, -0.35 - 0.1 * k)
            m.spike(bones_[1], 'glow' if k % 2 else 'feather3', trail[i], d, (1.0 + 0.2 * k) * span, 0.36, 0.06, snap=False)
        m.socket(f'WingTip{side}', bones_[1], tip)
        m.socket(f'WingTrail{side}', bones_[1], trail[-2])
        m.blob(['Chest', bones_[0]], 'gold', sh, (0.45, 0.45, 0.42), u=8, v=5)


def pose(c, clip, t, p):
    if clip == 'Idle':
        up, fold, tipf = 6 * math.sin(TAU * t), 22, 4 * math.sin(TAU * t - 0.6)
    elif clip == 'Walk':
        up, fold, tipf = -4 + 4 * math.sin(TAU * 2 * t), 30, 8
    elif clip == 'Run':
        up, fold, tipf = 36 * math.sin(TAU * t), 0, 22 * math.sin(TAU * t - 0.9)
    elif clip == 'Sleep':
        up, fold, tipf = -30, 45, 35
    elif clip == 'Roar':
        e = envelope(t, 0.2, 0.75)
        up, fold, tipf = 45 * e + 5 * math.sin(TAU * 6 * t) * e, -15 * e, -10 * e
    elif clip == 'Attack':
        w = envelope(t, 0.3, 0.5, 0.9)
        up, fold, tipf = 30 * w, -10 * w, -12 * w
    else:
        up, fold, tipf = 30 * math.sin(TAU * 3 * t) * envelope(t, 0.1, 0.7), 0, 15 * math.sin(TAU * 3 * t - 0.8)
    for side, s in c.SIDES:
        p[f'Wing{side}'] = ((0, -up * s, fold * s), (0, 0, 0))
        p[f'WingTip{side}'] = ((0, -tipf * s, fold * 0.6 * s), (0, 0, 0))


build(dict(
    sides=6,
    kneePlates='gold',
    name='Gryphon',
    palette={
        'body': '#3b4060', 'body2': ('#262a42', True, True), 'belly': '#5d6488', 'feather': '#eef1f8',
        'feather2': ('#2c3150', True, True), 'feather3': ('#151827', False),
        'beak': ('#ffc23a', False, True), 'beak2': ('#ffe08a', False), 'gold': ('#ffcf3a', False, True),
        'glow': ('#5ff2ff', False), 'dark': ('#0e1018', False),
        'tuft': '#20233a', 'foot': '#ffc23a', 'claw': ('#101015', False), 'mouth': '#7a3a4a', 'tongue': '#d6405c',
        'eye_dark': ('#0e1018', False), 'iris': ('#5ff2ff', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.1, legT=0.95, bL=1.05, bW=0.92, bH=0.95, girth=1.0, head=0.95, neck=1.1, neckUp=1.8,
              tail=1.1, tailDroop=1.1, eye=1.0),
    neckRadius=0.85,
    gait=dict(stride=1.2),
    bones=bones, head=head, decor=decor, pose=pose,
))
