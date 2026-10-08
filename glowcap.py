"""Glowcap Stag - Epic forest deer, chunky style: a dark bark-brown stag with huge branching antlers built
from chunky segments, a glowing mushroom cap on every tip, a mane of outlined leaf shards round the
neck, glowing cyan rune stripes along the flanks, glowing eyes, and a chiselled
muzzle. Faces -Y. In Roblox the caps get light + drifting spore particles (sockets Cap*)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quadruped import build


def norm(v):
    l = math.sqrt(sum(x * x for x in v))
    return tuple(x / l for x in v)


def antler_seg(m, a, b, r0, r1):
    m.loft('Head', 'antler', [a, b], [(r0, r0), (r1, r1)], sides=6, steps=1, smooth=False, cap_round=0.0)


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    m.box('Head', 'body', H(0, -1.05, 0.05), (1.6 * h, 2.5 * h, 1.4 * h), bevel=0.1 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.6, 0.66)))
    m.box('Head', 'muzzle', H(0, -2.0, -0.12), (0.78 * h, 0.9 * h, 0.75 * h), bevel=0.06 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.85, 0.85)))
    m.box('Head', 'nose', H(0, -2.45, 0.0), (0.55 * h, 0.12 * h, 0.35 * h), bevel=0.03 * h)
    m.box('Head', 'mouth', H(0, -1.25, -0.6), (0.95 * h, 1.5 * h, 0.14 * h), bevel=0.0)
    m.box('Jaw', 'muzzle', H(0, -1.3, -0.74), (1.0 * h, 1.75 * h, 0.3 * h), bevel=0.05 * h,
          taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
    m.box('Jaw', 'mouth', H(0, -1.2, -0.6), (0.82 * h, 1.4 * h, 0.1 * h), bevel=0.0)
    for side, s in c.SIDES:
        m.box('Head', 'bark', H(0.42 * s, -0.95, 0.62), (0.7 * h, 1.0 * h, 0.2 * h), rot=(-8, -15 * s, 0), bevel=0.03 * h)   # brow
        m.box('Head', 'dark', H(0.76 * s, -0.95, 0.28), (0.14 * h, 0.5 * h, 0.42 * h), bevel=0.03 * h)
        m.eye('Head', H(0.84 * s, -0.97, 0.28), (1 * s, -0.35, 0.1), 0.38 * h * c.eye)
        # long angled ears with glowing inner edge
        m.box('Head', 'body', H(0.95 * s, -0.25, 0.6), (1.05 * h, 0.2 * h, 0.42 * h), rot=(0, 0, 24 * s), bevel=0.04 * h)
        m.box('Head', 'glow', H(0.97 * s, -0.33, 0.6), (0.75 * h, 0.06 * h, 0.22 * h), rot=(0, 0, 24 * s), bevel=0.0)
        # antlers: chunky segmented beam with branching tines, a glowing cap on every tip
        base = H(0.42 * s, -0.35, 0.68)
        L = (0.6 + 2.2 * g) * h
        beam = [base, c.add(base, (0.35 * s * L, 0.15 * L, 0.45 * L)), c.add(base, (0.55 * s * L, 0.3 * L, 0.85 * L)),
                c.add(base, (0.6 * s * L, 0.55 * L, 1.15 * L))]
        r = [0.24 * h, 0.2 * h, 0.16 * h, 0.12 * h]
        for i in range(3):
            antler_seg(m, beam[i], beam[i + 1], r[i], r[i + 1])
            m.box('Head', 'antler', beam[i + 1], (r[i + 1] * 2.3,) * 3, rot=(20, 30, 10), bevel=0.02)   # knuckle
        tips = [beam[3]]
        if g > 0.4:
            for at, d, k in ((1, (0.1 * s, -0.55, 1.0), 0.42), (2, (0.95 * s, 0.05, 0.55), 0.4), (2, (-0.1 * s, -0.4, 1.0), 0.3)):
                tb = beam[at]
                tip = c.add(tb, tuple(v * L * k for v in norm(d)))
                antler_seg(m, tb, tip, r[at] * 0.85, r[at] * 0.55)
                tips.append(tip)
        for i, tip in enumerate(tips):
            m.socket(f'Cap{side}{i + 1}', 'Head', tip)
            rr = (0.44 if i == 0 else 0.3) * h * (0.55 + 0.45 * g)
            m.loft('Head', 'glow', [c.add(tip, (0, 0, -0.15 * rr)), c.add(tip, (0, 0, 0.3 * rr)), c.add(tip, (0, 0, 0.7 * rr))],
                   [(rr, rr), (rr * 0.85, rr * 0.85), (rr * 0.3, rr * 0.3)], sides=7, steps=1, smooth=False, cap_round=0.0)
            m.loft('Head', 'glow2', [c.add(tip, (0, 0, -0.2 * rr)), c.add(tip, (0, 0, -0.12 * rr))], [(rr * 0.92, rr * 0.92)] * 2,
                   sides=7, steps=1, smooth=False, cap_round=0.0)


def decor(c):
    m, g = c.m, c.grow
    # mane of outlined leaf shards round the neck and shoulders
    for ring, (at, rad, n) in enumerate(((0.35, 0.95, 9), (0.75, 1.15, 11))):
        center = tuple(a + (b - a) * at for a, b in zip(c.neckStart, c.hp))
        for i in range(n):
            a = -1.9 + i * 3.8 / (n - 1)
            p = c.add(center, (math.sin(a) * rad * c.bW, 0.1, math.cos(a) * rad * 0.9))
            L = (0.55 + 0.45 * g) * (1.0 if ring == 0 else 0.8)
            m.box('Neck', 'leaf' if (i + ring) % 2 else 'leaf2', c.add(p, (math.sin(a) * 0.2, 0.25, math.cos(a) * 0.2)),
                  (0.42 * L, 0.12, 0.95 * L), rot=(35, math.degrees(a), 0), bevel=0.02)
    # glowing rune stripes along the flanks
    for side, s in c.SIDES:
        for i, (ya, za, ang) in enumerate(((-0.4, 2.7, 25), (0.2, 2.55, -20), (0.75, 2.75, 30), (1.25, 2.6, -15))):
            p = c.body_pt(ya, za)
            m.box(c.spine_bone(p[1]), 'glow', (1.32 * c.bW * s * (1 - 0.06 * abs(ya)), p[1], p[2]), (0.06, 0.6, 0.12),
                  rot=(ang, 0, 0), bevel=0.0)
        # bark plates on the haunches
        p = c.body_pt(1.1, 3.0)
        m.box('Hips', 'bark', (1.05 * c.bW * s, p[1], p[2]), (0.25, 1.0, 0.75), rot=(15, 22 * s, 0), bevel=0.04)
    m.box('Tail3', 'leaf2', c.tailEnd, (0.4, 0.45, 0.55), rot=(30, 0, 0), bevel=0.04)


build(dict(
    name='GlowcapStag',
    palette={
        'body': '#5a3e2c', 'belly': '#c9a87e', 'muzzle': '#8a6448', 'nose': ('#15101a', False), 'bark': ('#36261b', True, True),
        'antler': ('#e9dcc4', True), 'glow': ('#58f0e0', False), 'glow2': ('#d8fff8', False), 'dark': ('#0c0d12', False),
        'leaf': ('#2f8f5c', False, True), 'leaf2': ('#5fd6a0', False, True), 'moss': '#6fb64a',
        'foot': '#1f1a24', 'claw': ('#2f2a3a', False), 'mouth': ('#4a1a22', False), 'tongue': '#d6405c',
        'eye_dark': ('#081012', False), 'iris': ('#58f0e0', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.6, legT=0.8, bL=0.98, bW=0.84, bH=0.9, girth=0.95, head=0.9, neck=1.9, neckUp=2.6,
              tail=0.3, tailDroop=0.3, eye=1.1),
    neckRadius=0.8,
    gait=dict(stride=1.25),
    sides=6,
    kneePlates='bark',
    head=head, decor=decor,
))
