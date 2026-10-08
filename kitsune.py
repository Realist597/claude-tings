"""Kitsune Kit - Common Mythic fox spirit: golden fur with red shrine markings, tall ears, a twisted
shrine-rope collar with zigzag paper charms and a little bell, and THREE big fluffy tails (each its
own bone chain) tipped with blue foxfire. Faces -Y.
Sockets: Foxfire1-3 (tail-tip flames), Bell."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, standard_eyes, standard_jaw, TAU

TAILS = (('A', 0.0, 0.0), ('B', 0.55, 28.0), ('C', -0.55, -28.0))   # tag, x offset, fan angle


def tail_points(c, fan):
    a = math.radians(fan)
    k = 0.55 + 0.45 * c.grow
    base = c.add(c.hipsHead, (0, 0.2, 0.15))
    pts = [base]
    for i, (dy, dz) in enumerate(((1.1, 0.9), (1.0, 0.75), (0.8, 0.2))):
        prev = pts[-1]
        pts.append((prev[0] + math.sin(a) * dy * k, prev[1] + math.cos(a) * dy * k, prev[2] + dz * k))
    return pts


def bones(c):
    for tag, x, fan in TAILS:
        pts = tail_points(c, fan)
        parent = 'Hips'
        for i in range(3):
            c.m.bone(f'Fox{tag}{i + 1}', pts[i], pts[i + 1], parent)
            parent = f'Fox{tag}{i + 1}'


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    m.box('Head', 'body', H(0, -0.75, 0.1), (1.55 * h, 1.6 * h, 1.3 * h), bevel=0.4 * h, segs=1)
    m.box('Head', 'body', H(0, -1.75, -0.12), (0.8 * h, 1.2 * h, 0.6 * h), bevel=0.2 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.6, 0.7)))
    m.box('Head', 'belly', H(0, -1.65, -0.35), (0.75 * h, 1.05 * h, 0.3 * h), bevel=0.1 * h, taper=dict(axis='y', end=-1, scale=(0.6, 0.8)))
    m.blob('Head', 'nose', H(0, -2.35, -0.05), (0.13 * h, 0.08 * h, 0.1 * h), u=8, v=5)
    for side, s in c.SIDES:
        # spiky cheek ruff
        for k, (dy, dz) in enumerate(((-0.8, -0.3), (-0.5, -0.45), (-1.05, -0.15))):
            m.spike('Head', 'belly', H(0.62 * s, dy, dz), (s, 0.3, -0.25), (0.5 - 0.1 * k) * h, 0.3 * h, 0.12 * h)
        # tall ears with dark insides
        m.spike('Head', 'body', H(0.48 * s, -0.4, 0.55), (0.35 * s, 0.15, 1), (0.9 + 0.5 * g) * h, 0.62 * h, 0.22 * h)
        m.spike('Head', 'ear_in', H(0.48 * s, -0.48, 0.6), (0.35 * s, 0.15, 1), (0.7 + 0.4 * g) * h, 0.4 * h, 0.06 * h)
        # red shrine markings over the eyes and on the cheeks
        # red shrine stripes sweeping back along the cheek, below the eye
        m.box('Head', 'mark', H(0.7 * s, -0.75, -0.08), (0.06 * h, 0.5 * h, 0.08 * h), rot=(-12, 0, 8 * s), bevel=0.0)
    m.box('Head', 'mark', H(0, -1.0, 0.62), (0.12 * h, 0.3 * h, 0.05 * h), bevel=0.0)
    # glowing eyes in dark sockets, angry slanted shrine-mark brows
    for side, s in c.SIDES:
        m.box('Head', 'dark', H(0.72 * s, -1.08, 0.25), (0.12 * h, 0.52 * h, 0.4 * h), rot=(0, 0, 12 * s), bevel=0.03 * h)
        m.box('Head', 'mark', H(0.76 * s, -1.12, 0.66), (0.12 * h, 0.55 * h, 0.09 * h), rot=(20, 0, 12 * s), bevel=0.02 * h)
        # fangs hanging over the lip
        m.spike('Head', 'fang', H(0.24 * s, -2.0, -0.38), (0, -0.15, -1), 0.3 * h, 0.12 * h, snap=False)
    standard_eyes(c, x=0.82, y=-1.08, z=0.24, size=0.34)
    # a gold shrine crest with a red gem between the ears
    m.box('Head', 'gold', H(0, -0.75, 0.75), (0.5 * h, 0.7 * h, 0.22 * h), rot=(-10, 0, 0), bevel=0.05 * h)
    m.box('Head', 'gem', H(0, -1.08, 0.82), (0.24 * h, 0.12 * h, 0.24 * h), rot=(0, 45, 0), bevel=0.03 * h)
    m.spike('Head', 'gold', H(0, -0.55, 0.85), (0, 0.4, 1), (0.4 + 0.3 * g) * h, 0.22 * h, 0.1 * h)
    # slim fox jaw under the snout
    m.box('Head', 'mouth', H(0, -1.7, -0.42), (0.55 * h, 1.0 * h, 0.06 * h), bevel=0.0)
    m.box('Jaw', 'belly', H(0, -1.55, -0.5), (0.6 * h, 1.15 * h, 0.18 * h), bevel=0.06 * h, taper=dict(axis='y', end=-1, scale=(0.6, 0.8)))


def decor(c):
    m, g = c.m, c.grow
    # twisted shrine rope collar with paper charms and a bell
    nc = c.add(c.neckStart, (0, -0.15, 0.1))
    r = 0.95 * max(c.bW, 0.8 * c.h)
    for twist in (0.0, math.pi):
        ring = []
        for i in range(25):
            a = TAU * i / 24
            off = 0.09 * math.sin(a * 6 + twist)
            ring.append((math.cos(a) * (r + off), nc[1] + 0.12 * math.cos(a * 6 + twist), nc[2] + math.sin(a) * (r * 0.85 + off)))
        m.loft('Neck', 'rope', ring, [(0.09, 0.09)] * len(ring), sides=5, steps=1, smooth=False, cap_round=0.0)
    for x in (-0.55, 0.55):
        top = (x * r, nc[1] - 0.6, nc[2] - 0.55)
        lead = [top, (top[0] + 0.12, top[1], top[2] - 0.25), (top[0] - 0.05, top[1], top[2] - 0.45), (top[0] + 0.1, top[1], top[2] - 0.7)]
        trail = [(p[0] + 0.22, p[1], p[2]) for p in lead]
        m.strip('Neck', 'paper', lead, trail, thickness=0.03)
    m.blob('Neck', 'gold', (0, nc[1] - 0.95, nc[2] - 0.75), (0.2, 0.2, 0.2), u=8, v=6)
    m.socket('Bell', 'Neck', (0, nc[1] - 0.95, nc[2] - 0.75))
    # gold shoulder guards edged in red
    for side, s in c.SIDES:
        p = c.body_pt(-1.05, 3.55)
        m.box('Chest', 'gold', (1.0 * c.bW * s, p[1], p[2] - 0.25), (0.7, 0.8, 0.18), rot=(0, 55 * s, 0), bevel=0.05)
        m.box('Chest', 'mark', (1.04 * c.bW * s, p[1] - 0.05, p[2] - 0.22), (0.45, 0.48, 0.18), rot=(0, 55 * s, 0), bevel=0.03)
    # white chest bib
    m.blob('Chest', 'belly', c.body_pt(-1.45, 2.1), (0.95 * c.bW, 0.45, 0.85), u=8, v=6)
    # three big fluffy tails with white tips and blue foxfire
    for i, (tag, x, fan) in enumerate(TAILS):
        pts = tail_points(c, fan)
        bones_ = ['Hips', f'Fox{tag}1', f'Fox{tag}2', f'Fox{tag}3']
        k = 0.55 + 0.45 * g
        m.loft(bones_, 'body', pts, [(0.32, 0.32), (0.62 * k, 0.6 * k), (0.68 * k, 0.66 * k), (0.4 * k, 0.4 * k)], sides=8, steps=3, smooth=False)
        tip = pts[-1]
        m.blob(f'Fox{tag}3', 'belly', tip, (0.42 * k, 0.42 * k, 0.45 * k), u=8, v=6)
        m.blob(f'Fox{tag}3', 'fire', (tip[0], tip[1] + 0.15, tip[2] + 0.35 * k), (0.25 * k, 0.25 * k, 0.35 * k), u=8, v=5)
        m.socket(f'Foxfire{i + 1}', f'Fox{tag}3', (tip[0], tip[1] + 0.15, tip[2] + 0.55 * k))


def pose(c, clip, t, p):
    E = c.E
    for i, (tag, x, fan) in enumerate(TAILS):
        ph = 1.1 * i
        if clip == 'Sleep':
            sw, lift = 25, 10
        elif clip in ('Walk', 'Run'):
            sw, lift = 12 * math.sin(TAU * t + ph), -5
        elif clip == 'Happy':
            sw, lift = 30 * math.sin(TAU * 3 * t + ph), -12
        else:
            sw, lift = 10 * E * math.sin(TAU * t + ph), -3 * math.sin(TAU * t + ph)
        for j in range(3):
            p[f'Fox{tag}{j + 1}'] = ((lift * (1 - 0.2 * j), 0, sw * (0.6 + 0.4 * j)), (0, 0, 0))


build(dict(
    sides=6,
    name='KitsuneKit',
    palette={
        'body': '#ee8a2c', 'dark': ('#1a0e0a', False), 'fang': ('#fbf6ec', False), 'gem': ('#e0302a', False), 'belly': '#fff6ea', 'ear_in': '#5a3424', 'mark': ('#e0302a', False, True), 'nose': ('#2a1a1a', False),
        'rope': ('#e8d6a0', True, True), 'paper': ('#ffffff', False), 'gold': ('#ffcf3a', False, True), 'fire': ('#6ad8ff', False),
        'foot': '#3a2a28', 'claw': ('#f0e8dc', False), 'mouth': '#e48aa2', 'tongue': '#d6405c',
        'eye_dark': ('#121419', False), 'iris': ('#ffb21a', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.05, legT=0.78, bL=0.85, bW=0.78, bH=0.82, girth=0.92, head=1.0, neck=0.9, neckUp=1.7,
              tail=0.25, tailDroop=1.0, eye=1.1),
    neckRadius=0.8,
    gait=dict(stride=1.15),
    bones=bones, head=head, decor=decor, pose=pose,
))
