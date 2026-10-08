"""Bristleboar - Common forest boar, chunky style: a barrel of a body, a huge boxy head with an angry
brow, a flat snout, big curved tusks and glowing amber eyes; a mohawk of dark bristle thorns and leaf
blades down the spine, bark armour plates over the shoulders, moss with little red mushrooms on its
back and a leafy tail tuft. Faces -Y."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quadruped import build, standard_jaw


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # big boxy skull, heavy brow, flat snout
    m.box('Head', 'body', H(0, -0.9, 0.05), (2.5 * h, 2.3 * h, 2.0 * h), bevel=0.2 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.86, 0.86)))
    m.box('Head', 'bark', H(0, -1.55, 0.88), (2.45 * h, 0.7 * h, 0.42 * h), rot=(-18, 0, 0), bevel=0.06 * h)
    m.box('Head', 'snout', H(0, -2.15, -0.2), (1.45 * h, 0.7 * h, 1.05 * h), bevel=0.1 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.92, 0.9)))
    m.box('Head', 'snout2', H(0, -2.52, -0.2), (1.2 * h, 0.08 * h, 0.82 * h), bevel=0.02 * h)
    for side, s in c.SIDES:
        m.box('Head', 'dark', H(0.28 * s, -2.56, -0.18), (0.22 * h, 0.06 * h, 0.34 * h), bevel=0.02)   # nostrils
        # glowing eyes in dark sockets under the brow
        m.box('Head', 'dark', H(1.18 * s, -1.25, 0.42), (0.2 * h, 0.6 * h, 0.5 * h), bevel=0.04 * h)
        m.eye('Head', H(1.3 * s, -1.27, 0.42), (1 * s, -0.4, 0.05), 0.46 * h * c.eye)
        # notched ears flopping out
        m.box('Head', 'body', H(1.25 * s, -0.15, 0.95), (0.95 * h, 0.22 * h, 0.75 * h), rot=(20, 0, 35 * s), bevel=0.04 * h)
        m.box('Head', 'snout', H(1.27 * s, -0.24, 0.93), (0.6 * h, 0.06 * h, 0.45 * h), rot=(20, 0, 35 * s), bevel=0.0)
        # big curved tusks from the jaw corners
        base = H(0.62 * s, -1.95, -0.8)
        k = (0.45 + 0.55 * g) * h
        pts = [base, c.add(base, (0.15 * s * k, -0.25 * k, 0.55 * k)), c.add(base, (0.45 * s * k, -0.35 * k, 1.05 * k)),
               c.add(base, (0.8 * s * k, -0.15 * k, 1.35 * k))]
        m.loft('Jaw', 'tusk', pts, [(0.2 * h, 0.2 * h), (0.17 * h, 0.17 * h), (0.11 * h, 0.11 * h), (0.02, 0.02)],
               sides=6, steps=3, smooth=False)
    # teeth along the upper lip
    for k in range(4):
        for side, s in c.SIDES:
            m.box('Head', 'tooth', H(0.7 * s, -0.75 - k * 0.32, -0.66), (0.16 * h, 0.18 * h, 0.24 * h), bevel=0.02)
    standard_jaw(c, width=1.75, length=2.0, color='belly')


def decor(c):
    m, g = c.m, c.grow
    # mohawk of dark bristle thorns and leaf blades from the crown down the spine
    m.spike('Head', 'bristle', c.H(0, -0.45, 1.0), (0, 0.35, 1), 0.85 * g + 0.3, 0.32, 0.12)
    y = -1.7
    i = 0
    while y < 1.4:
        p = c.body_pt(y, 3.72)
        bone = c.spine_bone(p[1])
        k = (0.55 + 0.6 * g) * (1.0 - 0.25 * abs(y + 0.2) / 1.6)
        m.spike(bone, 'bristle', (0, p[1], p[2] - 0.2), (0, 0.45, 1), 1.05 * k, 0.36, 0.14)
        side = 1 if i % 2 else -1
        m.box(bone, 'leaf' if i % 2 else 'leaf2', (0.22 * side, p[1] + 0.1, p[2] + 0.25 * k), (0.1, 0.32, 0.75 * k),
              rot=(25, 0, 20 * side), bevel=0.03)
        y += 0.42
        i += 1
    # bark armour over the shoulders and haunches
    for side, s in c.SIDES:
        for ya, za, w in ((-0.9, 3.55, 1.0), (-0.35, 3.75, 0.9), (0.9, 3.6, 0.9)):
            p = c.body_pt(ya, za)
            m.box(c.spine_bone(p[1]), 'bark', (0.85 * c.bW * s, p[1], p[2]), (0.95 * w, 0.75 * w, 0.22), rot=(10, 32 * s, 0), bevel=0.05)
    # moss patches with little red mushrooms
    for ya, x in ((0.25, 0.55), (-0.55, -0.6), (1.05, -0.35)):
        p = c.body_pt(ya, 3.62)
        bone = c.spine_bone(p[1])
        m.box(bone, 'moss', (x * c.bW, p[1], p[2]), (0.65, 0.55, 0.16), rot=(0, 25 * (1 if x > 0 else -1), 30), bevel=0.04)
        if g > 0.5:
            for k, (dx, dy, sz) in enumerate(((0.12, 0.05, 1.0), (-0.15, -0.12, 0.7))):
                b = (x * c.bW + dx, p[1] + dy, p[2] + 0.1)
                m.box(bone, 'stem', c.add(b, (0, 0, 0.14 * sz)), (0.1 * sz, 0.1 * sz, 0.28 * sz), bevel=0.02)
                m.box(bone, 'cap', c.add(b, (0, 0, 0.32 * sz)), (0.32 * sz, 0.32 * sz, 0.14 * sz), bevel=0.04)
    # leafy tail tuft
    for k, d in enumerate(((0, 0.6, 0.6), (0.5, 0.5, 0.3), (-0.5, 0.5, 0.3))):
        m.spike('Tail3', 'leaf' if k else 'leaf2', c.tailEnd, d, 0.55, 0.22, 0.08)


build(dict(
    name='Bristleboar',
    palette={
        'body': '#8a5c3c', 'belly': '#d6ab78', 'snout': '#d98a7a', 'snout2': '#b8665a', 'bark': ('#4a3122', True, True),
        'bristle': ('#2e1f17', True, True), 'leaf': ('#5fae2e', False, True), 'leaf2': ('#9be04a', False, True),
        'moss': '#86c43a', 'stem': ('#efe6cf', False), 'cap': ('#d8402e', True), 'tusk': ('#f4efe2', False),
        'tooth': ('#fbf7ee', False), 'dark': ('#141010', False), 'foot': '#2e221a', 'claw': ('#e8e0d0', False),
        'mouth': ('#5a1e22', False), 'tongue': '#d6405c', 'eye_dark': ('#120c08', False),
        'iris': ('#ff9a1a', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=0.98, legT=1.2, bL=0.95, bW=1.12, bH=1.1, girth=1.15, head=1.12, neck=0.6, neckUp=0.5,
              tail=0.35, tailDroop=1.6),
    sides=6,
    head=head, decor=decor,
))
