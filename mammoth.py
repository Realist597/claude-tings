"""Woolly Mammoth - Epic Frost Peaks mammoth: a giant on pillar legs with a domed head, a shoulder
hump, a long shaggy skirt of fur, little flapping ears, huge curving tusks and a 4-bone trunk that
sways as it walks, curls up when it sleeps and raises to trumpet. Snow and ice crystals on its back.
Faces -Y. Uses the four-legged body plan plus its own Trunk1-4 and Ear bones.
Sockets: TrunkTip (frost breath / trumpet), TuskL/TuskR (glints), Crystal1/Crystal2 (back crystals)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quadruped import build, standard_eyes, TAU
from kit import envelope


def trunk_points(c):
    H, k = c.H, 0.6 + 0.4 * c.grow
    return [H(0, -1.75, -0.25), H(0, -2.0, -0.25 - 0.95 * k), H(0, -2.05, -0.25 - 1.85 * k),
            H(0, -1.95, -0.25 - 2.65 * k), H(0, -1.65, -0.25 - 3.2 * k)]


def bones(c):
    m = c.m
    pts = trunk_points(c)
    parent = 'Head'
    for i in range(4):
        m.bone(f'Trunk{i + 1}', pts[i], pts[i + 1], parent)
        parent = f'Trunk{i + 1}'
    for side, s in c.SIDES:
        m.bone(f'Ear{side}', c.H(1.0 * s, -0.4, 0.4), c.H(1.6 * s, 0.1, -0.2), 'Head')


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # chunky style: a blocky domed skull with a war-helm of ice plates, a heavy brow over glowing eyes,
    # a chiselled ridged trunk, huge faceted tusks banded with ice, a shaggy crown of spiky fur
    m.box('Head', 'skin', H(0, -0.85, 0.2), (2.3 * h, 2.1 * h, 2.5 * h), bevel=0.35 * h, segs=1,
          taper=dict(axis='z', end=-1, scale=(0.85, 0.9)))
    m.box('Head', 'plate', H(0, -1.2, 1.05), (1.8 * h, 1.3 * h, 0.35 * h), rot=(-20, 0, 0), bevel=0.06 * h)
    m.box('Head', 'plate', H(0, -1.88, 0.62), (1.0 * h, 0.2 * h, 0.7 * h), rot=(-10, 0, 0), bevel=0.05 * h)
    m.spike('Head', 'ice', H(0, -1.95, 0.95), (0, -0.4, 1), (0.5 + 0.5 * g) * h, 0.3 * h, twist=45)
    for x in (-0.55, -0.2, 0.2, 0.55):
        m.spike('Head', 'fur2' if abs(x) < 0.3 else 'fur', H(x, -0.3, 1.5), (x * 0.8, 0.5, 1.0), 0.85 * h, 0.4 * h, 0.22 * h)
    # trunk: chiselled, tapering to a curled tip, with dark ridges
    pts = trunk_points(c)
    radii = [(0.58 * h, 0.52 * h), (0.44 * h, 0.42 * h), (0.34 * h, 0.33 * h), (0.26 * h, 0.25 * h), (0.18 * h, 0.18 * h)]
    m.loft(['Head', 'Trunk1', 'Trunk2', 'Trunk3', 'Trunk4'], 'skin', pts, radii, sides=6, steps=3, smooth=False, up=(0, -1, 0))
    for i in range(1, 4):
        p, r = pts[i], radii[i][0]
        m.box(f'Trunk{i}', 'skin2', (p[0], p[1] - r * 0.15, p[2]), (r * 2.15, r * 1.95, 0.1 * h), bevel=0.02)
    m.box('Trunk4', 'skin2', pts[4], (0.4 * h, 0.4 * h, 0.22 * h), bevel=0.05 * h)
    m.socket('TrunkTip', 'Trunk4', pts[4])
    # mouth under the trunk
    m.box('Head', 'mouth', H(0, -1.35, -0.95), (0.8 * h, 0.6 * h, 0.2 * h), bevel=0.06 * h)
    m.box('Jaw', 'skin', H(0, -1.25, -1.15), (0.9 * h, 0.75 * h, 0.35 * h), bevel=0.06 * h)
    for side, s in c.SIDES:
        # huge faceted tusks sweeping forward, up and in, with ice bands
        k = 0.45 + 0.55 * g
        tusk = [H(0.6 * s, -1.5, -0.75), H(0.85 * s, -2.1 - 0.4 * k, -1.4 * k), H(0.8 * s, -2.65 - 0.8 * k, -0.9 * k),
                H(0.42 * s, -2.85 - 1.0 * k, 0.2 * k)]
        m.loft('Head', 'tusk', tusk, [(0.3 * h, 0.3 * h), (0.24 * h, 0.24 * h), (0.16 * h, 0.16 * h), (0.04 * h, 0.04 * h)],
               sides=6, steps=4, smooth=False)
        m.spike('Head', 'ice', tusk[2], (0.6 * s, 0.2, 0.6), (0.3 + 0.3 * g) * h, 0.16 * h, twist=45)
        m.socket(f'Tusk{side}', 'Head', tusk[-1])
        # small furry ears that flap
        m.box(f'Ear{side}', 'fur', H(1.25 * s, -0.25, 0.15), (0.25 * h, 0.95 * h, 1.1 * h), rot=(0, 0, 20 * s), bevel=0.08 * h)
        m.box(f'Ear{side}', 'skin2', H(1.2 * s, -0.32, 0.15), (0.1 * h, 0.6 * h, 0.75 * h), rot=(0, 0, 20 * s), bevel=0.04 * h)
        # glowing eyes in dark sockets under a heavy brow
        m.box('Head', 'dark', H(1.05 * s, -1.4, 0.42), (0.18 * h, 0.55 * h, 0.42 * h), bevel=0.04 * h)
        m.box('Head', 'skin2', H(1.0 * s, -1.45, 0.75), (0.4 * h, 0.75 * h, 0.22 * h), rot=(18, 0, 0), bevel=0.04 * h)
    standard_eyes(c, x=1.12, y=-1.38, z=0.42, size=0.3, normal_y=-0.5)


def decor(c):
    m, g = c.m, c.grow
    rng_y = (-1.6, -1.0, -0.4, 0.2, 0.8, 1.4)
    # shoulder hump of thick spiky fur
    for x in (-0.6, 0.0, 0.6):
        p = c.body_pt(-0.9, 3.9)
        m.spike('Chest', 'fur2', (x * c.bW, p[1], p[2] - 0.4), (x * 0.6, 0.6, 1.0), (0.9 + 0.6 * g), 0.75, 0.35)
    # the long shaggy skirt hanging down both flanks
    for side, s in c.SIDES:
        for i, ya in enumerate(rng_y):
            p = c.body_pt(ya, 2.0)
            for j, dz in enumerate((0.0, -0.55)):
                k = (0.9 + 0.7 * g) * (1.0 - 0.15 * j)
                m.spike(c.spine_bone(p[1]), 'fur' if (i + j) % 2 else 'fur2',
                        (1.55 * c.bW * s, p[1] + 0.15 * j, p[2] + dz), (0.35 * s, 0.15, -1.0), 1.35 * k, 0.6, 0.26)
        for y in (c.yF, c.yB):
            m.spike('Chest' if y < 0 else 'Hips', 'fur', (1.3 * c.bW * s, y, c.hipZ - 0.2), (0.3 * s, 0, -1), 1.15 * (0.7 + 0.3 * g), 0.7, 0.3)
        # an ice-armour saddle plate over each flank
        if g > 0.25:
            for ya in (-0.7, 0.5):
                p = c.body_pt(ya, 3.5)
                m.box(c.spine_bone(p[1]), 'plate', (0.95 * c.bW * s, p[1], p[2]), (1.1, 1.0, 0.24), rot=(0, 32 * s, 0), bevel=0.06)
    # snow drifts and a ridge of big ice crystals down the back
    for ya, x, r in ((-0.6, 0.35, 0.9), (0.4, -0.4, 0.75), (1.2, 0.2, 0.6)):
        p = c.body_pt(ya, 3.72)
        m.box(c.spine_bone(p[1]), 'snow', (x * c.bW, p[1], p[2] - 0.1), (r * 1.5, r * 1.5, 0.3), rot=(0, 0, 20 * x), bevel=0.08)
    if g > 0.25:
        for i, ya in enumerate((-0.5, 0.25, 1.0)):
            p = c.body_pt(ya, 3.75)
            for d, k in (((0, 0.2, 1), 1.0), ((0.55, 0.3, 1), 0.7), ((-0.55, 0.1, 1), 0.7)):
                m.spike(c.spine_bone(p[1]), 'ice', (0, p[1], p[2] - 0.3), d, (1.0 * k * g + 0.25) * (1 - 0.15 * i), 0.4 * k, twist=45)
            if i < 2:
                m.socket(f'Crystal{i + 1}', c.spine_bone(p[1]), (0, p[1], p[2] + 1.0))
    # tail with a hair tuft
    m.spike('Tail3', 'fur2', c.tailEnd, (0, 0.6, -1.0), 0.75, 0.35, 0.22)


def pose(c, clip, t, p):
    E = c.E
    if clip == 'Idle':
        sway, curl, flap = 10 * math.sin(TAU * t), -6 + 8 * math.sin(TAU * t + 1), 12 * math.sin(TAU * 2 * t)
    elif clip == 'Walk':
        sway, curl, flap = 14 * math.sin(TAU * t), 4 * math.sin(TAU * 2 * t), 8 * math.sin(TAU * t)
    elif clip == 'Run':
        sway, curl, flap = 6 * math.sin(TAU * t), -25, 20 * math.sin(TAU * t)
    elif clip == 'Sleep':
        sway, curl, flap = 0, 30, 0   # curled back under the chin
    elif clip == 'Roar':
        e = envelope(t, 0.2, 0.75)   # trumpet: trunk raised high and curled back
        sway, curl, flap = 4 * math.sin(TAU * 6 * t) * e, -55 * e, 35 * e
    elif clip == 'Attack':
        e = envelope(t, 0.25, 0.4, 0.7)
        sway, curl, flap = 35 * e * math.sin(TAU * t), -20 * e, 10 * e
    else:  # Happy: wave the trunk about
        e = envelope(t, 0.1, 0.7)
        sway, curl, flap = 25 * e * math.sin(TAU * 3 * t), -40 * e, 25 * e * math.sin(TAU * 3 * t)
    for i in range(4):
        k = 0.6 + 0.25 * i
        p[f'Trunk{i + 1}'] = ((curl * k * E, sway * k * (0.5 + 0.3 * i), 0), (0, 0, 0))
    for side, s in c.SIDES:
        p[f'Ear{side}'] = ((0, 0, flap * s), (0, 0, 0))


build(dict(
    name='WoollyMammoth',
    palette={
        'body': '#6e4630', 'fur': '#5a3624', 'fur2': '#8a5a3a', 'skin': '#54423e', 'skin2': '#3a2c28',
        'belly': '#4e3222', 'tusk': ('#eaf6ff', False), 'snow': '#f4f8ff', 'ice': ('#8ff0ff', False),
        'plate': ('#6fb8ea', True, True), 'dark': ('#0d1222', False),
        'foot': '#3a2c28', 'claw': ('#d9cfc2', False), 'mouth': ('#5a1e22', False), 'tongue': '#d6405c',
        'eye_dark': ('#0d1222', False), 'iris': ('#3ff0ff', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.3, legT=1.65, bL=1.15, bW=1.25, bH=1.3, girth=1.18, head=1.3, neck=0.4, neckUp=1.3,
              tail=0.5, tailDroop=1.8, eye=0.85),
    gait=dict(stride=0.95, duty=1.1),
    sides=6, kneePlates='plate',
    bones=bones, head=head, decor=decor, pose=pose,
))
