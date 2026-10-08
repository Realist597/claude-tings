"""Snowy Owl - Rare Frost Peaks owl: round white body with dark speckles, a big swivelling head with
a facial disc and huge yellow eyes, icy ear tufts, wings that fold against the body and open into a
full spread, feathered legs with talons. Owlets are fluffy and grey. Hops on the ground, flaps low
over it when running, turns its head almost all the way round. Faces -Y.
    blender -b --python owl.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: FrostL/FrostR (ear tuft crystals), WingTipL/WingTipR + WingTrailL/WingTrailR (flap trails)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('SnowyOwl', {
    'body': '#f2f5fb', 'wing': '#e6ecf5', 'bar': '#2c3446', 'fluff': '#aab2c2', 'face': '#ffffff',
    'beak': ('#2a2f3a', False), 'talon': ('#1c1f28', False), 'foot': '#c9d0de', 'ice': ('#8ff0ff', False),
    'plate': ('#6fb8ea', True, True), 'feather': ('#cfd9ea', True, True), 'dark': ('#0d1222', False),
    'eye_dark': ('#0d1222', False), 'iris': ('#ffc21a', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.3, eye=1.25), 'Teen': dict(head=1.1, eye=1.1)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
owlet = st['stage'] == 'Child'
coat = 'fluff' if owlet else 'body'
SIDES = (('L', 1), ('R', -1))
HEAD = (0, -0.15, 3.85 + 0.35 * (h - 1))


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0.2, 1.2), (0, 0, 2.4), 'MonsterRoot')
m.bone('Chest', (0, 0, 2.4), (0, -0.1, 3.25), 'Hips')
m.bone('Head', (0, -0.1, 3.25), Hd(0, -1.0, 0.1), 'Chest')
m.bone('Tail', (0, 0.8, 1.5), (0, 1.75, 0.85), 'Hips')
span = 0.7 + 0.3 * g
for side, s in SIDES:
    sh = (1.0 * s, 0.05, 3.0)
    wr = (1.22 * s, 0.35, 3.0 - 1.15 * span)
    tip = (1.05 * s, 1.05, 3.0 - 2.25 * span)
    m.bone(f'Wing{side}', sh, wr, 'Chest')
    m.bone(f'WingTip{side}', wr, tip, f'Wing{side}')
    m.bone(f'Leg{side}', (0.45 * s, 0.0, 1.05), (0.45 * s, -0.1, 0.35), 'Hips')
    m.bone(f'Foot{side}', (0.45 * s, -0.1, 0.35), (0.45 * s, -0.65, 0.05), f'Leg{side}')

# ---------------- body ----------------
# chunky style: a chiselled studded body, a boxy head with a flat facial disc, huge glowing amber eyes
# under heavy dark brows, a big hooked beak, icy horn tufts, ice-armoured shoulders, crystal-tipped
# flight feathers and big talons
m.loft(['Hips', 'Chest', 'Head'], coat,
       [(0, 0.15, 0.75), (0, 0.05, 1.6), (0, 0, 2.5), (0, -0.05, 3.15), Hd(0, 0.05, -0.35)],
       [(0.82, 0.78), (1.22, 1.12), (1.15, 1.05), (0.98, 0.92), (0.9 * h, 0.85 * h)],
       sides=7, steps=3, smooth=False, up=(0, -1, 0))
m.box(['Hips', 'Chest'], 'face', (0, -0.95, 1.8), (1.3, 0.3, 1.5), bevel=0.15)
# chevron chest bars
if not owlet:
    for z in (1.4, 1.8, 2.2):
        for side, s in SIDES:
            m.box(['Hips', 'Chest'], 'bar', (0.28 * s, -1.08, z), (0.4, 0.06, 0.08), rot=(0, 25 * s, 0), bevel=0.0)
# head
m.box('Head', coat, Hd(0, 0, 0), (2.2 * h, 2.0 * h, 1.9 * h), bevel=0.3 * h, segs=1)
m.box('Head', 'face', Hd(0, -0.98, -0.05), (1.75 * h, 0.12 * h, 1.45 * h), bevel=0.12 * h)
for side, s in SIDES:
    m.box('Head', 'dark', Hd(0.42 * s, -1.04, 0.08), (0.78 * h, 0.06 * h, 0.72 * h), bevel=0.06 * h)
    m.eye('Head', Hd(0.42 * s, -1.08, 0.08), (0.15 * s, -1, 0.05), 0.4 * h * st['eye'])
    # heavy brows: thick bars slanting down to the beak
    m.box('Head', 'bar', Hd(0.46 * s, -1.1, 0.56), (0.85 * h, 0.16 * h, 0.2 * h), rot=(0, -22 * s, 0), bevel=0.03 * h)
    # icy horn tufts
    tip = Hd(0.75 * s, -0.15, 1.35)
    m.spike('Head', 'ice', Hd(0.62 * s, -0.2, 0.85), (0.5 * s, 0.15, 1), (0.5 + 0.45 * g) * h, 0.26 * h, twist=45)
    m.spike('Head', 'ice', Hd(0.45 * s, 0.0, 0.9), (0.2 * s, 0.4, 1), (0.3 + 0.3 * g) * h, 0.18 * h, twist=45)
    m.spike('Head', 'feather', Hd(0.8 * s, 0.1, 0.7), (0.8 * s, 0.4, 0.7), 0.5 * h, 0.22 * h, 0.08 * h)
    m.socket(f'Frost{side}', 'Head', tip)
m.spike('Head', 'beak', Hd(0, -1.12, -0.12), (0, -0.4, -1), 0.6 * h, 0.34 * h, 0.26 * h, snap=False)
m.box('Head', 'beak', Hd(0, -1.12, 0.04), (0.34 * h, 0.2 * h, 0.22 * h), bevel=0.04 * h)

if owlet:
    for a in range(12):
        ang = a * TAU / 12
        z = 1.0 + 0.7 * (a % 3)
        m.spike(['Hips', 'Chest'][a % 2], 'fluff', (math.cos(ang) * 1.1, math.sin(ang) * 1.0, z),
                (math.cos(ang), math.sin(ang), 0.5), 0.4, 0.3, 0.2)
else:
    # dark speckle bars on the flanks and back
    for i in range(12):
        ang = 1.3 + (i % 6) * 0.6 + (0.3 if i >= 6 else 0)
        z = 1.3 + 0.6 * (i % 3) + (0.3 if i >= 6 else 0)
        r = 1.15 - 0.08 * abs(z - 2.0)
        m.box(['Hips', 'Chest'][int(z > 2.4)], 'bar', (math.cos(ang) * r, math.sin(ang) * r * 0.95, z),
              (0.24, 0.07, 0.07), rot=(0, 0, math.degrees(ang) + 90), bevel=0.0)

# wings: a feathered panel per side folded along the body; scalloped trailing edge, dark bars
for side, s in SIDES:
    sh = (1.0 * s, 0.05, 3.0)
    wr = (1.22 * s, 0.35, 3.0 - 1.15 * span)
    tip = (1.05 * s, 1.05, 3.0 - 2.25 * span)
    bones = [f'Wing{side}', f'WingTip{side}']
    lead, trail = [], []
    n = 11
    for i in range(n):
        u = i / (n - 1)
        a, b, f = (sh, wr, u / 0.5) if u <= 0.5 else (wr, tip, (u - 0.5) / 0.5)
        p = tuple(x + (y - x) * f for x, y in zip(a, b))
        lead.append(p)
        chord = (1.05 * (1 - u) ** 0.6 + 0.12) * span * (0.85 + 0.15 * abs(math.cos(u * 4 * math.pi)))
        trail.append(add(p, (0.12 * s * chord, chord, 0.15 * chord)))
    m.strip(bones, 'wing', lead, trail, thickness=0.18)
    m.loft(bones, 'wing', [sh, wr, tip], [(0.2, 0.2), (0.15, 0.15), (0.06, 0.06)], sides=4, steps=3, smooth=False)
    for k, u in enumerate((0.35, 0.55, 0.75, 0.9)):
        i = int(u * (n - 1))
        mid = tuple((x + y) / 2 for x, y in zip(lead[i], trail[i]))
        m.box(bones[0] if u < 0.5 else bones[1], 'bar', add(mid, (0.1 * s, 0, 0)), (0.06, 0.5 * span, 0.12), bevel=0.02)
        # ice-tipped flight feathers along the trailing edge
        m.spike(bones[0] if u < 0.5 else bones[1], 'feather' if k % 2 else 'ice', trail[i], (0.1 * s, 1, -0.5), (0.35 + 0.3 * g) * span, 0.2, 0.06, snap=False)
    m.socket(f'WingTip{side}', bones[1], tip)
    m.socket(f'WingTrail{side}', bones[1], trail[-3])
    m.blob(['Chest', bones[0]], coat, sh, (0.4, 0.4, 0.38), u=6, v=4, smooth=False)
    if not owlet:
        m.box(['Chest', bones[0]], 'plate', add(sh, (0.12 * s, 0, 0.18)), (0.55, 0.7, 0.2), rot=(0, 30 * s, 0), bevel=0.05)
        m.spike(['Chest', bones[0]], 'ice', add(sh, (0.3 * s, 0, 0.3)), (0.7 * s, 0.1, 0.8), 0.5 * g + 0.15, 0.18, twist=45)

# tail fan, feathered legs, big talons
for yaw in (-0.4, -0.13, 0.13, 0.4):
    m.spike('Tail', 'feather', (0, 0.8, 1.45), (yaw, 1.0, -0.55), (0.85 + 0.4 * g), 0.4, 0.1, snap=False)
for side, s in SIDES:
    m.loft([f'Leg{side}'], coat, [(0.45 * s, 0.0, 1.05), (0.45 * s, -0.08, 0.4)], [(0.34, 0.34), (0.26, 0.26)],
           sides=5, steps=1, smooth=False, up=(0, -1, 0))
    m.box(f'Foot{side}', 'foot', (0.45 * s, -0.25, 0.16), (0.5, 0.6, 0.3), bevel=0.06)
    for dx in (-0.18, 0.0, 0.18):
        m.spike(f'Foot{side}', 'talon', (0.45 * s + dx, -0.52, 0.14), (dx, -1, -0.6), 0.38, 0.12, snap=False)
    m.spike(f'Foot{side}', 'talon', (0.45 * s, 0.05, 0.12), (0, 1, -0.6), 0.3, 0.12, snap=False)


# ---------------- animation ----------------
WALK = dict(stride=1.0, frames=24)
RUN = dict(stride=4.0, frames=20)


def wings(pose, spread, fold=0.0, tip=0.0, flap_fwd=0.0):
    """spread 0 = folded on the body, 90 = straight out to the side"""
    for side, s in SIDES:
        pose[f'Wing{side}'] = ((flap_fwd, -spread * s, fold * s), (0, 0, 0))
        pose[f'WingTip{side}'] = ((0, -tip * s, 0), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    # the owl head-turn: look over one shoulder, hold, swing round to the other, back to front
    look = 110 * (smooth01((t_ - 0.15) / 0.12) - smooth01((t_ - 0.45) / 0.15) * 1.6 + smooth01((t_ - 0.8) / 0.12) * 0.6)
    tilt = 18 * E * math.sin(TAU * t_ * 2) * envelope(t_, 0.6, 0.8)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0.03 * S * math.sin(2 * p))),
        'Chest': ((1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((0, tilt, look), (0, 0, 0)),
        'Tail': ((0, 0, 6 * math.sin(2 * p)), (0, 0, 0)),
    }
    wings(pose, 3 + 3 * math.sin(2 * p))
    return pose


def walk(t_):
    # small two-footed hops with the wings held a little open for balance
    u = t_ % 1.0
    hop = math.sin(math.pi * u) if u < 0.6 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.45 * S * E * hop)),
        'Hips': ((-6 * hop, 0, 0), (0, 0, 0)),
        'Head': ((6 * hop, 0, 8 * math.sin(TAU * u)), (0, 0, 0)),
        'Tail': ((-10 * hop, 0, 0), (0, 0, 0)),
    }
    wings(pose, 18 + 22 * hop, tip=10 * hop)
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((20 * hop, 0, 0), (0, 0, 0))
        pose[f'Foot{side}'] = ((-25 * hop, 0, 0), (0, 0, 0))
    return pose


def run(t_):
    # low flapping flight just over the ground
    p = TAU * t_
    beat = math.sin(p)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (1.2 + 0.25 * beat) * S)),
        'Hips': ((35, 0, 0), (0, 0, 0)),
        'Head': ((-32, 0, 0), (0, 0, 0)),
        'Tail': ((-15, 0, 0), (0, 0, 0)),
    }
    wings(pose, 92 + 38 * beat, tip=25 * math.sin(p - 0.8), flap_fwd=-10)
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((55, 0, 0), (0, 0, 0))   # talons tucked back
        pose[f'Foot{side}'] = ((40, 0, 0), (0, 0, 0))
    return pose


def happy(t_):
    e = envelope(t_, 0.1, 0.75)
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.6 * S * E * hop)),
        'Head': ((-8 * e, 22 * e * math.sin(TAU * 2 * t_), 0), (0, 0, 0)),
        'Tail': ((0, 0, 20 * math.sin(TAU * 4 * t_) * e), (0, 0, 0)),
    }
    wings(pose, 60 * e + 40 * e * math.sin(TAU * 4 * t_), tip=20 * e)
    return pose


def sleep(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 0, 0), (0, 0, -0.2 * S + 0.03 * S * math.sin(p))),
        'Chest': ((4 + 1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((15, 0, 150), (0, 0, 0)),   # head turned round and tucked into the back
    }
    wings(pose, -4)
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((0, 0, 0), (0, 0, 0.15 * S))
    return pose


def display(t_):
    # threat display: wings thrown wide, head low and forward
    e = envelope(t_, 0.2, 0.75)
    pose = {
        'Hips': ((10 * e, 0, 0), (0, 0, 0)),
        'Head': ((15 * e, 0, 8 * math.sin(TAU * 6 * t_) * e), (0, 0, 0)),
    }
    wings(pose, 95 * e + 8 * math.sin(TAU * 6 * t_) * e, tip=15 * e, flap_fwd=-20 * e)
    return pose


m.anim('Idle', 96, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, walk, key_step=1)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, display, key_step=2)
m.anim('Attack', 30, False, display, key_step=2)
m.anim('Happy', 40, False, happy, key_step=2)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
