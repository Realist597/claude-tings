"""Skull Crawler - Common Underworld critter: a big outlined ivory skull with two dark horns and
ember-glowing cracks, scuttling on six chunky black spider legs with glowing red tips (alternating
tripod gait), ember fire blazing up out of its eye sockets, a chattering jaw full of teeth and a
melting candle stuck on top with a big flame. Faces -Y.
    blender -b --python skullcrawler.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: EyeL/EyeR (ember glow), Candle (flame)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from mathutils import Vector, Matrix
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('SkullCrawler', {
    'bone': ('#efe4c8', True, True), 'bone2': ('#cbbd9e', True, True), 'dark': ('#140e10', False), 'ember': ('#ff7a1e', False), 'leg': ('#1e1820', True, True),
    'leg2': '#3a2e40', 'tip': ('#ff3a2a', False), 'wax': '#f2ead6', 'flame': ('#ffc43a', False), 'crack': ('#ff7a1e', False),
    'horn': ('#1a1416', False, True),
    'eye_dark': ('#120709', False), 'iris': ('#ff7a1e', False), 'eye_glint': ('#ffe9b0', False),
}, {'Child': dict(head=1.0), 'Teen': dict(head=1.0)})
S, E, g = st['S'], st['energy'], st['grow']
SIDES = (('L', 1), ('R', -1))
CZ = 1.75   # skull centre height
LEG_ANGLES = (('1', 40), ('2', 90), ('3', 140))   # degrees from straight ahead
leg_len = 0.75 + 0.25 * g


def leg_points(side, s, ang):
    a = math.radians(ang)
    d = Vector((math.sin(a) * s, -math.cos(a), 0))
    hip = Vector((0, 0, CZ - 0.35)) + d * 0.95
    knee = hip + d * 1.15 * leg_len + Vector((0, 0, 0.95 * leg_len))
    foot = hip + d * 2.3 * leg_len + Vector((0, 0, -(CZ - 0.35)))
    foot.z = 0.05
    return hip, knee, foot, d


# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Body', (0, 0.6, CZ), (0, -0.7, CZ + 0.1), 'MonsterRoot')
m.bone('Jaw', (0, -0.25, CZ - 0.7), (0, -1.25, CZ - 0.85), 'Body')
for side, s in SIDES:
    for tag, ang in LEG_ANGLES:
        hip, knee, foot, d = leg_points(side, s, ang)
        m.bone(f'LegA{side}{tag}', tuple(hip), tuple(knee), 'Body')
        m.bone(f'LegB{side}{tag}', tuple(knee), tuple(foot), f'LegA{side}{tag}')

# ---------------- skull ----------------
m.blob('Body', 'bone', (0, 0.05, CZ + 0.15), (1.25, 1.35, 1.12), u=12, v=9)
m.blob('Body', 'bone', (0, -0.8, CZ - 0.35), (0.85, 0.65, 0.6), u=10, v=7)   # face / maxilla
for side, s in SIDES:
    # deep eye sockets with ember fire
    m.blob('Body', 'dark', (0.48 * s, -1.0, CZ + 0.05), (0.36, 0.25, 0.32), u=8, v=6)
    m.blob('Body', 'ember', (0.48 * s, -1.08, CZ + 0.05), (0.2, 0.12, 0.18), u=6, v=4)
    m.spike('Body', 'ember', (0.48 * s, -1.12, CZ + 0.15), (0.15 * s, -0.3, 1), 0.5, 0.22, 0.1)   # fire blazing out of the socket
    # two dark horns curling up off the brow
    prev = Vector((0.55 * s, -0.4, CZ + 0.95))
    for j in range(3):
        d = Vector((0.5 * s, 0.3 * j, 1 - 0.25 * j)).normalized()
        seg = (0.35 - 0.06 * j) * (0.6 + 0.4 * g)
        m.spike('Body', 'horn', tuple(prev), tuple(d), seg * 1.7, 0.2 - 0.04 * j, snap=False)
        prev = prev + d * seg
    m.socket(f'Eye{side}', 'Body', (0.48 * s, -1.15, CZ + 0.05))
    m.blob('Body', 'bone2', (0.85 * s, -0.75, CZ - 0.3), (0.25, 0.35, 0.18), u=8, v=5)   # cheekbone
m.spike('Body', 'dark', (0, -1.28, CZ - 0.4), (0, -0.3, 1), 0.3, 0.22, 0.08, snap=False)   # nasal cavity
for k in range(6):
    x = -0.45 + 0.18 * k
    m.box('Body', 'bone2', (x, -1.12 + abs(x) * 0.25, CZ - 0.72), (0.14, 0.12, 0.2), bevel=0.03)
# jaw with lower teeth
m.box('Jaw', 'bone2', (0, -0.75, CZ - 0.92), (1.1, 1.05, 0.28), bevel=0.1, taper=dict(axis='y', end=-1, scale=(0.75, 0.85)))
for k in range(5):
    x = -0.36 + 0.18 * k
    m.box('Jaw', 'bone', (x, -1.12 + abs(x) * 0.25, CZ - 0.75), (0.13, 0.11, 0.16), bevel=0.03)
# cracks across the cranium
for pts in (((0.3, -0.55, CZ + 1.0), (0.45, -0.2, CZ + 1.12), (0.3, 0.15, CZ + 1.15), (0.5, 0.45, CZ + 1.02)),
            ((-0.6, 0.3, CZ + 0.95), (-0.85, 0.5, CZ + 0.7), (-1.0, 0.35, CZ + 0.4)),
            ((-0.2, -0.75, CZ + 0.9), (-0.45, -0.5, CZ + 1.05), (-0.35, -0.1, CZ + 1.16)),
            ((1.0, 0.1, CZ + 0.55), (1.15, 0.4, CZ + 0.3), (1.05, 0.7, CZ + 0.1))):
    m.loft('Body', 'crack', list(pts), [(0.12, 0.12)] * len(pts), sides=4, steps=1, smooth=False)
# melting candle with a flame
cz = CZ + 1.18
m.loft('Body', 'wax', [(-0.15, 0.1, cz - 0.1), (-0.15, 0.1, cz + 0.65 * (0.5 + 0.5 * g))], [(0.17, 0.17), (0.15, 0.15)], sides=8, steps=1, smooth=False)
for dx, dy, l in ((0.12, 0.0, 0.35), (-0.3, 0.12, 0.25), (-0.1, 0.25, 0.3)):
    m.spike('Body', 'wax', (-0.15 + dx, 0.1 + dy, cz + 0.45 * (0.5 + 0.5 * g)), (dx, dy, -1), l, 0.1, snap=False)
ft = (-0.15, 0.1, cz + 0.65 * (0.5 + 0.5 * g) + 0.05)
m.blob('Body', 'flame', add(ft, (0, 0, 0.2)), (0.16, 0.16, 0.3), u=6, v=5)
m.socket('Candle', 'Body', add(ft, (0, 0, 0.3)))

# ---------------- legs ----------------
for side, s in SIDES:
    for tag, ang in LEG_ANGLES:
        hip, knee, foot, d = leg_points(side, s, ang)
        A, B = f'LegA{side}{tag}', f'LegB{side}{tag}'
        m.loft([A], 'leg', [tuple(hip), tuple(knee)], [(0.26, 0.26), (0.18, 0.18)], sides=6, steps=1, smooth=False)
        m.blob([A, B], 'leg2', tuple(knee), (0.24, 0.24, 0.24), u=6, v=5)
        mid = knee.lerp(foot, 0.55)
        m.loft([B], 'leg', [tuple(knee), tuple(mid), tuple(foot)], [(0.18, 0.18), (0.13, 0.13), (0.05, 0.05)], sides=6, steps=1, smooth=False)
        m.spike(B, 'tip', tuple(mid.lerp(foot, 0.55)), tuple((foot - mid).normalized()), (foot - mid).length * 0.55, 0.17, snap=False)
        for t in (0.35, 0.7):
            p = hip.lerp(knee, t) if t < 0.5 else knee.lerp(mid, t)
            m.spike(A if t < 0.5 else B, 'leg2', tuple(p), (0, 0, 1), 0.28, 0.1, snap=False)


# ---------------- animation ----------------
GROUP_A = {('L', '1'), ('R', '2'), ('L', '3')}
WALK = dict(stride=1.4, frames=20)
RUN = dict(stride=2.6, frames=14)


def leg_pose(pose, side, s, tag, ang, lift, swing):
    a = math.radians(ang)
    tangent = Vector((math.sin(a) * s, -math.cos(a), 0)).cross(Vector((0, 0, 1)))   # turning about this lifts the leg
    rA = Matrix.Rotation(math.radians(swing), 3, 'Z') @ Matrix.Rotation(math.radians(lift), 3, tangent)
    rB = Matrix.Rotation(math.radians(-lift * 0.6), 3, tangent)
    pose[f'LegA{side}{tag}'] = (tuple(math.degrees(x) for x in rA.to_euler('XYZ')), (0, 0, 0))
    pose[f'LegB{side}{tag}'] = (tuple(math.degrees(x) for x in rB.to_euler('XYZ')), (0, 0, 0))


def scuttle(t_, gait, amp):
    p = TAU * t_
    pose = {
        'Body': ((3 * math.sin(2 * p), 4 * math.sin(p), 3 * math.sin(p)), (0, 0, 0.08 * S * abs(math.sin(2 * p)))),
        'Jaw': ((10 + 10 * math.sin(TAU * 4 * t_), 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        for tag, ang in LEG_ANGLES:
            ph = 0.0 if (side, tag) in GROUP_A else 0.5
            u = (t_ + ph) % 1.0
            if u < 0.5:   # planted, sweeping back
                lift, swing = 0.0, (-amp + 2 * amp * (u / 0.5)) * s
            else:
                q = (u - 0.5) / 0.5
                lift, swing = 30 * math.sin(math.pi * q), (amp - 2 * amp * smooth01(q)) * s
            leg_pose(pose, side, s, tag, ang, lift, swing)
    return pose


def idle(t_):
    p = TAU * t_
    chatter = max(0.0, math.sin(TAU * 6 * t_)) * envelope(t_, 0.4, 0.6, 0.7)
    pose = {
        'Body': ((2 * math.sin(p), 0, 10 * math.sin(p * 0.5)), (0, 0, 0.03 * S * math.sin(2 * p))),
        'Jaw': ((5 + 20 * chatter, 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        for i, (tag, ang) in enumerate(LEG_ANGLES):
            tap = max(0.0, math.sin(TAU * 2 * t_ + i * 2 + (0 if s > 0 else 1))) * 12
            leg_pose(pose, side, s, tag, ang, tap, 0)
    return pose


def happy(t_):
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 360 * smooth01(t_ / 0.7) if t_ < 0.7 else 0), (0, 0, 0.9 * S * hop)),
        'Jaw': ((25 * envelope(t_, 0.1, 0.8), 0, 0), (0, 0, 0)),
    }
    for side, s in SIDES:
        for tag, ang in LEG_ANGLES:
            leg_pose(pose, side, s, tag, ang, 35 * hop, 0)
    return pose


def sleep(t_):
    pose = {'Body': ((4, 0, 0), (0, 0, -0.8 * S + 0.03 * S * math.sin(TAU * t_))), 'Jaw': ((0, 0, 0), (0, 0, 0))}
    for side, s in SIDES:
        for tag, ang in LEG_ANGLES:
            leg_pose(pose, side, s, tag, ang, 45, 0)
    return pose


def rear(t_):
    e = envelope(t_, 0.2, 0.75)
    pose = {'Body': ((-25 * e, 0, 0), (0, 0.3 * S * e, 0.4 * S * e)), 'Jaw': ((40 * e, 0, 0), (0, 0, 0))}
    for side, s in SIDES:
        for tag, ang in LEG_ANGLES:
            leg_pose(pose, side, s, tag, ang, (70 if tag == '1' else 10) * e + 10 * math.sin(TAU * 6 * t_) * e, 0)
    return pose


m.anim('Idle', 72, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, lambda t_: scuttle(t_, WALK, 18), key_step=1)
m.anim('Run', RUN['frames'], True, lambda t_: scuttle(t_, RUN, 26), key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, rear, key_step=2)
m.anim('Attack', 30, False, rear, key_step=2)
m.anim('Happy', 40, False, happy, key_step=1)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
