"""Mosshell - Rare forest tortoise, chunky style: a dome of thick outlined hexagonal shell plates with a
spiked bark rim and creeping moss, a grove of big mushrooms with glowing spots on top, a blocky
snapping-turtle head with a hooked beak, angry brow and glowing teal eyes, and plated pillar legs.
Faces -Y. Sockets: Shroom1..n (mushroom caps, spores)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quadruped import build


def head(c):
    m, H, h = c.m, c.H, c.h
    m.box('Head', 'body', H(0, -0.75, 0.0), (1.55 * h, 1.8 * h, 1.3 * h), bevel=0.12 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.85, 0.82)))
    for side, s in c.SIDES:
        m.box('Head', 'scute', H(0.4 * s, -0.95, 0.62), (0.7 * h, 1.05 * h, 0.2 * h), rot=(-10, -16 * s, 0), bevel=0.03 * h)   # brow
        m.box('Head', 'dark', H(0.74 * s, -0.95, 0.25), (0.14 * h, 0.5 * h, 0.42 * h), bevel=0.03 * h)
        m.eye('Head', H(0.82 * s, -0.97, 0.25), (1 * s, -0.35, 0.1), 0.38 * h * c.eye)
        m.box('Head', 'scute', H(0.8 * s, -0.25, -0.1), (0.16 * h, 0.8 * h, 0.75 * h), rot=(0, 10 * s, 0), bevel=0.03 * h)   # cheek
    # hooked beak, top and bottom
    m.box('Head', 'beak', H(0, -1.65, -0.18), (1.05 * h, 0.75 * h, 0.75 * h), bevel=0.06 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.6, 0.65), offset=(0, -0.15 * h)))
    m.box('Head', 'mouth', H(0, -1.0, -0.52), (1.15 * h, 1.3 * h, 0.12 * h), bevel=0.0)
    m.box('Jaw', 'beak', H(0, -1.05, -0.72), (1.2 * h, 1.5 * h, 0.32 * h), bevel=0.05 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.68, 0.8)))
    m.box('Jaw', 'mouth', H(0, -0.95, -0.57), (1.0 * h, 1.2 * h, 0.1 * h), bevel=0.0)
    for side, s in c.SIDES:
        m.box('Head', 'dark', H(0.16 * s, -1.95, 0.08), (0.1 * h, 0.06 * h, 0.08 * h), bevel=0.0)


def decor(c):
    m, g, bL, bW, bH = c.m, c.grow, c.bL, c.bW, c.bH
    top = c.body_pt(0.2, 2.45)
    A, B, C = 1.95 * bW, 2.35 * bL, 1.6 * bH
    BONES = ['Hips', 'Chest']
    m.blob(BONES, 'shell', c.add(top, (0, 0, -0.1 * bH)), (A, B, C), u=10, v=7, smooth=False)

    def surf(dx, dy):
        """point on the dome and its outward normal, for shell-relative offsets (dx, dy)"""
        q = max(1 - (dx * bW / A) ** 2 - (dy * bL / B) ** 2, 0.02)
        z = C * math.sqrt(q)
        p = c.add(top, (dx * bW, dy * bL, -0.1 * bH + z))
        n = (dx * bW / A ** 2, dy * bL / B ** 2, z / C ** 2)
        k = math.sqrt(sum(v * v for v in n))
        return p, tuple(v / k for v in n)

    # thick hexagonal plates tiling the dome (centre, then two rings)
    tiles = [(0, 0, 0.62)]
    tiles += [(0.95 * math.cos(a), 1.15 * math.sin(a), 0.55) for a in [i * math.tau / 6 + 0.26 for i in range(6)]]
    tiles += [(1.6 * math.cos(a), 1.9 * math.sin(a), 0.45) for a in [i * math.tau / 11 for i in range(11)]]
    for dx, dy, r in tiles:
        p, n = surf(dx, dy)
        m.loft(BONES, 'scute', [c.add(p, tuple(-v * 0.1 for v in n)), c.add(p, tuple(v * 0.22 for v in n))],
               [(r * bW, r * bW), (r * 0.86 * bW, r * 0.86 * bW)], sides=6, steps=1, smooth=False)
    # spiked bark rim round the bottom of the shell
    m.blob(BONES, 'rim', c.add(top, (0, 0, -0.3 * bH)), (A * 1.06, B * 1.06, 0.32 * bH), u=12, v=4, smooth=False)
    if g > 0.4:
        for i in range(12):
            a = i * math.tau / 12
            p = c.add(top, (math.cos(a) * A * 1.06, math.sin(a) * B * 1.06, -0.3 * bH))
            m.spike(BONES, 'horn', p, (math.cos(a), math.sin(a), -0.15), 0.45 * g, 0.24, 0.24)
    # creeping moss
    for dx, dy in ((-0.7, -0.8), (0.8, 0.9), (0.6, -1.0), (-0.6, 1.1), (1.2, -0.2)):
        p, n = surf(dx, dy)
        m.loft(BONES, 'moss', [p, c.add(p, tuple(v * 0.3 for v in n))], [(0.5 * bW, 0.45 * bW), (0.42 * bW, 0.38 * bW)],
               sides=7, steps=1, smooth=False)
    # a grove of big mushrooms with glowing spots
    shrooms = [(0.3, -0.35, 1.15), (-0.6, 0.45, 0.9), (0.35, 1.05, 0.75), (-0.2, -1.1, 0.65)] if g > 0.5 else [(0.2, -0.1, 0.8)]
    for i, (dx, dy, k) in enumerate(shrooms):
        k *= 0.45 + 0.55 * g
        p, n = surf(dx, dy)
        base = c.add(p, tuple(v * 0.15 for v in n))
        m.loft(BONES, 'stem', [base, c.add(base, (0, 0, 0.85 * k))], [(0.2 * k, 0.2 * k), (0.16 * k, 0.16 * k)], sides=6, steps=1, smooth=False)
        cap = c.add(base, (0, 0, 0.9 * k))
        m.loft(BONES, 'cap', [c.add(cap, (0, 0, -0.08 * k)), c.add(cap, (0, 0, 0.18 * k)), c.add(cap, (0, 0, 0.42 * k))],
               [(0.7 * k, 0.7 * k), (0.62 * k, 0.62 * k), (0.22 * k, 0.22 * k)], sides=8, steps=1, smooth=False, cap_round=0.0)
        m.loft(BONES, 'gill', [c.add(cap, (0, 0, -0.1 * k)), c.add(cap, (0, 0, -0.06 * k))], [(0.66 * k, 0.66 * k)] * 2,
               sides=8, steps=1, smooth=False, cap_round=0.0)
        for a in range(5):
            ang = a * math.tau / 5 + 0.4
            m.box(BONES, 'glow', c.add(cap, (math.cos(ang) * 0.42 * k, math.sin(ang) * 0.42 * k, 0.3 * k)),
                  (0.15 * k, 0.15 * k, 0.08 * k), rot=(0, 0, math.degrees(ang)), bevel=0.02)
        m.socket(f'Shroom{i + 1}', 'Hips', c.add(cap, (0, 0, 0.5 * k)))


build(dict(
    name='Mosshell',
    palette={
        'body': '#7a9a52', 'belly': '#d8cf9a', 'shell': '#4a3624', 'scute': ('#a07a42', True, True), 'rim': ('#5a3e26', True, True),
        'moss': '#86c43a', 'horn': ('#efe6cf', False), 'cap': ('#d8402e', True, True), 'gill': ('#f2dfc0', False),
        'glow': ('#b8fff0', False), 'stem': ('#efe6cf', True), 'beak': ('#cdb58a', True, True), 'dark': ('#10140c', False),
        'foot': '#3e4a2a', 'claw': ('#e8e0d0', False), 'mouth': ('#5a1e22', False), 'tongue': '#d6405c',
        'eye_dark': ('#0d100a', False), 'iris': ('#3fffd0', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=0.7, legT=1.35, bL=0.9, bW=1.08, bH=0.85, girth=0.9, head=0.9, neck=1.2, neckUp=0.4,
              tail=0.25, tailDroop=1.5, eye=1.1),
    stages={'Child': dict(head=1.35), 'Teen': dict(head=1.05)},
    gait=dict(stride=0.8),
    sides=6,
    kneePlates='scute',
    head=head, decor=decor,
))
