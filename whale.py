"""Aurora Whale - Legendary Frost Peaks sky whale: a huge whale that floats through the air, swimming
with slow up-and-down strokes of its flukes. Deep night-blue back, pale pleated belly, long
pectoral fins edged with glowing aurora light, aurora bands down its back, a crown of ice crystals
and a gentle smile. Sings (jaw opens), and does a full barrel roll when happy. Faces -Y.
    blender -b --python whale.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: FinTipL/R + FinTrailL/R and FlukeL/R + FlukeTrailL/R (aurora trails), Blowhole (sparkle
spout), Aurora1-3 (glow along the back), Crown (ice glint)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('AuroraWhale', {
    'body': '#2c3878', 'body2': '#1f275a', 'belly': '#dfe9ff', 'pleat': '#a9bbe8', 'fin': '#33428c',
    'glow': ('#7dffc0', False), 'glow2': ('#b78cff', False), 'glow3': ('#7fd8ff', False), 'ice': ('#9ff4ff', False),
    'plate': ('#6fb8ea', True, True), 'tooth': ('#ffffff', False), 'dark': ('#0b0f26', False),
    'mouth': ('#141a40', False), 'eye_dark': ('#0b0f26', False), 'iris': ('#7dffc0', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.25, eye=1.4), 'Teen': dict(head=1.1, eye=1.15)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
Z = 5.5   # it floats: body centre height


def P(x, y, z):
    return (x, y, Z + z)


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Body', P(0, 1.0, 0), P(0, -3.0, 0.1), 'MonsterRoot')
m.bone('Head', P(0, -3.0, 0.1), P(0, -7.0, -0.1), 'Body')
m.bone('Jaw', P(0, -3.0, -1.0), P(0, -6.6, -1.2), 'Head')
m.bone('Tail1', P(0, 1.0, 0), P(0, 4.5, 0.15), 'Body')
m.bone('Tail2', P(0, 4.5, 0.15), P(0, 7.5, 0.3), 'Tail1')
m.bone('Fluke', P(0, 7.5, 0.3), P(0, 9.2, 0.4), 'Tail2')
for side, s in SIDES:
    m.bone(f'Fin{side}', P(2.3 * s, -1.5, -0.9), P(5.2 * s, 0.0, -1.9), 'Body')

# ---------------- body ----------------
# chunky style: a chiselled studded sky whale with an ice-armour helm, a great narwhal horn of ice,
# glowing eyes under armoured brows, a ridge of crystals down the spine, armour plates along the
# back, crystal clusters on the flanks, aurora bands and glowing fin edges
spine = [P(0, -7.15, -0.25), P(0, -6.4, -0.05), P(0, -4.2, 0.05), P(0, -1.0, 0.0), P(0, 2.0, 0.1), P(0, 4.6, 0.2),
         P(0, 7.0, 0.32), P(0, 8.3, 0.4)]
radii = [(1.2, 1.0), (2.3, 2.0), (2.95, 2.6), (3.05, 2.75), (2.5, 2.25), (1.6, 1.5), (0.75, 0.7), (0.4, 0.36)]
m.loft(['Head', 'Head', 'Head', 'Body', 'Body', 'Tail1', 'Tail2', 'Fluke'], 'body', spine,
       [(w * (h if i < 3 else 1), v * (h if i < 3 else 1)) for i, (w, v) in enumerate(radii)], sides=8, steps=3, smooth=False)
# pale belly with throat pleats
m.loft(['Jaw', 'Head', 'Body', 'Tail1'], 'belly',
       [P(0, -6.8, -0.75), P(0, -4.5, -1.55), P(0, -1.0, -1.75), P(0, 2.5, -1.3), P(0, 4.8, -0.7)],
       [(1.0, 0.45), (2.3, 0.9), (2.6, 1.0), (1.9, 0.8), (1.0, 0.45)], sides=6, steps=3, smooth=False)
for x in (-1.2, -0.6, 0.0, 0.6, 1.2):
    m.loft(['Jaw', 'Head'], 'pleat', [P(x * 0.8, -6.3, -1.2), P(x, -4.6, -2.25), P(x * 1.05, -2.6, -2.45)],
           [(0.09, 0.09)] * 3, sides=4, steps=3, smooth=False)
# mouth line with a row of little teeth, and glowing eyes under armoured brows
for side, s in SIDES:
    m.loft(['Jaw', 'Head'], 'mouth', [P(1.05 * s, -6.6, -0.75), P(2.25 * s, -4.9, -0.85), P(2.65 * s, -3.4, -0.55)],
           [(0.1, 0.1)] * 3, sides=4, steps=3, smooth=False)
    for k in range(4):
        m.spike('Head', 'tooth', P((1.3 + 0.38 * k) * s, -6.25 + 0.48 * k, -0.7), (0, 0, -1), 0.28, 0.14, snap=False)
    ex = 2.55 * s * (0.92 + 0.08 * h)
    m.box('Head', 'dark', P(ex * 0.98, -3.9, 0.15), (0.2, 1.1 * h, 0.9 * h), rot=(0, 0, -12 * s), bevel=0.06)
    m.eye('Head', P(ex * 1.02, -3.9, 0.15), (1 * s, -0.35, 0.05), 0.46 * h * st['eye'])
    m.box('Head', 'plate', P(ex * 0.93, -4.0, 0.85), (0.5, 1.6 * h, 0.32), rot=(14, 0, -12 * s), bevel=0.06)
# ice-armour helm over the head and a great narwhal horn
m.box('Head', 'plate', P(0, -5.6, 1.95 * h), (2.3 * h, 2.0, 0.42), rot=(-24, 0, 0), bevel=0.1)
m.box('Head', 'plate', P(0, -3.9, 2.55 * h), (2.4 * h, 1.7, 0.38), rot=(-6, 0, 0), bevel=0.08)
hl = 1.6 + 2.6 * g
m.loft('Head', 'ice', [P(0, -6.6, 1.25), P(0, -6.6 - 0.45 * hl, 1.25 + 0.2 * hl), P(0, -6.6 - hl, 1.25 + 0.45 * hl)],
       [(0.42, 0.42), (0.26, 0.26), (0.02, 0.02)], sides=5, steps=3, smooth=False)
m.loft('Head', 'glow3', [P(0.2, -6.7, 1.45), P(0.12, -6.6 - 0.45 * hl, 1.43 + 0.2 * hl), P(0.03, -6.6 - 0.9 * hl, 1.3 + 0.42 * hl)],
       [(0.06, 0.06)] * 3, sides=4, steps=3, smooth=False)
# a crown of ice crystals and the blowhole
for d, k, x in (((0, 0.3, 1), 1.0, 0.0), ((0.5, 0.2, 1), 0.75, 0.45), ((-0.5, 0.2, 1), 0.75, -0.45),
                ((0.9, 0.5, 0.8), 0.55, 0.85), ((-0.9, 0.5, 0.8), 0.55, -0.85)):
    m.spike('Head', 'ice', P(x, -4.6, 2.35), d, (0.8 + 1.2 * g) * k, 0.5 * k, twist=45)
m.socket('Crown', 'Head', P(0, -4.4, 4.0))
m.box('Head', 'body2', P(0, -3.0, 2.62), (0.7, 0.5, 0.16), bevel=0.04)
m.socket('Blowhole', 'Head', P(0, -3.0, 2.8))
# aurora bands wrapping over the back (sampled on the body's surface)
for i, (y, rx, rz, bone) in enumerate(((-1.5, 3.05, 2.75, 'Body'), (0.9, 2.7, 2.45, 'Body'), (3.1, 2.0, 1.85, 'Tail1'))):
    col = ('glow', 'glow2', 'glow3')[i]
    zc = 0.02 + 0.06 * i
    pts = []
    for k in range(9):
        a = math.radians(-70 + 140 * k / 8)
        pts.append(P(rx * 1.01 * math.sin(a), y + 0.15 * abs(math.sin(a)), zc + rz * 1.01 * math.cos(a)))
    m.loft(bone, col, pts, [(0.26, 0.14)] * len(pts), sides=4, steps=2, smooth=False)
    m.socket(f'Aurora{i + 1}', bone, P(0, y, zc + rz + 0.3))
# a ridge of crystals down the spine, armour plates either side, crystal clusters on the flanks
for y, z, k, bone in ((-2.4, 2.8, 1.0, 'Body'), (-0.3, 2.85, 0.9, 'Body'), (2.0, 2.4, 0.75, 'Body'), (4.0, 1.75, 0.55, 'Tail1'),
                      (5.6, 1.15, 0.4, 'Tail2')):
    m.spike(bone, 'ice', P(0, y, z), (0, 0.35, 1), (0.6 + 1.0 * g) * k, 0.5 * k, twist=45)
for side, s in SIDES:
    if g > 0.25:
        for y, z in ((-0.8, 0.2), (1.6, -0.2)):
            for d, k in (((s, 0, 0.3), 1.0), ((s, 0.4, 0.8), 0.7), ((s, -0.4, -0.2), 0.6)):
                m.spike('Body', 'ice', P(2.9 * s, y, z), d, (0.5 + 0.6 * g) * k, 0.35 * k, twist=45)
m.spike('Tail1', 'body2', P(0, 3.6, 1.45), (0, 1, 0.6), 1.0, 0.7, 0.18)

# long pectoral fins with glowing edges, and the flukes
fin_k = 0.7 + 0.3 * g
for side, s in SIDES:
    root, mid, tip = P(2.3 * s, -1.5, -0.9), P((2.3 + 1.5 * fin_k) * s, -0.8, -1.4), P((2.3 + 2.9 * fin_k) * s, 0.05, -1.9)
    m.loft(f'Fin{side}', 'fin', [root, mid, tip], [(1.3, 0.24), (1.0, 0.19), (0.32, 0.09)], sides=4, steps=3,
           smooth=False, up=(0, 0, 1))
    m.loft(f'Fin{side}', 'glow' if s > 0 else 'glow2', [add(root, (0, 1.25, 0)), add(mid, (0, 0.98, 0)), add(tip, (0, 0.32, 0))],
           [(0.14, 0.14), (0.12, 0.12), (0.07, 0.07)], sides=4, steps=3, smooth=False)
    for u in (0.3, 0.6):
        p = tuple(a + (b - a) * u for a, b in zip(root, tip))
        m.spike(f'Fin{side}', 'ice', add(p, (0, -0.9 * (1 - u) - 0.2, 0.1)), (0.3 * s, -1, 0.2), 0.6 * fin_k, 0.25, twist=45)
    m.socket(f'FinTip{side}', f'Fin{side}', tip)
    m.socket(f'FinTrail{side}', f'Fin{side}', add(mid, (0, 0.98, 0)))
    f0, f1, f2 = P(0.2 * s, 8.5, 0.4), P(1.9 * s, 9.35, 0.45), P(3.2 * s, 9.95, 0.55)
    m.loft('Fluke', 'fin', [f0, f1, f2], [(1.25, 0.2), (1.0, 0.16), (0.4, 0.08)], sides=4, steps=3, smooth=False, up=(0, 0, 1))
    m.loft('Fluke', 'glow3', [add(f0, (0, 1.2, 0)), add(f1, (0, 0.98, 0)), add(f2, (0, 0.38, 0))],
           [(0.12, 0.12), (0.1, 0.1), (0.06, 0.06)], sides=4, steps=3, smooth=False)
    m.socket(f'Fluke{side}', 'Fluke', f2)
    m.socket(f'FlukeTrail{side}', 'Fluke', add(f1, (0, 0.98, 0)))


# ---------------- animation ----------------
WALK = dict(stride=3.0, frames=72)
RUN = dict(stride=5.5, frames=40)


def fins(pose, up, sweep=0.0):
    for side, s in SIDES:
        pose[f'Fin{side}'] = ((sweep, -up * s, 0), (0, 0, 0))


def swim(t_, amp, bob):
    p = TAU * t_
    pose = {
        'Body': ((3 * amp * math.sin(p + 1.2), 2 * math.sin(p * 0.5), 0), (0, 0, bob * S * math.sin(p + 0.4))),
        'Head': ((-3 * amp * math.sin(p + 1.6), 0, 0), (0, 0, 0)),
        'Tail1': ((8 * amp * math.sin(p), 0, 0), (0, 0, 0)),
        'Tail2': ((12 * amp * math.sin(p - 0.7), 0, 0), (0, 0, 0)),
        'Fluke': ((16 * amp * math.sin(p - 1.4), 0, 0), (0, 0, 0)),
        'Jaw': ((0, 0, 0), (0, 0, 0)),
    }
    fins(pose, 14 * amp * math.sin(p + 0.5), 6 * amp * math.sin(p))
    return pose


def sing(t_):
    e = envelope(t_, 0.25, 0.75)
    p = TAU * t_
    pose = swim(t_, 0.4, 0.15)
    pose['Body'] = ((-10 * e, 0, 0), (0, 0, 0.6 * S * e))
    pose['Head'] = ((-6 * e, 0, 0), (0, 0, 0))
    pose['Jaw'] = ((8 * e * (0.7 + 0.3 * math.sin(TAU * 4 * t_)), 0, 0), (0, 0, 0))
    fins(pose, 30 * e + 8 * math.sin(p * 3) * e)
    return pose


def barrel_roll(t_):
    # a full roll about its own length, rising a little
    q = smooth01(t_ / 0.85)
    pose = swim(t_, 0.6, 0.0)
    pose['Body'] = ((0, 360 * q, 0), (0, 0, 1.0 * S * math.sin(math.pi * q)))
    fins(pose, 25 * math.sin(math.pi * q))
    return pose


def sleep(t_):
    pose = swim(t_, 0.2, 0.1)
    pose['Body'] = ((4, 0, 0), (0, 0, -1.2 * S + 0.1 * S * math.sin(TAU * t_)))
    fins(pose, -10)
    return pose


m.anim('Idle', 120, True, lambda t_: swim(t_, 0.45, 0.25), key_step=3)
m.anim('Walk', WALK['frames'], True, lambda t_: swim(t_, 1.0, 0.35), key_step=2)
m.anim('Run', RUN['frames'], True, lambda t_: swim(t_, 1.5, 0.45), key_step=2)
m.anim('Sleep', 120, True, sleep, key_step=8)
m.anim('Roar', 72, False, sing, key_step=2)
m.anim('Attack', 40, False, sing, key_step=2)
m.anim('Happy', 54, False, barrel_roll, key_step=1)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
