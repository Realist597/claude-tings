"""Mummy Cat - Epic Haunted monster (Haunted Pumpkin featured egg): a sleek, dark sphinx-like cat
wound in outlined linen bandages - diagonal wraps round the body, legs and tail, loose ends trailing
behind - under a wide Egyptian collar of gold, lapis and turquoise bands with hanging pendants. A
glowing scarab gem set in gold on its brow, piercing green eyes rimmed with black kohl wings, tall
ears ringed in gold, gold anklets and a gold cap on the tail tip. Faces -Y.
Sockets: Gem (scarab glow), Wrap1-4 (dust from the bandage ends)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, TAU


def ring_around(c, center, rw, rh, tilt, n=12):
    """points of an ellipse round the body cross-section at `center`, tipped forward by `tilt` (y per unit z)"""
    pts = []
    for i in range(n + 1):
        a = TAU * i / n
        x, z = math.cos(a) * rw, math.sin(a) * rh
        pts.append((center[0] + x, center[1] + z * tilt, center[2] + z))
    return pts


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # sleek cat head: rounded skull, short muzzle, small chin
    m.box('Head', 'body', H(0, -0.7, 0.15), (1.45 * h, 1.4 * h, 1.2 * h), bevel=0.4 * h, segs=1)
    m.box('Head', 'body', H(0, -1.45, -0.15), (0.85 * h, 0.75 * h, 0.6 * h), bevel=0.2 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.75, 0.75)))
    m.box('Jaw', 'body2', H(0, -1.3, -0.5), (0.7 * h, 0.7 * h, 0.2 * h), bevel=0.06 * h, taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
    m.box('Head', 'mouth', H(0, -1.4, -0.4), (0.6 * h, 0.6 * h, 0.06 * h), bevel=0.0)
    m.blob('Head', 'nose', H(0, -1.82, 0.0), (0.12 * h, 0.07 * h, 0.08 * h), u=6, v=4)
    for side, s in c.SIDES:
        m.spike('Head', 'fang', H(0.16 * s, -1.68, -0.38), (0, -0.1, -1), 0.24 * h, 0.08 * h, snap=False)
        # piercing green eyes rimmed with black kohl, the liner flicked out into a wing
        m.box('Head', 'kohl', H(0.48 * s, -1.08, 0.3), (0.12 * h, 0.5 * h, 0.32 * h), rot=(0, 0, 14 * s), bevel=0.02 * h)
        m.box('Head', 'kohl', H(0.7 * s, -0.85, 0.22), (0.07 * h, 0.4 * h, 0.06 * h), rot=(0, -18 * s, 32 * s), bevel=0.0)
        m.eye('Head', H(0.53 * s, -1.1, 0.3), (0.8 * s, -0.6, 0.15), 0.25 * h * c.eye)
        m.box('Head', 'body2', H(0.45 * s, -1.12, 0.55), (0.42 * h, 0.4 * h, 0.08 * h), rot=(12, 0, -22 * s), bevel=0.02 * h)
        # tall ears, dark inside, ringed with gold hoops
        e0 = H(0.48 * s, -0.4, 0.62)
        m.spike('Head', 'body', e0, (0.3 * s, 0.1, 1), (1.25 + 0.5 * g) * h, 0.62 * h, 0.16 * h)
        m.spike('Head', 'ear_in', c.add(e0, (0, -0.07, 0.04)), (0.3 * s, 0.1, 1), (0.78 + 0.3 * g) * h, 0.36 * h, 0.05 * h, snap=False)
        for k in range(2):
            ring = [c.add(e0, (0.06 * s + math.cos(TAU * i / 8) * 0.2 * h, math.sin(TAU * i / 8) * 0.12 * h, (0.25 + 0.18 * k) * h)) for i in range(9)]
            m.loft('Head', 'gold', ring, [(0.03 * h, 0.03 * h)] * 9, sides=4, steps=1, smooth=False, cap_round=0.0)
        # whisker cheek tufts of bandage
        m.spike('Head', 'linen', H(0.62 * s, -1.25, -0.12), (s, -0.2, -0.3), 0.4 * h, 0.12 * h, 0.04 * h)
    # pharaoh's diadem: a gold band round the brow with a rearing cobra (the uraeus) at the front,
    # its hood flared and eyes glowing
    diadem = [H(math.cos(TAU * i / 14) * 0.74, -0.72 + math.sin(TAU * i / 14) * 0.72, 0.52) for i in range(15)]
    m.loft('Head', 'gold', diadem, [(0.06 * h, 0.1 * h)] * 15, sides=4, steps=1, smooth=False, cap_round=0.0)
    for i in range(14):   # lapis inlays round the band
        if i % 2 == 0:
            a = TAU * i / 14
            m.box('Head', 'lapis', H(math.cos(a) * 0.79, -0.72 + math.sin(a) * 0.77, 0.52), (0.08 * h, 0.08 * h, 0.12 * h), rot=(0, 0, math.degrees(a)), bevel=0.0)
    cobra = [H(0, -1.38, 0.5), H(0, -1.48, 0.72), H(0, -1.4, 0.95), H(0, -1.5, 1.12)]
    m.loft('Head', 'gold', cobra, [(0.08 * h, 0.08 * h), (0.07 * h, 0.07 * h), (0.07 * h, 0.07 * h), (0.09 * h, 0.08 * h)], sides=6, steps=2, smooth=False)
    m.box('Head', 'gold', H(0, -1.44, 0.98), (0.42 * h, 0.06 * h, 0.4 * h), bevel=0.02 * h, taper=dict(axis='z', end=1, scale=(0.55, 1)))   # flared hood
    m.box('Head', 'lapis', H(0, -1.48, 0.98), (0.26 * h, 0.04 * h, 0.26 * h), bevel=0.0, taper=dict(axis='z', end=1, scale=(0.5, 1)))
    m.box('Head', 'gold', H(0, -1.62, 1.15), (0.12 * h, 0.2 * h, 0.09 * h), bevel=0.02 * h)   # the cobra's head
    for side, s in c.SIDES:
        m.blob('Head', 'glow', H(0.05 * s, -1.7, 1.18), (0.03 * h, 0.03 * h, 0.03 * h), u=5, v=4)
    m.socket('Gem', 'Head', H(0, -1.6, 0.98))
    # striped lapis-and-gold lappets hanging from behind the ears down onto the chest
    for side, s in c.SIDES:
        for k in range(5):
            col = 'lapis' if k % 2 == 0 else 'gold'
            m.box('Neck', col, H(0.66 * s, -0.55 - 0.08 * k, 0.15 - 0.32 * k), (0.12 * h, 0.42 * h, 0.3 * h),
                  rot=(-15, 0, 8 * s), bevel=0.02 * h)
        m.box('Neck', 'gold', H(0.66 * s, -0.95, -1.5), (0.14 * h, 0.44 * h, 0.08 * h), rot=(-15, 0, 8 * s), bevel=0.02 * h)
    # a bandage wrapped across the top of the head
    band = [H(math.cos(TAU * i / 10) * 0.68, -0.45 + math.sin(TAU * i / 10) * 0.15, 0.1 + math.sin(TAU * i / 10) * 0.6) for i in range(11)]
    m.loft('Head', 'linen', band, [(0.1 * h, 0.05 * h)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)


def decor(c):
    m, g, bW, bH = c.m, c.grow, c.bW, c.bH
    gi = c.spec['body']['girth']
    # diagonal bandage wraps round the body, each with a loose end trailing behind
    k = 0
    for ya, tilt in ((-1.0, 0.35), (-0.35, -0.3), (0.3, 0.32), (0.95, -0.28)):
        ctr = c.body_pt(ya, 2.45)
        rw, rh = 1.62 * bW * gi * 1.03, 1.3 * bH * gi * 1.03
        pts = ring_around(c, ctr, rw, rh, tilt, 14)
        m.loft(c.spine_bone(ctr[1]), 'linen', pts, [(0.2, 0.06)] * len(pts), sides=4, steps=1, smooth=False, cap_round=0.0)
        k += 1
        top = pts[4]
        end = c.add(top, (0.25 * (1 if k % 2 else -1), 0.7, -0.35))
        m.strip(c.spine_bone(ctr[1]), 'linen', [top, end, c.add(end, (0, 0.4, -0.4))],
                [c.add(top, (0, 0.18, 0)), c.add(end, (0, 0.16, 0.05)), c.add(end, (0, 0.5, -0.3))], thickness=0.04)
        m.socket(f'Wrap{k}', c.spine_bone(ctr[1]), end)
    # the Egyptian collar: wide layered bands of gold, lapis and turquoise with pendants
    nc = c.add(c.neckStart, (0, 0.1, -0.1))
    for layer, (col, r, dz) in enumerate((('gold', 1.16, 0.15), ('lapis', 1.28, 0.0), ('turq', 1.38, -0.16), ('gold', 1.46, -0.3))):
        pts = []
        for i in range(17):
            a = math.pi + math.pi * i / 16          # the front half, drooping in a bib
            x = math.cos(a) * r * bW
            dip = (1 - abs(math.cos(a))) * 0.35
            pts.append((x, nc[1] - 0.15 + math.sin(a) * 0.25, nc[2] + dz - dip - 0.15 * layer * (1 - abs(math.cos(a)))))
        m.loft('Chest', col, pts, [(0.1, 0.06)] * len(pts), sides=4, steps=1, smooth=False, cap_round=0.0)
    for i in range(7):
        a = math.pi + math.pi * (i + 0.5) / 7
        x = math.cos(a) * 1.46 * bW
        p = (x, nc[1] - 0.15 + math.sin(a) * 0.25, nc[2] - 0.3 - (1 - abs(math.cos(a))) * 0.8)
        m.spike('Chest', 'gold', p, (0, -0.15, -1), 0.3, 0.14, 0.06, snap=False)
        m.blob('Chest', 'turq' if i % 2 else 'lapis', c.add(p, (0, -0.02, -0.25)), (0.07, 0.04, 0.07), u=6, v=4)
    # bandaged legs with gold anklets
    for side, s in c.SIDES:
        for end, x, y in (('F', 1.15 * bW * s, c.yF), ('B', 1.2 * bW * s, c.yB)):
            for j, z in enumerate((c.kneeZ + 0.25, c.kneeZ - 0.35)):
                # a slanted wrap round the leg
                ring = [(x + math.cos(TAU * i / 10) * 0.56 * c.T, y + (0.15 if end == 'F' else -0.25) + math.sin(TAU * i / 10) * 0.5 * c.T,
                         z + math.cos(TAU * i / 10) * 0.12 * (1 if j else -1)) for i in range(11)]
                m.loft(f'Upper{end}{side}' if j == 0 else f'Lower{end}{side}', 'linen', ring, [(0.14, 0.05)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
            ank = [(x + math.cos(TAU * i / 10) * 0.52 * c.T, y - 0.05 + math.sin(TAU * i / 10) * 0.48 * c.T, c.ankZ + 0.25) for i in range(11)]
            m.loft(f'Lower{end}{side}', 'gold', ank, [(0.08, 0.1)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
    # a gold ankh hanging from the middle of the collar
    ak = (0, nc[1] - 0.45, nc[2] - 1.05)
    loop = [(math.cos(TAU * i / 10) * 0.13, ak[1], ak[2] + 0.22 + math.sin(TAU * i / 10) * 0.17) for i in range(11)]
    m.loft('Chest', 'gold', loop, [(0.045, 0.045)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
    m.box('Chest', 'gold', (0, ak[1], ak[2]), (0.36, 0.07, 0.07), bevel=0.0)
    m.box('Chest', 'gold', (0, ak[1], ak[2] - 0.18), (0.08, 0.07, 0.42), bevel=0.0)
    m.blob('Chest', 'glow', (0, ak[1] - 0.04, ak[2]), (0.05, 0.03, 0.05), u=5, v=4)
    # glowing green hieroglyph runes along the bandages on the flanks
    for side, s in c.SIDES:
        for j, ya in enumerate((-0.7, -0.1, 0.5)):
            p = c.body_pt(ya, 2.55)
            x = 1.62 * bW * gi * 1.04 * s
            bone = c.spine_bone(p[1])
            m.box(bone, 'linen', (x, p[1], p[2]), (0.06, 0.55, 0.42), bevel=0.02)
            m.box(bone, 'glow', (x * 1.02, p[1] - 0.12, p[2] + 0.06), (0.05, 0.05, 0.22), bevel=0.0)                # a staff
            m.box(bone, 'glow', (x * 1.02, p[1] + 0.06, p[2] + 0.1), (0.05, 0.16, 0.05), bevel=0.0)                 # a bar
            m.box(bone, 'glow', (x * 1.02, p[1] + 0.12, p[2] - 0.08), (0.05, 0.1, 0.1), rot=(45, 0, 0), bevel=0.0)  # an eye
    # tail: bandage rings along it and a gold cap on the tip
    for t, bone in ((0.25, 'Tail1'), (0.5, 'Tail2'), (0.75, 'Tail3')):
        p = c.tail_pt(1.3 + 4.2 * t, 2.35 - 0.8 * t)
        r = 0.55 * (1 - 0.55 * t)
        ring = [(math.cos(TAU * i / 8) * r, p[1] + math.cos(TAU * i / 8) * 0.12, p[2] + math.sin(TAU * i / 8) * r) for i in range(9)]
        m.loft(bone, 'linen', ring, [(0.1, 0.04)] * 9, sides=4, steps=1, smooth=False, cap_round=0.0)
    m.loft('Tail3', 'gold', [c.add(c.tailEnd, (0, -0.2, 0)), c.add(c.tailEnd, (0, 0.25, 0.05))], [(0.18, 0.18), (0.05, 0.05)], sides=6, steps=1, smooth=False)
    m.spike('Tail3', 'glow', c.add(c.tailEnd, (0, 0.2, 0.05)), (0, 1, 0.3), 0.3, 0.12, snap=False)


build(dict(
    sides=6,
    name='MummyCat',
    palette={
        'body': '#45405c', 'body2': ('#6a6288', True, True), 'belly': '#7a7090', 'linen': ('#e6dabc', True, True),
        'gold': ('#ffcf3a', False, True), 'lapis': ('#2a4ac0', False, True), 'turq': ('#3ad0c4', False, True),
        'kohl': ('#08060a', False), 'glow': ('#7aff8a', False), 'ear_in': '#1a1420', 'nose': ('#140e14', False),
        'fang': ('#f4eee2', False), 'foot': '#45405c', 'claw': ('#e6dabc', False), 'mouth': '#3a1420', 'tongue': '#c8405a',
        'eye_dark': ('#08060a', False), 'iris': ('#7aff8a', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.3, legT=0.6, bL=0.92, bW=0.7, bH=0.8, girth=0.78, head=0.9, neck=1.1, neckUp=1.9,
              tail=1.3, tailDroop=-0.55, eye=1.15),
    neckRadius=0.8,
    gait=dict(stride=1.2),
    head=head, decor=decor,
))
