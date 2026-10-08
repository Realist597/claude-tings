"""Thornhorn - Forest biome quadruped (triceratops-style). Faces -Y.

One design, three growth stages:
    blender -b --python thornhorn.py -- <out_dir> [Child|Teen|Adult]

All stages share bone names and rig layout, so the same animation code drives each one;
IK reads each stage's own leg lengths so feet still plant correctly.
Adult is exported as "Thornhorn" (also used for nest mothers), the others as
"Thornhorn_Child" / "Thornhorn_Teen".
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Monster, envelope, smooth01

STAGES = {
    # S: overall size vs adult. legL/legT: leg length/thickness. bL/bW/bH: body length/width/height.
    # head/eye: relative head and eye size. horn/frill/spikes: how grown those are (0 = none).
    # energy: how bouncy/expressive the animations are.
    'Adult': dict(name='Thornhorn', S=1.0, legL=1.0, legT=1.0, bL=1.0, bW=1.0, bH=1.0, head=1.0, eye=1.0,
                  horn=1.0, frill=1.0, spikes=1.0, tail=1.0, neck=1.0, beak=1.0, taper=(0.8, 0.85),
                  energy=1.0, body='#4a8a3a'),
    'Teen': dict(name='Thornhorn_Teen', S=0.78, legL=1.12, legT=0.85, bL=0.95, bW=0.82, bH=0.85, head=1.0, eye=1.15,
                 horn=0.6, frill=0.55, spikes=0.55, tail=1.05, neck=1.1, beak=0.9, taper=(0.82, 0.86),
                 energy=1.25, body='#53964a'),
    'Child': dict(name='Thornhorn_Child', S=0.55, legL=0.86, legT=1.05, bL=0.72, bW=0.95, bH=0.95, head=1.45, eye=1.7,
                  horn=0.3, frill=0.0, spikes=0.35, tail=0.6, neck=0.6, beak=0.7, taper=(0.92, 0.92),
                  energy=1.6, body='#5ea456'),
}

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
STAGE = args[1] if len(args) > 1 else 'Adult'
P = STAGES[STAGE]
S = P['S']


class Scaled(Monster):
    """Monster whose definition calls are in adult-design units; everything is multiplied by S."""
    def bone(self, name, head, tail, parent=None):
        super().bone(name, sv(head), sv(tail), parent)

    def box(self, bone, color, center, size, rot=(0, 0, 0), bevel=0.12, segs=1, taper=None, smooth=False):
        if taper and 'offset' in taper:
            taper = dict(taper, offset=tuple(o * S for o in taper['offset']))
        super().box(bone, color, sv(center), sv(size), rot, bevel * S, segs, taper, smooth)

    def spike(self, bone, color, base, direction, length, width, depth=None, twist=0.0, snap=True):
        super().spike(bone, color, sv(base), direction, length * S, width * S,
                      None if depth is None else depth * S, twist, snap)

    def eye(self, bone, center, normal, size=0.3, up=(0, 0, 1), iris='iris'):
        super().eye(bone, sv(center), normal, size * S, up, iris)

    def loft(self, bone, color, points, radii, **kw):
        super().loft(bone, color, [sv(p) for p in points], [(a * S, b * S) for a, b in radii], **kw)


def sv(v):
    return tuple(c * S for c in v)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


m = Scaled(P['name'])
bL, bW, bH, h, t, L, T = P['bL'], P['bW'], P['bH'], P['head'], P['tail'], P['legL'], P['legT']

# palette (children are a little brighter): deep moss green hide, dark outlined armour plates, an
# orange crown frill, ivory horns and glowing lime eyes
m.color('body', P['body'])
m.color('belly', '#d9c48e')
m.color('plate', '#4b7a34', edges=True)
m.color('moss', '#86c43a')
m.color('leaf', '#5fae2e', dots=False, edges=True)
m.color('leaf2', '#9be04a', dots=False, edges=True)
m.color('frill', '#e0602a', edges=True)
m.color('frill2', '#ffb43a', edges=True)
m.color('horn', '#f3ead6', dots=False)
m.color('tooth', '#fbf7ee', dots=False)
m.color('beak', '#cdb58a', edges=True)
m.color('dark', '#141710', dots=False)
m.color('foot', '#3a2a1e')
m.color('mouth', '#5a1e22', dots=False)
m.color('tongue', '#d6405c')
m.color('eye_dark', '#0d0f0a', dots=False)
m.color('iris', '#c8ff3a', dots=False)
m.color('eye_glint', '#ffffff', dots=False)

# ---------------- anchors (adult-design units) ----------------
hipZ = 2.05 * L
bodyZ = hipZ + 0.4 * bH
ankZ = 0.42 * T
kneeZ = ankZ + (hipZ - ankZ) * (0.78 / 1.63)
neckStart = (0, -1.4 * bL, bodyZ + 0.1 * bH)
hp = add(neckStart, (0, -0.9 * P['neck'], 0.3 * P['neck']))   # head pivot
hipsHead = (0, 1.3 * bL, bodyZ - 0.1 * bH)
yF, yB = -0.9 * bL, 1.4 * bL


def H(dx, dy, dz):
    """point relative to the head pivot, scaled by head size"""
    return add(hp, (dx * h, dy * h, dz * h))


def tail_pt(ya, za):
    """adult tail point -> this stage (tail starts at the hips)"""
    return (0, 1.3 * bL + (ya - 1.3) * t, hipsHead[2] + (za - 2.35) * t)


def body_pt(ya, za):
    return (0, ya * bL, bodyZ + (za - 2.45) * bH)


# ---------------- rig ----------------
SIDES = (('L', 1), ('R', -1))   # L = +X (monster's left when facing -Y)
m.bone('MonsterRoot', (0, 0.3 * bL, 0), (0, 0.3 * bL, 1.0))
m.bone('Hips', hipsHead, (0, 0, bodyZ), 'MonsterRoot')
m.bone('Chest', (0, 0, bodyZ), neckStart, 'Hips')
m.bone('Neck', neckStart, hp, 'Chest')
m.bone('Head', hp, H(0, -2.1, -0.05), 'Neck')
m.bone('Jaw', H(0, -0.3, -0.7), H(0, -1.8, -0.8), 'Head')
t1 = add(hipsHead, (0, 1.4 * t, -0.2 * t))
t2 = add(t1, (0, 1.3 * t, -0.3 * t))
t3 = add(t2, (0, 1.3 * t, -0.3 * t))
m.bone('Tail1', hipsHead, t1, 'Hips')
m.bone('Tail2', t1, t2, 'Tail1')
m.bone('Tail3', t2, t3, 'Tail2')
for side, s in SIDES:
    x = 1.15 * bW * s
    m.bone(f'UpperF{side}', (x, yF, hipZ), (x, yF + 0.2 * L, kneeZ), 'Chest')
    m.bone(f'LowerF{side}', (x, yF + 0.2 * L, kneeZ), (x, yF - 0.05, ankZ), f'UpperF{side}')
    m.bone(f'FootF{side}', (x, yF - 0.05, ankZ), (x, yF - 0.7 * T, 0.15 * T), f'LowerF{side}')
    x = 1.2 * bW * s
    m.bone(f'UpperB{side}', (x, yB, hipZ), (x, yB - 0.4 * L, kneeZ), 'Hips')
    m.bone(f'LowerB{side}', (x, yB - 0.4 * L, kneeZ), (x, yB - 0.05, ankZ), f'UpperB{side}')
    m.bone(f'FootB{side}', (x, yB - 0.05, ankZ), (x, yB - 0.65 * T, 0.15 * T), f'LowerB{side}')

# ---------------- body: chunky stepped blocks (hard edges) ----------------
SPINE = ['Tail3', 'Tail2', 'Tail1', 'Hips', 'Chest', 'Neck']


def spine_bone(y):
    return ('Chest' if y < 0.0 else 'Hips' if y < 1.3 * bL else
            'Tail1' if y < 1.3 * bL + 1.4 * t else 'Tail2')


m.box('Chest', 'body', body_pt(-0.8, 2.6), (3.0 * bW, 1.9 * bL, 2.4 * bH), bevel=0.2, segs=1,
      taper=dict(axis='z', end=1, scale=(0.82, 0.9)))
m.box(['Chest', 'Hips'], 'body', body_pt(0.35, 2.5), (2.8 * bW, 1.7 * bL, 2.2 * bH), bevel=0.2, segs=1,
      taper=dict(axis='z', end=1, scale=(0.84, 0.9)))
m.box('Hips', 'body', body_pt(1.3, 2.4), (2.5 * bW, 1.4 * bL, 1.95 * bH), bevel=0.2, segs=1,
      taper=dict(axis='y', end=1, scale=(0.82, 0.85)))
m.box(['Hips', 'Chest'], 'belly', body_pt(0.2, 1.3), (2.3 * bW, 3.4 * bL, 0.45 * bH), bevel=0.12, segs=1)
m.box(['Chest', 'Neck'], 'body', tuple((a + b) / 2 for a, b in zip(neckStart, hp)), (2.1 * max(bW, 0.8 * h), 1.4, 1.9 * max(bH, 0.8 * h)),
      bevel=0.2, segs=1)
# tail: hexagonal, tapering, with plates down the top
pts = [body_pt(1.8, 2.35)] + [tail_pt(ya, za) for ya, za in ((2.3, 2.3), (3.3, 2.05), (4.5, 1.75), (5.6, 1.5))]
m.loft(['Hips', 'Tail1', 'Tail2', 'Tail3'], 'body', pts,
       [(1.0 * bW, 0.9 * bH), (0.95 * bW, 0.85 * bH), (0.62, 0.55), (0.36, 0.32), (0.12, 0.1)], sides=6, steps=1, smooth=False)

# armoured back: three rows of overlapping outlined plates, a bone spike on each ridge plate
sp = P['spikes']
for ya in (-1.25, -0.6, 0.05, 0.7, 1.3):
    for x, tilt in ((-0.75, 28), (0.0, 0), (0.75, -28)):
        p = body_pt(ya, 4.0 - abs(x) * 0.42)
        bone = spine_bone(p[1])
        big = 1.0 if x == 0 else 0.82
        m.box(bone, 'plate', (x * bW, p[1], p[2]), (0.95 * big, 0.78 * big, 0.2), rot=(14, tilt, 0), bevel=0.05)
        if x == 0 and sp > 0:
            m.spike(bone, 'horn', (0, p[1] + 0.05, p[2] + 0.1), (0, 0.3, 1), 0.75 * sp, 0.34 * sp, 0.34 * sp)
for ya, za in ((2.4, 3.0), (3.2, 2.55), (4.0, 2.15), (4.8, 1.85)):
    if sp < 0.5:
        break
    p = tail_pt(ya, za)
    m.box(spine_bone(p[1]), 'plate', p, (0.7 * (1.4 - ya / 6), 0.6, 0.16), rot=(14, 0, 0), bevel=0.04)
    m.spike(spine_bone(p[1]), 'horn', (0, p[1], p[2] + 0.08), (0, 0.4, 1), 0.45 * sp, 0.24 * sp, 0.24 * sp)
# moss and leaf sprigs growing between the plates
for ya, x in ((-0.95, 0.45), (0.4, -0.5), (1.0, 0.5), (-0.2, 0.0)):
    p = body_pt(ya, 4.02)
    bone = spine_bone(p[1])
    m.box(bone, 'moss', (x * bW, p[1], p[2] - 0.05), (0.55, 0.5, 0.14), rot=(0, 0, 25), bevel=0.04)
    for k in range(3):
        a = k * 2.1 + x
        m.box(bone, 'leaf' if k % 2 else 'leaf2', (x * bW + 0.12 * math.cos(a), p[1] + 0.12 * math.sin(a), p[2] + 0.22),
              (0.1, 0.32, 0.45), rot=(25, 0, math.degrees(a)), bevel=0.03)
# flank plates
for side, s in SIDES:
    for ya in (-0.8, 0.4):
        p = body_pt(ya, 2.7)
        m.box(spine_bone(p[1]), 'plate', (1.47 * bW * s, p[1], p[2] + 0.2), (0.18, 0.95, 0.6), rot=(25, 18 * s, 0), bevel=0.05)

# ---------------- head: huge and chiselled ----------------
m.box('Head', 'body', H(0, -0.95, 0.15), (2.45 * h, 2.4 * h, 1.95 * h), bevel=0.22 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=P['taper']))
m.box('Head', 'plate', H(0, -1.6, 0.92), (2.35 * h, 0.7 * h, 0.42 * h), rot=(-18, 0, 0), bevel=0.06 * h)   # angry brow
for side, s in SIDES:
    m.box('Head', 'plate', H(1.18 * s, -0.75, -0.15), (0.24 * h, 1.3 * h, 0.95 * h), rot=(0, 12 * s, 0), bevel=0.05 * h)   # cheek plate
bk = P['beak']
m.box('Head', 'beak', H(0, -2.2 + 0.35 * (1 - bk), -0.05), (1.35 * h * bk, 0.9 * h * bk, 1.15 * h * bk), bevel=0.08 * h,
      segs=1, taper=dict(axis='y', end=-1, scale=(0.55, 0.6), offset=(0, -0.2 * h * bk)))
for side, s in SIDES:
    m.box('Head', 'dark', H(0.32 * s, -2.05, 0.28), (0.18 * h, 0.12 * h, 0.14 * h), bevel=0.02)   # nostrils
m.box('Head', 'mouth', H(0, -1.1, -0.62), (1.7 * h, 1.9 * h, 0.22 * h), bevel=0.0)
for k in range(5):   # upper teeth: chunky squares along the lip
    for side, s in SIDES:
        m.box('Head', 'tooth', H(0.78 * s, -0.55 - k * 0.32, -0.75), (0.18 * h, 0.2 * h, 0.26 * h), bevel=0.02)
# glowing eyes in dark sockets under the brow
for side, s in SIDES:
    m.box('Head', 'dark', H(1.08 * s, -1.25, 0.42), (0.2 * h, 0.62 * h, 0.52 * h), bevel=0.04 * h)
    m.eye('Head', H(1.2 * s, -1.27, 0.42), (1 * s, -0.4, 0.05), 0.5 * h * P['eye'])
# crown frill: a fan of outlined plates with bone tips
fr = P['frill']
if fr > 0:
    fc = H(0, 0.05, 0.85 * (0.5 + 0.5 * fr))
    for i, ang in enumerate((-80, -54, -27, 0, 27, 54, 80)):
        a = math.radians(ang)
        r = 1.55 * h * fr
        c = add(fc, (math.sin(a) * r, 0.25 * h, math.cos(a) * r))
        m.box('Head', 'frill', c, (0.95 * h * fr, 0.22 * h, 1.3 * h * fr), rot=(-22, -ang, 0), bevel=0.04)
        m.box('Head', 'frill2', add(c, (0, -0.14 * h, -0.1 * h * fr)), (0.58 * h * fr, 0.08 * h, 0.85 * h * fr), rot=(-22, -ang, 0), bevel=0.02)
        tip = add(fc, (math.sin(a) * r * 1.48, 0.5 * h, math.cos(a) * r * 1.48))
        m.spike('Head', 'horn', tip, (math.sin(a), 0.25, math.cos(a)), 0.5 * h * fr, 0.24 * h * fr, 0.2 * h * fr)
# horns: two big curving brow horns (three segments) and a stubby nose horn
hn = P['horn']
for side, s in SIDES:
    p0 = H(0.62 * s, -1.25, 0.95)
    k = h * hn
    w = h * (0.6 + 0.4 * hn)
    pts = [p0, add(p0, (0.2 * s * k, -0.15 * k, 0.75 * k)), add(p0, (0.32 * s * k, -0.75 * k, 1.25 * k)), add(p0, (0.36 * s * k, -1.55 * k, 1.35 * k))]
    m.loft('Head', 'horn', pts, [(0.3 * w, 0.3 * w), (0.24 * w, 0.24 * w), (0.15 * w, 0.15 * w), (0.02, 0.02)], sides=6, steps=3, smooth=False)
m.spike('Head', 'horn', H(0, -2.0, 0.55), (0, -0.5, 1), 0.7 * h * hn, 0.42 * h * (0.6 + 0.4 * hn))

# ---------------- jaw ----------------
m.box('Jaw', 'body', H(0, -1.15, -1.0), (1.95 * h, 2.15 * h, 0.55 * h), bevel=0.1 * h, segs=1,
      taper=dict(axis='y', end=-1, scale=(0.72, 0.8)))
m.box('Jaw', 'belly', H(0, -1.15, -1.22), (1.6 * h, 1.9 * h, 0.2 * h), bevel=0.05 * h)
m.box('Jaw', 'mouth', H(0, -1.05, -0.86), (1.55 * h, 1.8 * h, 0.2 * h), bevel=0.0)
m.box('Jaw', 'tongue', H(0, -1.2, -0.8), (0.7 * h, 1.1 * h, 0.12 * h), bevel=0.03 * h)
for k in range(4):
    for side, s in SIDES:
        m.box('Jaw', 'tooth', H(0.68 * s, -0.7 - k * 0.34, -0.66), (0.17 * h, 0.18 * h, 0.24 * h), bevel=0.02)

# ---------------- legs: thick pillars, knee plates, clawed feet ----------------
for side, s in SIDES:
    for end, x, yy, lean in (('F', 1.2 * bW * s, yF, 0.2), ('B', 1.25 * bW * s, yB, -0.4)):
        m.loft([f'Upper{end}{side}', f'Lower{end}{side}', f'Foot{end}{side}'], 'body',
               [(x, yy - 0.05, hipZ + 0.15), (x, yy + lean * L, kneeZ), (x, yy - 0.05, ankZ + 0.08)],
               [(0.72 * T, 0.75 * T), (0.55 * T, 0.55 * T), (0.5 * T, 0.5 * T)],
               sides=6, steps=1, smooth=False, up=(0, -1, 0))
        m.box(f'Upper{end}{side}', 'plate', (x * 1.06, yy + lean * L - 0.32 * T, kneeZ + 0.1), (0.75 * T, 0.32 * T, 0.7 * T),
              rot=(10, 0, 0), bevel=0.04)
        m.box(f'Foot{end}{side}', 'foot', (x, yy - 0.3 * T, 0.26 * T), (1.15 * T, 1.3 * T, 0.52 * T), bevel=0.08 * T, segs=1)
        for dx in (-0.36, 0.0, 0.36):
            m.spike(f'Foot{end}{side}', 'horn', (x + dx * T, yy - 0.92 * T, 0.2 * T), (0, -1, -0.25), 0.32 * T, 0.2 * T)

# ---------------- animation ----------------
# translations below are in adult-design units and get multiplied by S; IK uses the scaled rig.
TAU = 2 * math.pi
E = P['energy']
LEGS = {f'{e}{side}': (f'Upper{e}{side}', f'Lower{e}{side}', f'Foot{e}{side}')
        for e in 'FB' for side, _ in SIDES}
FRONT_LEVER = abs(hipsHead[1] - yF) * S   # Hips pivot to the front shoulders
WALK = dict(stride=1.1 * L, lift=0.4 * L, duty=0.64, frames=32)
RUN = dict(stride=1.8 * L, lift=0.6 * L, duty=0.4, frames=20)


def step(u, stride, lift, duty):
    """Foot path relative to its rest spot: stance slides back, swing arcs forward."""
    u %= 1.0
    if u < duty:
        s = u / duty
        roll = smooth01((s - 0.7) / 0.3)   # heel peels up before push-off
        return -stride / 2 + stride * s, 0.12 * S * roll, 22 * roll
    s = (u - duty) / (1 - duty)
    dz = lift * math.sin(math.pi * s) ** 0.8 + 0.12 * S * (1 - smooth01(s / 0.25))
    tilt = 22 * (1 - smooth01(s / 0.6)) - 8 * math.sin(math.pi * smooth01((s - 0.5) / 0.5))
    return stride / 2 - stride * smooth01(s), dz, tilt


def legs(pose, t, phases, gait, shift_front=(0, 0), shift_back=(0, 0)):
    for leg, ph in phases.items():
        dy, dz, tilt = step(t + ph, gait['stride'] * S, gait['lift'] * S, gait['duty'])
        ay, az = m.rest_ankle(LEGS[leg][1])
        shift = shift_front if leg[0] == 'F' else shift_back
        m.ik_leg(pose, *LEGS[leg], (ay + dy, az + dz), shift, tilt)


def planted(pose, shift_front=(0, 0), shift_back=(0, 0), only=None):
    for leg, chain in LEGS.items():
        if only and leg[0] not in only:
            continue
        shift = shift_front if leg[0] == 'F' else shift_back
        m.ik_leg(pose, *chain, m.rest_ankle(chain[1]), shift)


def tail(pose, p, amp, pitch=(0, 0, 0)):
    for i, b in enumerate(('Tail1', 'Tail2', 'Tail3')):
        pose[b] = ((pitch[i], 0, amp * E * (1 + 0.4 * i) * math.sin(p - 0.6 * (i + 1))), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    bob = 0.035 * S * E * math.sin(p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, bob)),
        'Chest': ((1.0 * E * math.sin(p), 0, 0), (0, 0, 0)),
        'Neck': ((2 * E * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
        'Head': ((2 * E * math.sin(p + 1), 0, 6 * E * math.sin(p)), (0, 0, 0)),
        'Jaw': ((2 + 2 * math.sin(2 * p), 0, 0), (0, 0, 0)),
    }
    tail(pose, p, 5)
    planted(pose, (0, bob), (0, bob))
    return pose


def walk(t_):
    p = TAU * t_
    lean = math.cos(TAU * (t_ - 0.435))         # weight over left legs ~0.43, right ~0.93
    bob = -0.06 * S * E * math.cos(2 * TAU * (t_ - 0.3))   # dip after each front footfall
    flex = math.sin(TAU * (t_ - 0.1))           # spine flexes side to side
    pose = {
        'Hips': ((0, -3 * lean, 3 * flex), (0.07 * S * lean, 0, bob)),
        'Chest': ((0, 2 * lean, -5 * flex), (0, 0, 0)),
        'Neck': ((3 * E * math.cos(2 * TAU * (t_ - 0.36)), 0, 3 * flex), (0, 0, 0)),
        'Head': ((2.5 * E * math.cos(2 * TAU * (t_ - 0.42)), 0, 2 * flex), (0, 0, 0)),
        'Jaw': ((3, 0, 0), (0, 0, 0)),
        'Tail1': ((2 * math.cos(2 * p), 0, -7 * E * flex), (0, 0, 0)),
        'Tail2': ((0, 0, -10 * E * math.sin(TAU * (t_ - 0.22))), (0, 0, 0)),
        'Tail3': ((0, 0, -13 * E * math.sin(TAU * (t_ - 0.34))), (0, 0, 0)),
    }
    legs(pose, t_, {'BL': 0.0, 'FL': 0.25, 'BR': 0.5, 'FR': 0.75}, WALK, (0, bob), (0, bob))
    return pose


def run(t_):
    p = TAU * t_
    bob = (0.16 * math.sin(p) + 0.06) * S * E
    pitch = 4 * E * math.sin(p)
    pose = {
        'Hips': ((pitch, 0, 0), (0, 0, bob)),
        'Chest': ((-3 * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
        'Neck': ((-6, 0, 0), (0, 0, 0)),
        'Head': ((-4 + 4 * E * math.sin(p + 1), 0, 0), (0, 0, 0)),
        'Jaw': ((12, 0, 0), (0, 0, 0)),
    }
    tail(pose, p, 3, pitch=(10 + 5 * math.sin(p), 5 * math.sin(p - 1), 4 * math.sin(p - 1.6)))
    front_dz = bob - FRONT_LEVER * math.sin(math.radians(pitch))
    legs(pose, t_, {'BL': 0.0, 'BR': 0.1, 'FL': 0.5, 'FR': 0.6}, RUN, (0, front_dz), (0, bob))
    return pose


def sleep(t_):
    p = TAU * t_
    # lower the body until the belly rests on the ground
    drop = -(bodyZ - 1.15 * bH - 0.35) * S + 0.04 * S * math.sin(p)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, drop)),
        'Chest': ((1.0 * math.sin(p), 0, 0), (0, 0, 0)),
        'Neck': ((10, 0, 0), (0, 0, 0)),
        'Head': ((10 + 1.5 * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
        'Tail1': ((-6, 0, 18), (0, 0, 0)),
        'Tail2': ((-4, 0, 28), (0, 0, 0)),
        'Tail3': ((0, 0, 35), (0, 0, 0)),
    }
    for leg, chain in LEGS.items():
        ay, az = m.rest_ankle(chain[1])
        target = (ay - 0.55 * S * L, 0.32 * S * T) if leg[0] == 'F' else (ay + 0.15 * S * L, 0.3 * S * T)
        m.ik_leg(pose, *chain, target, (0, drop))
    return pose


def roar(t_):
    e = envelope(t_, 0.22, 0.75)
    shake = math.sin(TAU * 7 * t_) * envelope(t_, 0.3, 0.7, 0.8)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0.25 * S * e, 0)),
        'Hips': ((-4 * e, 0, 0), (0, 0, 0)),
        'Chest': ((-10 * e, 0, 0), (0, 0, 0)),
        'Neck': ((-14 * e, 0, 0), (0, 0, 0)),
        'Head': ((-16 * e, 0, 9 * shake), (0, 0, 0)),
        'Jaw': ((40 * e, 0, 0), (0, 0, 0)),
        'Tail1': ((10 * e, 0, 0), (0, 0, 0)),
        'Tail2': ((8 * e, 0, 6 * shake), (0, 0, 0)),
        'Tail3': ((6 * e, 0, 8 * shake), (0, 0, 0)),
    }
    for side, _ in SIDES:
        pose[f'UpperF{side}'] = ((-14 * e, 0, 0), (0, 0, 0))
        pose[f'LowerF{side}'] = ((22 * e, 0, 0), (0, 0, 0))
        pose[f'FootF{side}'] = ((-8 * e, 0, 0), (0, 0, 0))
    planted(pose, shift_back=(0.25 * S * e, 0), only='B')
    return pose


def attack(t_):
    w = envelope(t_, 0.3, 0.3, 0.45)
    s = smooth01((t_ - 0.33) / 0.15) if t_ < 0.6 else 1 - smooth01((t_ - 0.6) / 0.4)
    dy = (0.4 * w - 0.9 * s) * S
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, dy, 0)),
        'Chest': ((-5 * w + 5 * s, 0, 0), (0, 0, 0)),
        'Neck': ((-8 * w + 12 * s, 0, 0), (0, 0, 0)),
        'Head': ((-14 * w + 18 * s, 0, 0), (0, 0, 0)),
        'Jaw': ((12 * w, 0, 0), (0, 0, 0)),
        'Tail1': ((10 * w, 0, 0), (0, 0, 0)),
    }
    planted(pose, (dy, 0), (dy, 0))
    return pose


def happy(t_):
    """Evolve / celebrate: a little hop with a head toss."""
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    settle = envelope(t_, 0.1, 0.55, 1.0)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.5 * S * E * hop)),
        'Chest': ((-8 * settle, 0, 0), (0, 0, 0)),
        'Neck': ((-12 * settle, 0, 0), (0, 0, 0)),
        'Head': ((-10 * settle, 0, 10 * math.sin(TAU * 2 * t_) * settle), (0, 0, 0)),
        'Jaw': ((25 * settle, 0, 0), (0, 0, 0)),
    }
    tail(pose, TAU * 2 * t_, 10 * settle)
    for leg, chain in LEGS.items():
        ay, az = m.rest_ankle(chain[1])
        m.ik_leg(pose, *chain, (ay, az + 0.15 * S * hop), (0, 0.5 * S * E * hop))
    return pose


m.anim('Idle', 72, True, idle, key_step=4)
m.anim('Walk', WALK['frames'], True, walk, key_step=2)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 54, False, roar, key_step=3)
m.anim('Attack', 30, False, attack, key_step=2)
m.anim('Happy', 36, False, happy, key_step=2)

# ground speed each locomotion clip covers at playback speed 1 (Blender units / second)
m.refs = {g: gait['stride'] * S / (gait['duty'] * gait['frames'] / 30) for g, gait in (('Walk', WALK), ('Run', RUN))}
m.build(OUT)
