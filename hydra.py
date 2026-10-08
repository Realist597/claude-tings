"""Hydra - Legendary Mythic serpent-dragon with FIVE heads, each on a long two-bone neck that weaves
on its own: serpent skulls with a frilled crest, horns, fangs, a forked tongue and glowing venom
eyes in dark sockets under angry brow ridges. A heavy dark abyss-teal body in outlined scale plates on
four clawed legs, glowing venom bands up the throat of every neck, a finned crest down the spine and
tail with glowing tips, and venom glands glowing along the flanks. Faces -Y. Uses the four-legged body plan; the
centre head uses its Neck/Head/Jaw, the other four heads get their own neck chains.
Sockets: Venom1-5 (mouth drips), Glow1-4 (flank glands), TailFin."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from mathutils import Vector, Matrix
from quadruped import build, TAU
from kit import envelope

# extra heads: (tag, x offset at the chest, yaw outward, neck length, rise)
EXTRA = [('L1', 0.65, 20, 1.15, 1.0), ('R1', -0.65, -20, 1.15, 1.0), ('L2', 1.25, 48, 0.95, 0.8), ('R2', -1.25, -48, 0.95, 0.8)]


def rz(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), v[2])


def necks(c):
    """(tag, n1, n2, head, jaw, base, mid, hp, yaw) for the four extra necks"""
    out = []
    nk = c.st['neck']
    for tag, x, yaw, length, rise in EXTRA:
        base = c.add(c.neckStart, (x * c.bW, 0.35, -0.25))
        mid = c.add(base, rz((0, -1.0 * length * nk, 1.35 * rise * nk), yaw))
        hp = c.add(mid, rz((0, -1.1 * length * nk, 1.0 * rise * nk), yaw))
        out.append((tag, f'NeckA{tag}', f'NeckB{tag}', f'Head{tag}', f'Jaw{tag}', base, mid, hp, yaw))
    return out


def bones(c):
    m = c.m
    for tag, n1, n2, head, jaw, base, mid, hp, yaw in necks(c):
        h = c.h * 0.85
        P = lambda dx, dy, dz: c.add(hp, rz((dx * h, dy * h, dz * h), yaw))
        m.bone(n1, base, mid, 'Chest')
        m.bone(n2, mid, hp, n1)
        m.bone(head, hp, P(0, -2.0, 0), n2)
        m.bone(jaw, P(0, -0.3, -0.45), P(0, -1.9, -0.55), head)


def serpent_head(c, head, jaw, hp, yaw, h, tag):
    m, g = c.m, c.grow
    P = lambda dx, dy, dz: c.add(hp, rz((dx * h, dy * h, dz * h), yaw))
    D = lambda dx, dy, dz: rz((dx, dy, dz), yaw)
    m.box(head, 'body', P(0, -0.7, 0.1), (1.35 * h, 1.7 * h, 1.05 * h), rot=(0, 0, yaw), bevel=0.3 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.75, 0.8)))
    m.box(head, 'body2', P(0, -1.7, -0.05), (0.85 * h, 1.15 * h, 0.6 * h), rot=(0, 0, yaw), bevel=0.16 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.7, 0.72)))
    m.box(head, 'scale', P(0, -1.0, 0.6), (1.0 * h, 1.3 * h, 0.16 * h), rot=(-6, 0, yaw), bevel=0.05 * h)
    m.box(head, 'mouth', P(0, -1.45, -0.32), (0.75 * h, 1.5 * h, 0.1 * h), rot=(0, 0, yaw), bevel=0.0)
    m.box(jaw, 'belly', P(0, -1.4, -0.48), (0.8 * h, 1.6 * h, 0.26 * h), rot=(0, 0, yaw), bevel=0.07 * h,
          taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
    # forked tongue
    for s in (-1, 1):
        m.spike(jaw, 'tongue', P(0, -1.6, -0.35), D(0.25 * s, -1, 0.05), 0.75 * h, 0.08 * h, snap=False)
    for side, s in c.SIDES:
        m.spike(head, 'fang', P(0.27 * s, -1.95, -0.32), D(0, -0.2, -1), 0.4 * h, 0.13 * h, snap=False)
        m.box(head, 'dark', P(0.5 * s, -1.05, 0.28), (0.14 * h, 0.5 * h, 0.36 * h), rot=(0, 0, yaw + 12 * s), bevel=0.03 * h)
        m.eye(head, P(0.56 * s, -1.05, 0.28), D(0.85 * s, -0.5, 0.2), 0.22 * h * c.eye)
        m.box(head, 'horn', P(0.45 * s, -1.05, 0.58), (0.45 * h, 0.6 * h, 0.14 * h), rot=(16, 0, yaw - 22 * s), bevel=0.03 * h)   # angry brow
        # horns sweeping back and a frilled crest fanning out behind the jaw
        m.spike(head, 'horn', P(0.35 * s, -0.55, 0.55), D(0.3 * s, 1.0, 0.55), (0.7 + 1.1 * g) * h, 0.3 * h, snap=False)
        for k in range(3):
            m.spike(head, 'fin', P(0.55 * s, -0.25 + 0.1 * k, 0.1 - 0.25 * k), D(1.0 * s, 0.7, 0.4 - 0.45 * k),
                    (0.55 + 0.5 * g) * h * (1.0 - 0.2 * k), 0.35 * h, 0.08 * h)
    m.spike(head, 'fin', P(0, -0.3, 0.6), D(0, 0.7, 1), (0.6 + 0.5 * g) * h, 0.5 * h, 0.08 * h)
    m.socket(f'Venom{tag}', head, P(0, -2.05, -0.45))


def head(c):
    serpent_head(c, 'Head', 'Jaw', c.hp, 0.0, c.h, '1')
    for i, (tag, n1, n2, hb, jaw, base, mid, hp, yaw) in enumerate(necks(c)):
        serpent_head(c, hb, jaw, hp, yaw, c.h * 0.85, str(i + 2))


def decor(c):
    m, g = c.m, c.grow
    # the extra necks
    for tag, n1, n2, hb, jaw, base, mid, hp, yaw in necks(c):
        m.loft(['Chest', n1, n2, hb], 'body', [c.add(base, (0, 0.3, -0.1)), mid, hp, c.add(hp, rz((0, -0.3, 0.05), yaw))],
               [(0.75, 0.75), (0.55, 0.55), (0.48 * c.h, 0.48 * c.h), (0.45 * c.h, 0.45 * c.h)], sides=8, steps=3, smooth=False)
        # belly scales up the front of each neck
        for t in (0.25, 0.55, 0.85):
            p = Vector(base).lerp(Vector(hp), t)
            m.blob([n1, n2][int(t > 0.5)], 'glow' if t == 0.55 else 'belly', tuple(p + Vector(rz((0, -0.42, -0.1), yaw))), (0.42, 0.18, 0.36), rot=(0, 0, yaw), u=8, v=4)
    # rows of overlapping scale plates on the back and a finned crest down the spine
    for i, ya in enumerate((-1.5, -1.0, -0.5, 0.0, 0.5, 1.0)):
        p = c.body_pt(ya, 3.7)
        bone = c.spine_bone(p[1])
        for x in (-0.55, 0.0, 0.55):
            m.box(bone, 'scale' if (i + int(x * 2)) % 2 else 'body2', (x * c.bW, p[1], p[2] - 0.12 - abs(x) * 0.3),
                  (0.62, 0.55, 0.14), rot=(12, x * 30, 0), bevel=0.05)
    spine = [c.body_pt(ya, 3.85) for ya in (-1.6, -0.8, 0.0, 0.8, 1.4)] + [c.tail_pt(ya, za) for ya, za in ((2.6, 2.35), (3.8, 2.0), (4.9, 1.7))]
    lead = [tuple(p) for p in spine]
    trail = [c.add(p, (0, 0.25, 0.75 * (0.6 + 0.4 * g) * (1.0 - 0.06 * i))) for i, p in enumerate(spine)]
    m.strip(['Chest', 'Hips', 'Tail1', 'Tail2'], 'fin', lead, trail, thickness=0.08)
    for p, q in zip(lead, trail):
        m.loft(c.spine_bone(p[1]), 'scale', [p, q], [(0.06, 0.06), (0.03, 0.03)], sides=4, steps=1, smooth=False)
        m.spike(c.spine_bone(p[1]), 'glow', q, (0, 0.3, 1), 0.35 * (0.6 + 0.4 * g), 0.16, 0.06)   # glowing crest tips
    # big fin on the tail tip
    m.box('Tail3', 'fin', c.tailEnd, (0.1, 1.6 * (0.5 + 0.5 * g), 1.2 * (0.5 + 0.5 * g)), bevel=0.04,
          taper=dict(axis='y', end=1, scale=(1, 0.25)))
    m.socket('TailFin', 'Tail3', c.tailEnd)
    # glowing venom glands along the flanks
    k = 0
    for side, s in c.SIDES:
        for ya in (-0.6, 0.6):
            p = c.body_pt(ya, 2.6)
            k += 1
            m.blob(c.spine_bone(p[1]), 'glow', (s * 1.62 * c.bW * c.spec['body']['girth'], p[1], p[2]), (0.16, 0.4, 0.4), u=8, v=5)
            m.socket(f'Glow{k}', c.spine_bone(p[1]), (s * 1.75 * c.bW, p[1], p[2]))


def pose(c, clip, t, p):
    """each extra neck weaves on its own; all five rear up together to roar"""
    E = c.E
    base_neck = p.get('Neck', ((0, 0, 0), (0, 0, 0)))[0]
    base_head = p.get('Head', ((0, 0, 0), (0, 0, 0)))[0]
    base_jaw = p.get('Jaw', ((0, 0, 0), (0, 0, 0)))[0]
    for i, (tag, n1, n2, hb, jaw, base, mid, hp, yaw) in enumerate(necks(c)):
        ph = 1.3 * (i + 1)
        if clip == 'Idle':
            sway, nod, snap = 14 * E * math.sin(TAU * t + ph), 8 * math.sin(TAU * t * 2 + ph), max(0.0, 30 * math.sin(TAU * t + ph) - 22)
        elif clip in ('Walk', 'Run'):
            sway, nod, snap = 10 * math.sin(TAU * t + ph), 6 * math.sin(TAU * 2 * t + ph), 6
        elif clip == 'Sleep':
            sway, nod, snap = (20 if yaw > 0 else -20), 30, 0
        else:
            sway, nod, snap = 6 * math.sin(TAU * 3 * t + ph), 0, 0
        axis = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))

        def rot(pitch, turn):
            mtx = Matrix.Rotation(math.radians(turn), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, axis)
            return tuple(math.degrees(a) for a in mtx.to_euler('XYZ'))
        p[n1] = (rot(base_neck[0] * 0.6 + nod * 0.5, sway * 0.5), (0, 0, 0))
        p[n2] = (rot(base_neck[0] * 0.4 + nod * 0.5, sway * 0.6), (0, 0, 0))
        p[hb] = (rot(base_head[0] - nod * 0.4, sway * 0.3), (0, 0, 0))
        p[jaw] = (rot(base_jaw[0] * 0.6 + snap + 3, 0), (0, 0, 0))


build(dict(
    sides=6,
    name='Hydra',
    palette={
        'body': '#143a3a', 'body2': '#1d4f4c', 'scale': ('#0d2828', True, True), 'belly': '#cfc28a', 'fin': ('#6a2a8a', True, True),
        'horn': ('#ece2c8', False, True), 'fang': ('#f6f0e2', False), 'tongue': ('#d6405c', False), 'glow': ('#8dff4a', False),
        'dark': ('#060b0a', False),
        'foot': '#0c2424', 'claw': ('#e8dcc4', False), 'mouth': '#3a1a24', 'eye_dark': ('#0d1410', False),
        'iris': ('#8dff4a', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.0, legT=1.25, bL=1.15, bW=1.15, bH=1.1, girth=1.12, head=0.9, neck=1.7, neckUp=1.9,
              tail=1.35, tailDroop=0.9, eye=0.9),
    neckRadius=0.7,
    gait=dict(stride=1.0),
    bones=bones, head=head, decor=decor, pose=pose,
))
