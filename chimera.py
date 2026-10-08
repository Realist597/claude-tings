"""Chimera - Rare Mythic chimera: a dark lion with a huge layered fire-orange mane whose outer spikes
glow gold at the tips, glowing eyes in dark sockets under bronze brows, big fangs and a spiked bronze
collar; a bone-white goat's head rises from its back (dark outlined curled horns, beard, own neck
bones) and a living snake for a tail with glowing toxic-green bands, eyes and fangs. All three heads
animate. Faces -Y.
Sockets: GoatHorn (glint), SnakeMouth (venom), ManeTop."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, standard_eyes, standard_jaw, TAU
from kit import envelope


def goat_points(c):
    base = c.body_pt(-0.3, 3.75)
    mid = c.add(base, (0.15, 0.1, 0.9 * (0.6 + 0.4 * c.grow)))
    hp = c.add(mid, (0.25, -0.25, 0.8 * (0.6 + 0.4 * c.grow)))
    return base, mid, hp


def bones(c):
    m = c.m
    base, mid, hp = goat_points(c)
    m.bone('GoatNeck', base, mid, 'Chest')
    m.bone('GoatHead', mid, hp, 'GoatNeck')
    tip = c.tailEnd
    m.bone('SnakeHead', tip, c.add(tip, (0, 1.8, 0.7)), 'Tail3')
    m.bone('SnakeJaw', c.add(tip, (0, 0.3, -0.2)), c.add(tip, (0, 1.7, -0.4)), 'SnakeHead')


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # lion head
    m.box('Head', 'body', H(0, -0.75, 0.1), (1.7 * h, 1.7 * h, 1.45 * h), bevel=0.4 * h, segs=1)
    m.box('Head', 'muzzle', H(0, -1.65, -0.2), (1.05 * h, 0.85 * h, 0.75 * h), bevel=0.25 * h, segs=1)
    m.blob('Head', 'nose', H(0, -2.05, 0.05), (0.22 * h, 0.12 * h, 0.14 * h), u=8, v=5)
    for side, s in c.SIDES:
        m.spike('Head', 'fang', H(0.28 * s, -1.95, -0.5), (0, -0.1, -1), 0.5 * h, 0.16 * h, snap=False)
        m.spike('Jaw', 'fang', H(0.32 * s, -1.75, -0.75), (0, -0.1, 1), 0.3 * h, 0.12 * h, snap=False)
        m.blob('Head', 'body', H(0.62 * s, -0.25, 0.68), (0.25 * h, 0.12 * h, 0.25 * h), u=8, v=5)
        # dark eye sockets under heavy bronze brows
        m.box('Head', 'dark', H(0.78 * s, -1.0, 0.3), (0.14 * h, 0.55 * h, 0.42 * h), rot=(0, 0, 10 * s), bevel=0.03 * h)
        m.box('Head', 'bronze', H(0.62 * s, -1.05, 0.68), (0.55 * h, 0.6 * h, 0.16 * h), rot=(18, 0, -20 * s), bevel=0.04 * h)
    standard_eyes(c, x=0.86, y=-1.0, z=0.3, size=0.32)
    # bronze crest plate with a glowing gem on the brow
    m.box('Head', 'bronze', H(0, -0.9, 0.78), (0.5 * h, 0.8 * h, 0.18 * h), rot=(-10, 0, 0), bevel=0.05 * h)
    m.box('Head', 'glow', H(0, -1.2, 0.86), (0.22 * h, 0.12 * h, 0.22 * h), rot=(0, 45, 0), bevel=0.03 * h)
    standard_jaw(c, width=1.0, length=1.3, color='muzzle')


def decor(c):
    m, g, h = c.m, c.grow, c.h
    # huge layered mane: rings of thick spikes around the head and neck, darker on the outside
    k = 0.5 + 0.5 * g
    for ring_i, (dy, r, col) in enumerate(((-0.55, 1.05, 'mane2'), (-0.15, 1.3, 'mane'), (0.3, 1.2, 'mane2'))):
        center = c.add(c.hp, (0, dy, -0.15))
        for i in range(14):
            a = TAU * i / 14 + ring_i * 0.22
            d = (math.cos(a), 0.55, math.sin(a) * 0.95)
            p = (center[0] + math.cos(a) * r * h * 0.85, center[1], center[2] + math.sin(a) * r * h * 0.8)
            ln = (0.9 + 0.3 * (i % 2)) * k * h
            m.spike('Neck' if ring_i < 2 else 'Chest', col, p, d, ln, 0.55 * h, 0.25 * h)
            if ring_i == 1:   # the middle ring's spikes burn gold at the tips
                q = (p[0] + d[0] * ln * 0.7, p[1] + d[1] * ln * 0.7, p[2] + d[2] * ln * 0.7)
                m.spike('Neck', 'glow', q, d, ln * 0.6, 0.32 * h, 0.16 * h)
    # spiked bronze collar under the mane
    nc = c.add(c.neckStart, (0, 0.1, -0.1))
    ring = [(math.cos(TAU * i / 16) * 1.05 * c.bW, nc[1], nc[2] + math.sin(TAU * i / 16) * 0.95 * c.bH) for i in range(17)]
    m.loft('Chest', 'bronze', ring, [(0.16, 0.22)] * len(ring), sides=6, steps=1, smooth=False, cap_round=0.0)
    for i in range(8):
        a = math.pi + math.pi * (i + 0.5) / 8   # spikes round the underside
        m.spike('Chest', 'horn', (math.cos(a) * 1.1 * c.bW, nc[1] - 0.05, nc[2] + math.sin(a) * 1.0 * c.bH),
                (math.cos(a), -0.2, math.sin(a)), 0.4, 0.18, 0.1)
    m.socket('ManeTop', 'Neck', c.add(c.hp, (0, 0.3, 1.4 * h)))
    # the goat: neck rising off the back, head with curled horns and a beard
    base, mid, hp = goat_points(c)
    gh = 0.75 * (0.6 + 0.4 * g)
    m.loft(['Chest', 'GoatNeck', 'GoatHead'], 'goat', [c.add(base, (0, 0, -0.3)), mid, hp], [(0.55, 0.55), (0.42, 0.42), (0.38, 0.38)],
           sides=8, steps=2, smooth=False)
    G = lambda dx, dy, dz: c.add(hp, (dx * gh, dy * gh, dz * gh))
    m.box('GoatHead', 'goat', G(0, -0.6, 0.2), (1.0, 1.5, 0.95), bevel=0.25, segs=1, taper=dict(axis='y', end=-1, scale=(0.65, 0.7)))
    m.blob('GoatHead', 'nose', G(0, -1.45, 0.05), (0.15, 0.08, 0.1), u=8, v=5)
    m.spike('GoatHead', 'beard', G(0, -1.1, -0.35), (0, 0.2, -1), 0.8 * gh, 0.3, 0.15)
    for side, s in c.SIDES:
        m.box('GoatHead', 'dark', G(0.45 * s, -0.75, 0.35), (0.1, 0.4, 0.3), rot=(0, 0, 10 * s), bevel=0.02)
        m.eye('GoatHead', G(0.5 * s, -0.75, 0.35), (0.9 * s, -0.4, 0.2), 0.16, iris='glow2')
        m.spike('GoatHead', 'goat', G(0.5 * s, -0.4, 0.45), (1 * s, 0.3, 0.2), 0.45 * gh, 0.3, 0.1)
        # curled horn: a chain of short segments spiralling back and down
        prev = G(0.3 * s, -0.4, 0.62)
        for j in range(6):
            a = j * 0.75
            d = (0.35 * s, math.cos(a), math.sin(a) * -1.0 + 0.6)
            seg = (0.45 - 0.05 * j) * gh * (0.5 + 0.5 * g)
            m.spike('GoatHead', 'horn', prev, d, seg * 1.6, (0.3 - 0.035 * j) * gh, snap=False)
            prev = (prev[0] + d[0] * seg, prev[1] + d[1] * seg, prev[2] + d[2] * seg)
        if s > 0:
            m.socket('GoatHorn', 'GoatHead', prev)
    # the snake tail: scaled bands down the tail and a fanged snake head on the end
    for t in (0.3, 0.55, 0.8):
        p = c.tail_pt(1.3 + 4.2 * t, 2.35 - 0.8 * t)
        m.blob(c.spine_bone(p[1]), 'snake', p, (0.5 * (1 - 0.4 * t), 0.24, 0.48 * (1 - 0.4 * t)), u=8, v=4)
        m.blob(c.spine_bone(p[1]), 'glow2', p, (0.56 * (1 - 0.4 * t), 0.09, 0.54 * (1 - 0.4 * t)), u=8, v=4)
    tip = c.tailEnd
    S_ = lambda dx, dy, dz: c.add(tip, (dx * 2, dy * 2, dz * 2))   # snake head drawn at double size
    m.box('SnakeHead', 'snake', S_(0, 0.45, 0.2), (1.1, 1.8, 0.84), bevel=0.3, taper=dict(axis='y', end=1, scale=(0.7, 0.7)))
    m.box('SnakeJaw', 'snake2', S_(0, 0.5, -0.02), (0.9, 1.5, 0.28), bevel=0.1, taper=dict(axis='y', end=1, scale=(0.7, 0.8)))
    for side, s in c.SIDES:
        m.eye('SnakeHead', S_(0.27 * s, 0.6, 0.35), (0.9 * s, 0.3, 0.3), 0.2, iris='glow2')
        m.box('SnakeHead', 'glow2', S_(0.25 * s, 0.55, 0.47), (0.25, 0.5, 0.1), rot=(0, 0, -15 * s), bevel=0.03)   # glowing brow ridge
        m.spike('SnakeHead', 'glow2', S_(0.12 * s, 0.82, 0.0), (0, 0.2, -1), 0.5, 0.15, snap=False)
    for k in range(3):   # spines down the snake's head
        m.spike('SnakeHead', 'glow2', S_(0, 0.2 + 0.25 * k, 0.6), (0, 0.6, 1), 0.35 - 0.06 * k, 0.16, 0.06)
    m.socket('SnakeMouth', 'SnakeHead', S_(0, 0.95, 0.05))


def pose(c, clip, t, p):
    E = c.E
    if clip == 'Idle':
        gl, gn, sw, sj = 15 * math.sin(TAU * t + 1), 5 * math.sin(TAU * 2 * t), 25 * math.sin(TAU * t + 2), max(0.0, 30 * math.sin(TAU * 2 * t) - 20)
    elif clip in ('Walk', 'Run'):
        gl, gn, sw, sj = 8 * math.sin(TAU * t), 6 * math.sin(TAU * 2 * t), 18 * math.sin(TAU * t + 2), 5
    elif clip == 'Sleep':
        gl, gn, sw, sj = 30, 25, 40, 0
    else:
        e = envelope(t, 0.2, 0.75)
        gl, gn, sw, sj = 0, -25 * e, 10 * math.sin(TAU * 4 * t), 35 * e
    p['GoatNeck'] = ((gn, 0, gl * 0.5), (0, 0, 0))
    p['GoatHead'] = ((gn * 0.5, 0, gl * 0.6), (0, 0, 0))
    p['SnakeHead'] = ((-10 * E * math.sin(TAU * t), 0, sw), (0, 0, 0))
    p['SnakeJaw'] = ((-sj, 0, 0), (0, 0, 0))


build(dict(
    sides=6,
    kneePlates='bronze',
    name='Chimera',
    palette={
        'body': '#3a2c30', 'belly': '#5c464a', 'muzzle': '#5c464a', 'mane': ('#ff7a1e', True, True), 'mane2': ('#b8321a', True, True),
        'goat': '#e2dacb', 'beard': '#f4efe4', 'horn': ('#2a2224', False, True), 'snake': ('#1d3a26', True, True), 'snake2': '#2f5a36',
        'glow': ('#ffd23a', False), 'glow2': ('#7aff5a', False), 'bronze': ('#d08a3a', False, True), 'dark': ('#100c0e', False),
        'nose': ('#140e10', False), 'fang': ('#f6f0e2', False), 'foot': '#241a1c', 'claw': ('#f0e8dc', False),
        'mouth': '#7a2a3a', 'tongue': '#d6405c', 'eye_dark': ('#121419', False), 'iris': ('#ffb02a', False),
        'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.1, legT=1.1, bL=1.05, bW=0.98, bH=1.0, girth=1.02, head=1.05, neck=0.8, neckUp=1.4,
              tail=1.3, tailDroop=0.5, eye=1.0),
    neckRadius=0.95,
    gait=dict(stride=1.15),
    bones=bones, head=head, decor=decor, pose=pose,
))
