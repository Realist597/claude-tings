"""Gourdling - Uncommon Haunted monster (Haunted Pumpkin featured egg): a feral living
jack-o'-lantern. Its whole body is the pumpkin, ridged with dark outlined ribs and split by glowing
fissures across the back; a furious carved face blazes from inside, and the lower jaw is a cut chunk
of pumpkin that cracks open on the fire within. A curling thorned stem rises from the crown inside
a collar of jagged dark leaves. Arms and legs are twisted thorny vines ending in clawed roots, and
it drags a rusty sickle with a glowing edge. Faces -Y.
    blender -b --python gourdling.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Face (inner glow), Blade."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, ik, envelope, smooth01, add, TAU

m, st, OUT = setup('Gourdling', {
    'pumpkin': '#e8641c', 'rib': ('#3a160c', False, True), 'dark': ('#140604', False), 'glow': ('#ffd23a', False),
    'glow2': ('#ff7a12', False), 'stem': ('#2a1a10', True, True), 'thorn': ('#0e0809', False),
    'leaf': ('#24401c', True, True), 'vine': ('#2f4a22', True, True), 'root': ('#3a2414', True, True),
    'claw': ('#e8dfcc', False), 'wood': ('#4a3020', True, True), 'blade': ('#6a6470', False, True), 'rust': ('#8a3a1a', False),
    'bone': ('#e6dcc4', False, True), 'rope': ('#5a4428', True, True), 'glow3': ('#fff0a0', False),
    'eye_dark': ('#140604', False), 'iris': ('#ffd23a', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.25), 'Teen': dict(head=1.1)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
PC = (0, 0, 2.15)              # pumpkin centre
PR = (1.08 * h, 0.98 * h, 0.92 * h)


def P(x, y, z):
    """a point on/around the pumpkin in units of its radii"""
    return (PC[0] + x * PR[0], PC[1] + y * PR[1], PC[2] + z * PR[2])


def surf(az, el, out=0.0):
    """point on the pumpkin's surface: azimuth az (0 = front, -Y), elevation el (radians)"""
    x, y, z = math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)
    return (PC[0] + x * (PR[0] + out), PC[1] + y * (PR[1] + out), PC[2] + z * (PR[2] + out))


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0.1, 1.05), (0, 0.05, 1.45), 'MonsterRoot')
m.bone('Chest', (0, 0.05, 1.45), P(0, 0, 0.95), 'Hips')
m.bone('Jaw', P(0, -0.55, -0.35), P(0, -1.05, -0.45), 'Chest')
m.bone('Stem', P(0, 0.05, 0.92), P(0.1, 0.25, 1.6), 'Chest')
for side, s in SIDES:
    sh = P(0.98 * s, 0.05, 0.05)
    el = add(sh, (0.55 * s, -0.15, -0.5))
    wr = add(el, (0.15 * s, -0.45, -0.35))
    m.bone(f'Arm{side}', sh, el, 'Chest')
    m.bone(f'Fore{side}', el, wr, f'Arm{side}')
    m.bone(f'Thigh{side}', (0.42 * s, 0.1, 1.15), (0.5 * s, -0.25, 0.6), 'Hips')
    m.bone(f'Shin{side}', (0.5 * s, -0.25, 0.6), (0.5 * s, 0.15, 0.22), f'Thigh{side}')
    m.bone(f'Foot{side}', (0.5 * s, 0.15, 0.22), (0.5 * s, -0.35, 0.04), f'Shin{side}')

# ---------------- the pumpkin ----------------
m.blob('Chest', 'pumpkin', PC, PR, u=12, v=8)
# dark outlined ribs running pole to pole between the segments (the face stays clear)
for i in range(10):
    az = (i + 0.5) * TAU / 10
    if abs(((az + math.pi) % TAU) - math.pi) < 0.55:
        continue
    pts = [surf(az, el, 0.02) for el in (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25)]
    m.loft('Chest', 'rib', pts, [(0.07 * h, 0.1 * h)] * len(pts), sides=5, steps=2, smooth=False)
# glowing fissures across the back
for az0, n in ((2.6, 6), (3.5, 7), (4.1, 5)):
    pts = [surf(az0 + 0.12 * ((k % 2) * 2 - 1) + 0.05 * k, 0.9 - 0.3 * k, 0.03) for k in range(n)]
    m.loft('Chest', 'glow2', pts, [(0.05 * h, 0.05 * h)] * n, sides=4, steps=1, smooth=False)

# the carved face: dark rims, glowing insides
def tri(bone, color, center, w, hgt, slant, depth):
    """a carved triangle facing -Y: flat bottom, point on top, tipped by `slant` degrees"""
    m.box(bone, color, center, (w, depth, hgt), rot=(0, slant, 0), bevel=0.0,
          taper=dict(axis='z', end=1, scale=(0.05, 1)))
for side, s in SIDES:
    big = 1.3 if s > 0 else 0.95                                           # lopsided: one eye carved huge
    c = surf(0.38 * s, 0.22 + 0.05 * (big - 1), -0.02)
    tri('Chest', 'dark', c, 0.42 * h * big, 0.4 * h * big, 22 * s, 0.14 * h)   # furious: tipped towards the nose
    tri('Chest', 'glow', add(c, (0, -0.03, 0)), 0.3 * h * big, 0.3 * h * big, 22 * s, 0.12 * h)
    tri('Chest', 'glow3', add(c, (0, -0.05, -0.04 * h)), 0.12 * h * big, 0.12 * h * big, 22 * s, 0.1 * h)   # white-hot core
    m.box('Chest', 'rib', add(surf(0.36 * s, 0.45, 0.02), (0, 0, 0)), (0.4 * h, 0.1 * h, 0.09 * h), rot=(0, -26 * s, 0), bevel=0.02 * h)  # brow ridge
tri('Chest', 'dark', surf(0, -0.02, -0.02), 0.18 * h, 0.18 * h, 0, 0.12 * h)
tri('Chest', 'glow2', add(surf(0, -0.02, -0.02), (0, -0.03, 0)), 0.11 * h, 0.11 * h, 0, 0.1 * h)
# upper teeth: a jagged row cut along the top of the mouth
for k in range(7):
    f = (k - 3) / 3
    c = surf(0.55 * f, -0.3 + 0.08 * f * f, -0.01)
    m.box('Chest', 'dark', add(c, (0, 0, 0.02)), (0.2 * h, 0.12 * h, 0.13 * h), bevel=0.0)
    if k % 2 == 0:
        tri('Chest', 'pumpkin', add(c, (0, -0.04, -0.06)), 0.14 * h, 0.16 * h, 180, 0.08 * h)   # fang pointing down
# fire in the mouth, and the jaw: a cut chunk of pumpkin with its own teeth
m.blob('Chest', 'glow', P(0, -0.62, -0.42), (0.55 * h, 0.25 * h, 0.16 * h), u=8, v=5)
m.socket('Face', 'Chest', P(0, -0.8, -0.1))
jaw_pts = [surf(az, -0.62, 0.0) for az in (-0.75, -0.4, 0.0, 0.4, 0.75)]
m.loft('Jaw', 'pumpkin', jaw_pts, [(0.18 * h, 0.14 * h)] * 5, sides=6, steps=2, smooth=False)
for k in range(4):
    f = (k - 1.5) / 1.5
    tri('Jaw', 'pumpkin', add(surf(0.42 * f, -0.48, 0.0), (0, -0.05, 0.0)), 0.14 * h, 0.17 * h, 0, 0.08 * h)  # lower fangs

# crown: a collar of jagged dark leaves round a curling, thorned stem
for i in range(9):
    az = i * TAU / 9
    base = surf(az, 1.05, -0.02)
    d = (math.sin(az) * 1.0, -math.cos(az) * 1.0, 0.55)
    m.spike('Chest', 'leaf', base, d, (0.62 + 0.15 * (i % 2)) * h, 0.36 * h, 0.06 * h)
stem = [P(0, 0.05, 0.85), P(0.05, 0.1, 1.25), P(0.0, 0.35, 1.55), P(-0.15, 0.55, 1.6), P(-0.25, 0.65, 1.42)]
m.loft('Stem', 'stem', stem, [(0.2 * h, 0.2 * h), (0.17 * h, 0.17 * h), (0.13 * h, 0.13 * h), (0.09 * h, 0.09 * h), (0.04 * h, 0.04 * h)], sides=5, steps=2, smooth=False)
for p, d in ((stem[1], (1, 0, 0.3)), (stem[1], (-1, 0.2, 0.2)), (stem[2], (0.5, -0.8, 0.4)), (stem[3], (0, 1, 0.5))):
    m.spike('Stem', 'thorn', p, d, 0.26 * h, 0.08 * h, snap=False)

# a glowing crack splitting down from the small eye
crk = [surf(-0.3, 0.55, 0.02), surf(-0.42, 0.4, 0.02), surf(-0.36, 0.1, 0.02), surf(-0.5, -0.05, 0.02)]
m.loft('Chest', 'glow2', crk, [(0.035 * h, 0.035 * h)] * 4, sides=4, steps=1, smooth=False)
# glowing seeds spilling from the mouth and stuck in the fissures
for k, (az, el) in enumerate(((-0.3, -0.5), (0.1, -0.55), (0.35, -0.48), (-0.05, -0.62), (2.7, 0.5), (3.45, 0.2), (4.05, 0.6))):
    m.blob('Chest' if k > 3 else 'Jaw', 'glow3', surf(az, el, 0.05), (0.06 * h, 0.04 * h, 0.09 * h), u=5, v=3)
for k in range(3):   # a drool of seeds hanging off the jaw
    m.blob('Jaw', 'glow3', add(surf(0.2, -0.7, 0.0), (0, -0.02, -0.1 * k * h)), (0.045 * h, 0.035 * h, 0.06 * h), u=5, v=3)

# a ragged cape of big dark leaves hanging from the crown down its back
for i in range(7):
    az = math.pi + (i - 3) * 0.32
    top = surf(az, 0.95, 0.04)
    mid = surf(az, 0.25 + 0.06 * (i % 2), 0.16)
    bot = surf(az + 0.05 * (i - 3), -0.45 - 0.1 * (i % 2), 0.22)
    m.loft('Chest', 'leaf', [top, mid, bot], [(0.24 * h, 0.04 * h), (0.3 * h, 0.04 * h), (0.04 * h, 0.03 * h)], sides=4, steps=2, smooth=False)
    m.loft('Chest', 'vine', [top, mid, bot], [(0.03 * h, 0.06 * h)] * 3, sides=4, steps=2, smooth=False)   # leaf vein

# curling vine tendrils sprouting off the shoulders and crown
for side, s in SIDES:
    for j, (az, el, turn) in enumerate(((1.35, 0.75, 1), (2.2, 0.85, -1))):
        base = surf(az * s, el, 0.0)
        pts, r = [base], 0.38 * h
        for k in range(1, 7):
            a = k * 0.9 * turn
            pts.append(add(base, (s * (0.125 * k * h + math.cos(a) * r * 0.3), math.sin(a) * r * 0.4, 0.18 * k * h - 0.025 * k * k * h)))
            r *= 0.8
        m.loft('Chest', 'vine', pts, [(max(0.02, 0.07 - 0.009 * k) * h,) * 2 for k in range(7)], sides=4, steps=2, smooth=False)
        m.spike('Chest', 'thorn', pts[2], (s, 0, 0.4), 0.16 * h, 0.05 * h, snap=False)
        m.spike('Chest', 'leaf', pts[4], (s * 0.5, 0.6, 0.5), 0.3 * h, 0.16 * h, 0.03 * h)

# a rope belt of little bone skulls round its base
belt = [surf(i * TAU / 14, -0.95, 0.03) for i in range(15)]
m.loft('Hips', 'rope', belt, [(0.06 * h, 0.06 * h)] * 15, sides=4, steps=1, smooth=False, cap_round=0.0)
for i in (1, 3, 5, 9, 11, 13):
    az = i * TAU / 14
    c = add(surf(az, -1.02, 0.12), (0, 0, -0.08 * h))
    out = (math.sin(az), -math.cos(az), 0)
    side_v = (math.cos(az), math.sin(az), 0)
    m.blob('Hips', 'bone', c, (0.13 * h, 0.12 * h, 0.13 * h), u=6, v=4)
    m.box('Hips', 'bone', add(c, (out[0] * 0.04 * h, out[1] * 0.04 * h, -0.12 * h)), (0.14 * h, 0.14 * h, 0.07 * h), rot=(0, 0, math.degrees(az)), bevel=0.01 * h)
    for e in (-1, 1):   # eye holes
        m.blob('Hips', 'dark', add(c, (out[0] * 0.11 * h + side_v[0] * e * 0.05 * h, out[1] * 0.11 * h + side_v[1] * e * 0.05 * h, 0.01 * h)), (0.035 * h,) * 3, u=4, v=3)

# ---------------- vine limbs ----------------
for side, s in SIDES:
    sh = P(0.98 * s, 0.05, 0.05)
    el = add(sh, (0.55 * s, -0.15, -0.5))
    wr = add(el, (0.15 * s, -0.45, -0.35))
    arm = [f'Arm{side}', f'Fore{side}']
    m.loft(arm, 'vine', [sh, el, wr], [(0.16, 0.16), (0.13, 0.13), (0.1, 0.1)], sides=5, steps=2, smooth=False)
    m.loft(arm, 'vine', [add(sh, (0, 0.06, 0.08)), add(el, (0.05 * s, 0.05, 0.1)), add(wr, (0, 0.05, 0.08))],
           [(0.06, 0.06)] * 3, sides=4, steps=2, smooth=False)   # a second vine twisting round the first
    for f, d in ((0.3, (s, 0.3, 0.6)), (0.6, (s, -0.4, 0.2)), (0.85, (s * 0.4, 0.8, 0.3))):
        p = tuple(a + (b - a) * f for a, b in zip(sh, el)) if f < 0.5 else tuple(a + (b - a) * (f - 0.5) * 2 for a, b in zip(el, wr))
        m.spike(arm[0] if f < 0.5 else arm[1], 'thorn', p, d, 0.22, 0.08, snap=False)
    for k in (-1, 0, 1):   # root claws
        m.spike(f'Fore{side}', 'claw', wr, (0.25 * k + 0.1 * s, -0.7, -0.6), 0.32, 0.08, snap=False)
    m.blob(f'Fore{side}', 'root', wr, (0.15, 0.15, 0.13), u=6, v=4)
    # legs
    hip, knee, ank = (0.42 * s, 0.1, 1.15), (0.5 * s, -0.25, 0.6), (0.5 * s, 0.15, 0.22)
    leg = [f'Thigh{side}', f'Shin{side}', f'Foot{side}']
    m.loft(leg, 'vine', [hip, knee, ank], [(0.2, 0.2), (0.15, 0.15), (0.12, 0.12)], sides=5, steps=2, smooth=False)
    m.spike(f'Shin{side}', 'thorn', knee, (s, -0.5, 0.2), 0.22, 0.08, snap=False)
    m.box(f'Foot{side}', 'root', (0.5 * s, -0.05, 0.12), (0.42, 0.62, 0.24), bevel=0.06)
    for k in (-1, 0, 1):
        m.spike(f'Foot{side}', 'claw', (0.5 * s + 0.13 * k, -0.35, 0.1), (0.2 * k, -1, -0.2), 0.26, 0.08, snap=False)

# the rusty sickle in the right hand: a wooden haft and a crescent blade with a glowing edge
grip = add(P(-0.98, 0.05, 0.05), (-0.7, -0.6, -0.85))
haft_top = add(grip, (0, -0.15, 1.15))
m.loft('ForeR', 'wood', [add(grip, (0, 0.05, -0.35)), haft_top], [(0.07, 0.07), (0.06, 0.06)], sides=6, steps=1, smooth=False)
m.loft('ForeR', 'rust', [add(haft_top, (0, 0, -0.08)), add(haft_top, (0, 0, 0.04))], [(0.09, 0.09)] * 2, sides=6, steps=1, smooth=False)
lead, trail, edge_a, edge_b = [], [], [], []
for k in range(8):
    a = math.pi * 0.95 * k / 7
    r_out, r_in = 1.15, 1.15 - 0.36 * math.sin(math.pi * k / 7) - 0.05
    cx, cz = haft_top[1] - 1.15, haft_top[2]
    lead.append((haft_top[0], cx + math.cos(a) * r_out, cz + math.sin(a) * r_out * 0.8))
    trail.append((haft_top[0], cx + math.cos(a) * r_in, cz + math.sin(a) * r_in * 0.8))
    edge_a.append((haft_top[0], cx + math.cos(a) * (r_in + 0.02), cz + math.sin(a) * (r_in + 0.02) * 0.8))
    edge_b.append((haft_top[0], cx + math.cos(a) * (r_in - 0.05), cz + math.sin(a) * (r_in - 0.05) * 0.8))
m.strip('ForeR', 'blade', lead, trail, thickness=0.05)
m.strip('ForeR', 'glow2', edge_a, edge_b, thickness=0.06)
m.socket('Blade', 'ForeR', edge_b[3])
for k in (2, 4, 6):   # hooked spikes on the back of the blade, and rust-eaten notches
    m.spike('ForeR', 'blade', lead[k], (0, lead[k][1] - (haft_top[1] - 1.15), lead[k][2] - haft_top[2]), 0.2, 0.09, snap=False)
    m.box('ForeR', 'rust', tuple((a + b) / 2 for a, b in zip(lead[k - 1], trail[k - 1])), (0.07, 0.12, 0.12), bevel=0.0)
for k in range(4):   # leather wraps up the haft, and a skull charm on a cord
    z = grip[2] - 0.25 + 0.3 * k
    m.loft('ForeR', 'rope', [(grip[0], grip[1], z), (grip[0], grip[1], z + 0.08)], [(0.085, 0.085)] * 2, sides=6, steps=1, smooth=False)
m.blob('ForeR', 'bone', add(grip, (0.08, 0.05, -0.5)), (0.1, 0.09, 0.1), u=6, v=4)
m.blob('ForeR', 'glow', add(grip, (0.08, -0.03, -0.49)), (0.06, 0.03, 0.03), u=4, v=3)

# ---------------- animation ----------------
LEGS = {side: (f'Thigh{side}', f'Shin{side}', f'Foot{side}') for side, _ in SIDES}
WALK = dict(stride=0.95, lift=0.3, duty=0.58, frames=26)
RUN = dict(stride=1.7, lift=0.45, duty=0.45, frames=18)


def legs(pose, t_, g_, bob):
    for (side, _), ph in zip(SIDES, (0.0, 0.5)):
        u = (t_ + ph) % 1.0
        D = g_['stride'] * S
        if u < g_['duty']:
            dy, dz = D / 2 - D * u / g_['duty'], 0.0
        else:
            q = (u - g_['duty']) / (1 - g_['duty'])
            dy, dz = -D / 2 + D * smooth01(q), g_['lift'] * S * math.sin(math.pi * q)
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - dy, az + dz), shift=(0, bob))


def planted(pose, bob=0.0, dy=0.0):
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay + dy, az), shift=(0, bob))


def arms(pose, l, r, rz=0.0):
    pose['ArmL'] = ((-l, 0, 0), (0, 0, 0))
    pose['ArmR'] = ((-r, 0, rz), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    bob = 0.05 * S * math.sin(2 * p)
    pose = {
        'Hips': ((0, 0, 0), (0, 0, bob)),
        'Chest': ((3 * math.sin(p), 0, 6 * math.sin(p * 0.5)), (0, 0, 0)),
        'Jaw': ((6 + 5 * math.sin(3 * p), 0, 0), (0, 0, 0)),
        'Stem': ((5 * math.sin(p + 1), 0, 8 * math.sin(p)), (0, 0, 0)),
    }
    arms(pose, 6 * math.sin(p), -4 * math.sin(p))
    planted(pose, bob)
    return pose


def walk(t_):   # a lurching, heavy waddle - the pumpkin rolls side to side
    p = TAU * t_
    bob = 0.1 * S * abs(math.sin(p))
    pose = {
        'Hips': ((0, 8 * math.sin(p), 0), (0, 0, bob)),
        'Chest': ((-6, -10 * math.sin(p), 6 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((10 + 6 * abs(math.sin(2 * p)), 0, 0), (0, 0, 0)),
        'Stem': ((8 * math.sin(2 * p), 0, -10 * math.sin(p)), (0, 0, 0)),
    }
    arms(pose, 25 * math.sin(p), -15 * math.sin(p))
    legs(pose, t_, WALK, bob)
    return pose


def run(t_):
    p = TAU * t_
    bob = 0.16 * S * abs(math.sin(p))
    pose = {
        'Hips': ((12, 6 * math.sin(p), 0), (0, 0, bob)),
        'Chest': ((10, -8 * math.sin(p), 8 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((22, 0, 0), (0, 0, 0)),
        'Stem': ((-20, 0, -12 * math.sin(p)), (0, 0, 0)),
    }
    arms(pose, 45 * math.sin(p), -40 * math.sin(p))
    legs(pose, t_, RUN, bob)
    return pose


def sleep(t_):   # squats down, the fire in its face dims to a flicker
    p = TAU * t_
    drop = -0.55 * S
    pose = {
        'Hips': ((0, 0, 0), (0, 0, drop + 0.03 * S * math.sin(p))),
        'Chest': ((14 + 2 * math.sin(p), 0, 0), (0, 0, 0)),
        'Jaw': ((0, 0, 0), (0, 0, 0)),
        'Stem': ((25, 0, 10), (0, 0, 0)),
    }
    arms(pose, -20, -10)
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - 0.25 * S, az), shift=(0, drop))
    return pose


def roar(t_):    # jaw flung open on the fire inside, arms out
    e = envelope(t_, 0.2, 0.75)
    sh = math.sin(TAU * 8 * t_) * envelope(t_, 0.25, 0.7, 0.8)
    pose = {
        'Chest': ((-16 * e, 0, 6 * sh), (0, 0, 0)),
        'Jaw': ((48 * e, 0, 0), (0, 0, 0)),
        'Stem': ((-20 * e, 0, 10 * sh), (0, 0, 0)),
    }
    arms(pose, 60 * e, 75 * e, 20 * e)
    planted(pose)
    return pose


def attack(t_):  # wind the sickle back, then a big overhead chop
    w = envelope(t_, 0.32, 0.34, 0.42)
    c = smooth01((t_ - 0.34) / 0.12) if t_ < 0.65 else 1 - smooth01((t_ - 0.65) / 0.35)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, -0.4 * S * c, 0)),
        'Chest': ((-10 * w + 20 * c, 0, 15 * w - 10 * c), (0, 0, 0)),
        'Jaw': ((15 * w + 30 * c, 0, 0), (0, 0, 0)),
    }
    pose['ArmR'] = ((-140 * w + 160 * c, 0, 0), (0, 0, 0))
    pose['ForeR'] = ((-30 * w + 20 * c, 0, 0), (0, 0, 0))
    pose['ArmL'] = ((10 * w, 0, 0), (0, 0, 0))
    planted(pose, 0.0, -0.4 * S * c)
    return pose


def happy(t_):   # hop and twirl, swinging the sickle overhead
    e = envelope(t_, 0.1, 0.8)
    hop = math.sin(math.pi * smooth01(t_ / 0.55)) if t_ < 0.55 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 360 * smooth01(t_ / 0.6) if t_ < 0.6 else 0), (0, 0, 0.8 * S * hop)),
        'Jaw': ((30 * e, 0, 0), (0, 0, 0)),
        'Stem': ((0, 0, 30 * math.sin(TAU * 3 * t_) * e), (0, 0, 0)),
    }
    arms(pose, 70 * e, 150 * e)
    planted(pose)
    return pose


m.anim('Idle', 72, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, walk, key_step=1)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, roar, key_step=2)
m.anim('Attack', 36, False, attack, key_step=2)
m.anim('Happy', 42, False, happy, key_step=1)
m.refs = {'Walk': WALK['stride'] * S / (WALK['duty'] * WALK['frames'] / 30), 'Run': RUN['stride'] * S / (RUN['duty'] * RUN['frames'] / 30)}
m.build(OUT)
