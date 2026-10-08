"""Wisp Wolf - Legendary Haunted monster (Haunted Pumpkin featured egg): a huge midnight wolf
wearing a cracked bone-white wolf-skull mask, purple ghost-fire burning in the eye sockets and big
fangs below. A mane of purple ghost-flames rises off its neck and shoulders and runs down the spine,
its ribcage glows through the hide on its flanks, flame tips its ears, broken iron shackles with
snapped chain links hang on its legs over bone knee guards, and its tail is a great plume of ghost
fire trailing light. Faces -Y.
Sockets: Mane1-4 (ghost flames), TailFire + TailTrail (tail plume and its trail), EyeL/EyeR."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, TAU


def flame(m, bone, base, d, length, width, core=True):
    """a ghost-flame tongue: an outer purple blade and a pale hot core"""
    m.spike(bone, 'glow', base, d, length, width, width * 0.45, snap=False)
    if core:
        m.spike(bone, 'glow2', base, d, length * 0.6, width * 0.5, width * 0.25, snap=False)


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # long wolf head under the skull mask
    m.box('Head', 'body', H(0, -0.75, 0.1), (1.55 * h, 1.6 * h, 1.3 * h), bevel=0.35 * h, segs=1)
    m.box('Head', 'body', H(0, -1.9, -0.15), (0.85 * h, 1.4 * h, 0.7 * h), bevel=0.18 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.7, 0.75)))
    m.box('Head', 'mouth', H(0, -1.85, -0.5), (0.75 * h, 1.3 * h, 0.08 * h), bevel=0.0)
    m.box('Jaw', 'body2', H(0, -1.7, -0.62), (0.75 * h, 1.3 * h, 0.22 * h), bevel=0.06 * h, taper=dict(axis='y', end=-1, scale=(0.6, 0.8)))
    m.blob('Head', 'nose', H(0, -2.62, -0.02), (0.16 * h, 0.1 * h, 0.12 * h), u=6, v=4)
    # the skull mask: brow plate, snout plate, cheek guards - outlined bone, with a crack
    m.box('Head', 'bone', H(0, -1.05, 0.55), (1.3 * h, 0.95 * h, 0.22 * h), rot=(-12, 0, 0), bevel=0.06 * h)
    m.box('Head', 'bone', H(0, -1.95, 0.18), (0.7 * h, 1.25 * h, 0.16 * h), rot=(-6, 0, 0), bevel=0.05 * h,
          taper=dict(axis='y', end=-1, scale=(0.7, 1)))
    m.box('Head', 'crack', H(0.18, -1.3, 0.69), (0.04 * h, 0.6 * h, 0.03 * h), rot=(0, 0, 25), bevel=0.0)
    for side, s in c.SIDES:
        m.box('Head', 'bone', H(0.62 * s, -1.3, -0.05), (0.18 * h, 0.9 * h, 0.5 * h), rot=(0, 0, 10 * s), bevel=0.04 * h)
        # sockets with ghost-fire burning in them, slanted angrily
        m.box('Head', 'dark', H(0.42 * s, -1.42, 0.42), (0.36 * h, 0.12 * h, 0.2 * h), rot=(0, -20 * s, 0), bevel=0.02 * h)
        m.eye('Head', H(0.42 * s, -1.47, 0.42), (0.35 * s, -1, 0.15), 0.18 * h * c.eye)
        flame(m, 'Head', H(0.5 * s, -1.45, 0.5), (0.4 * s, 0.6, 0.8), 0.45 * h, 0.16 * h)
        m.socket(f'Eye{side}', 'Head', H(0.42 * s, -1.55, 0.42))
        # fangs, upper and lower
        m.spike('Head', 'fang', H(0.24 * s, -2.35, -0.48), (0, -0.1, -1), 0.45 * h, 0.13 * h, snap=False)
        m.spike('Head', 'fang', H(0.3 * s, -1.9, -0.5), (0, 0, -1), 0.3 * h, 0.1 * h, snap=False)
        m.spike('Jaw', 'fang', H(0.27 * s, -2.1, -0.65), (0, -0.1, 1), 0.28 * h, 0.1 * h, snap=False)
        # ears swept back, flame at the tips
        e0 = H(0.45 * s, -0.35, 0.65)
        m.spike('Head', 'body2', e0, (0.3 * s, 0.6, 0.8), (0.95 + 0.35 * g) * h, 0.55 * h, 0.16 * h)
        flame(m, 'Head', c.add(e0, (0.25 * s * h, 0.45 * h, 0.6 * h)), (0.2 * s, 0.6, 0.8), 0.45 * h, 0.18 * h)


def decor(c):
    m, g, bW, bH = c.m, c.grow, c.bW, c.bH
    k = 0.6 + 0.4 * g
    # ghost-fire mane: rings of flame round the neck, then a crest down the spine
    for ring_i, (dy, r, n) in enumerate(((-0.3, 1.0, 9), (0.1, 1.15, 11))):
        center = c.add(c.neckStart, (0, dy, 0.1))
        for i in range(n):
            a = math.pi * (i + 0.5) / n             # the top half
            p = (math.cos(a) * r * bW, center[1], center[2] + math.sin(a) * r * bH * 0.9)
            d = (math.cos(a) * 0.6, 0.6, math.sin(a))
            flame(m, 'Neck' if ring_i == 0 else 'Chest', p, d, (0.9 + 0.35 * (i % 2)) * k, 0.4, core=i % 2 == 0)
    mane_k = 0
    for ya in (-1.1, -0.5, 0.1, 0.7):
        p = c.body_pt(ya, 3.85)
        flame(m, c.spine_bone(p[1]), p, (0, 0.6, 1), (1.0 - 0.12 * mane_k) * k, 0.45)
        mane_k += 1
        m.socket(f'Mane{mane_k}', c.spine_bone(p[1]), c.add(p, (0, 0.3, 0.6 * k)))
    # jagged outlined fur shards along the back and haunches
    for ya in (-0.8, -0.2, 0.4, 1.0, 1.5):
        for side, s in c.SIDES:
            p = c.body_pt(ya, 3.4)
            m.spike(c.spine_bone(p[1]), 'body2', (0.75 * bW * s, p[1], p[2]), (0.7 * s, 0.5, 0.5), 0.6 * k, 0.4, 0.12)
    # the ribcage glowing through the hide
    for side, s in c.SIDES:
        for j, ya in enumerate((-0.9, -0.55, -0.2, 0.15)):
            pts = []
            for q in range(5):
                za = 3.2 - 0.32 * q
                p = c.body_pt(ya + 0.05 * q, za)
                rw = 1.62 * bW * c.spec['body']['girth'] * math.sqrt(max(0.05, 1 - ((za - 2.45) / 1.36) ** 2)) * 1.01
                pts.append((rw * s, p[1], p[2]))
            m.loft(c.spine_bone(pts[2][1]), 'glow', pts, [(0.05, 0.05)] * 5, sides=4, steps=1, smooth=False)
    # broken shackles on the legs, snapped chain links dangling
    for side, s in c.SIDES:
        for end, x, y in (('F', 1.15 * bW * s, c.yF), ('B', 1.2 * bW * s, c.yB)):
            z = c.ankZ + 0.45
            ring = [(x + math.cos(TAU * i / 10) * 0.55 * c.T, y - 0.05 + math.sin(TAU * i / 10) * 0.5 * c.T, z) for i in range(11)]
            m.loft(f'Lower{end}{side}', 'iron', ring, [(0.1, 0.13)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
            for li in range(3):
                lz = z - 0.2 - 0.2 * li
                m.box(f'Lower{end}{side}', 'iron', (x + 0.55 * c.T * s, y - 0.05, lz), (0.06, 0.16, 0.2), rot=(0, 0, 90 * (li % 2)), bevel=0.0)
    # the tail: a plume of ghost-fire that trails light
    tip = c.tailEnd
    for i, d in enumerate(((0, 1, 0.3), (0.45, 0.9, 0.2), (-0.45, 0.9, 0.2), (0.2, 0.8, 0.7), (-0.2, 0.8, 0.7))):
        flame(m, 'Tail3', c.add(tip, (0, -0.3, 0)), d, (2.1 - 0.2 * i) * k, 0.85, core=i < 3)
    for t, bone in ((0.45, 'Tail2'), (0.7, 'Tail3')):
        p = c.tail_pt(1.3 + 4.2 * t, 2.35 - 0.8 * t)
        flame(m, bone, p, (0, 0.5, 1), 0.6 * k, 0.35, core=False)
    m.socket('TailFire', 'Tail3', c.add(tip, (0, 0.6, 0.3)))
    m.socket('TailTrail', 'Tail3', c.add(tip, (0, 1.1, 0.4)))


build(dict(
    sides=6,
    kneePlates='bone',
    name='WispWolf',
    palette={
        'body': '#1c1a2a', 'body2': ('#2e2a46', True, True), 'belly': '#2a2440', 'bone': ('#e6dece', False, True),
        'crack': ('#a25cff', False), 'glow': ('#a25cff', False), 'glow2': ('#e8d4ff', False), 'iron': ('#3a3846', False, True),
        'dark': ('#06040a', False), 'nose': ('#0a080e', False), 'fang': ('#f4eee2', False), 'foot': '#1c1a2a',
        'claw': ('#e6dece', False), 'mouth': '#2a0a20', 'tongue': '#a82a5a',
        'eye_dark': ('#06040a', False), 'iris': ('#c88cff', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.25, legT=0.9, bL=1.15, bW=0.95, bH=0.95, girth=0.95, head=1.05, neck=1.0, neckUp=1.5,
              tail=1.2, tailDroop=0.7, eye=0.9),
    neckRadius=0.9,
    gait=dict(stride=1.25),
    head=head, decor=decor,
))
