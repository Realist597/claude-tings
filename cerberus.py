"""Cerberus - Epic Underworld hellhound with THREE heads, each on its own neck with its own jaw:
horned skulls, glowing red eyes, fangs, pointed ears and flaming manes. Spiked iron collars joined by
hanging chains, spiked armour plates down the back, glowing lava cracks over a charcoal hide and a
flaming tail. The side heads move on their own (look around, snap, roar together). Faces -Y.
Sockets: Fire{L,C,R}1-2 (mane flames), Mouth{L,C,R} (fire breath), TailFlame, Lava1-4 (embers)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from mathutils import Vector, Matrix
from quadruped import build, TAU
from kit import envelope

SIDE_YAW = 40   # degrees the side heads turn outward


def rz(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), v[2])


def heads(c):
    """(tag, neck bone, head bone, jaw bone, neck start, head point, yaw) for the three heads"""
    out = [('C', 'Neck', 'Head', 'Jaw', c.neckStart, c.hp, 0.0)]
    for side, s in c.SIDES:
        ns = c.add(c.neckStart, (1.1 * s * c.bW, 0.35, -0.2))
        hp = c.add(ns, rz((0, -0.95 * c.st['neck'], 0.85 * c.st['neck']), SIDE_YAW * s))
        hp = c.add(hp, (0.75 * s, 0, 0))
        out.append((side, f'Neck{side}', f'Head{side}', f'Jaw{side}', ns, hp, SIDE_YAW * s))
    return out


def bones(c):
    m = c.m
    for tag, neck, head, jaw, ns, hp, yaw in heads(c)[1:]:
        h = c.h * 0.92
        P = lambda dx, dy, dz: c.add(hp, rz((dx * h, dy * h, dz * h), yaw))
        m.bone(neck, ns, hp, 'Chest')
        m.bone(head, hp, P(0, -2.1, -0.05), neck)
        m.bone(jaw, P(0, -0.3, -0.55), P(0, -1.8, -0.7), head)


def dog_head(c, head, jaw, hp, yaw, h, tag):
    m, g = c.m, c.grow
    P = lambda dx, dy, dz: c.add(hp, rz((dx * h, dy * h, dz * h), yaw))
    D = lambda dx, dy, dz: rz((dx, dy, dz), yaw)
    # skull, brow and long tapering snout
    m.box(head, 'body', P(0, -0.75, 0.1), (1.55 * h, 1.85 * h, 1.3 * h), rot=(0, 0, yaw), bevel=0.32 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.82, 0.85)))
    m.box(head, 'body', P(0, -1.85, -0.12), (0.95 * h, 1.25 * h, 0.72 * h), rot=(0, 0, yaw), bevel=0.18 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.72, 0.75)))
    m.box(head, 'body2', P(0, -0.95, 0.66), (1.35 * h, 0.35 * h, 0.22 * h), rot=(-10, 0, yaw), bevel=0.08 * h)
    m.blob(head, 'nose', P(0, -2.48, 0.05), (0.24 * h, 0.14 * h, 0.16 * h), u=8, v=5)
    m.box(head, 'mouth', P(0, -1.6, -0.48), (0.82 * h, 1.6 * h, 0.12 * h), rot=(0, 0, yaw), bevel=0.0)
    # snarling jaw with fangs top and bottom
    m.box(jaw, 'body2', P(0, -1.5, -0.66), (0.86 * h, 1.7 * h, 0.3 * h), rot=(0, 0, yaw), bevel=0.08 * h,
          taper=dict(axis='y', end=-1, scale=(0.7, 0.8)))
    m.box(jaw, 'tongue', P(0, -1.5, -0.5), (0.4 * h, 1.1 * h, 0.08 * h), rot=(0, 0, yaw), bevel=0.03 * h)
    for side, s in c.SIDES:
        m.spike(head, 'fang', P(0.3 * s, -2.15, -0.5), D(0, -0.15, -1), 0.42 * h, 0.14 * h, snap=False)
        m.spike(jaw, 'fang', P(0.28 * s, -2.0, -0.6), D(0, -0.1, 1), 0.3 * h, 0.12 * h, snap=False)
        for k in range(3):
            m.spike(head, 'fang', P(0.36 * s, -1.75 + 0.3 * k, -0.5), D(0, 0, -1), 0.16 * h, 0.08 * h, snap=False)
        # glowing red eyes under a heavy brow
        m.eye(head, P(0.56 * s, -1.2, 0.3), D(0.8 * s, -0.6, 0.15), 0.26 * h * c.eye)
        # pointed ears and back-swept horns
        m.spike(head, 'body2', P(0.55 * s, -0.25, 0.6), D(0.45 * s, 0.55, 1), (0.55 + 0.3 * g) * h, 0.38 * h, 0.14 * h)
        L = (0.4 + 1.1 * g) * h
        base = P(0.4 * s, -0.75, 0.68)
        d1 = Vector(D(0.25 * s, 0.75, 0.65)).normalized()
        m.spike(head, 'horn', base, tuple(d1), L, 0.26 * h, snap=False)
        tip = tuple(Vector(base) + d1 * L * 0.85)
        m.spike(head, 'horn', tip, D(0.1 * s, 1.0, -0.15), 0.45 * L, 0.15 * h, snap=False)
    m.socket(f'Mouth{tag}', head, P(0, -2.55, -0.35))


def neck_ring(c, center, axis, r, bone, n=12):
    """points of a ring of radius r around `axis` at `center`"""
    a = Vector(axis).normalized()
    ref = Vector((1, 0, 0)) if abs(a.x) < 0.9 else Vector((0, 1, 0))
    u = a.cross(ref).normalized()
    v = a.cross(u).normalized()
    return [tuple(Vector(center) + (u * math.cos(TAU * i / n) + v * math.sin(TAU * i / n)) * r) for i in range(n + 1)], u, v


def head(c):
    for tag, neck, head_b, jaw, ns, hp, yaw in heads(c):
        dog_head(c, head_b, jaw, hp, yaw, c.h * (1.0 if tag == 'C' else 0.92), tag)


def decor(c):
    m, g, h = c.m, c.grow, c.h
    collars = []
    for tag, neck, head_b, jaw, ns, hp, yaw in heads(c):
        if tag != 'C':
            # side necks (the centre one is part of the body loft)
            mid = tuple((a + b) / 2 for a, b in zip(ns, hp))
            m.loft(['Chest', neck, head_b], 'body', [c.add(ns, (0, 0.3, -0.1)), mid, c.add(hp, (0, 0.15, -0.05))],
                   [(0.95 * c.bW, 0.95 * c.bH), (0.72 * h, 0.72 * h), (0.68 * h, 0.66 * h)], sides=8, steps=2, smooth=False)
        # spiked iron collar a third of the way up each neck
        axis = tuple(b - a for a, b in zip(ns, hp))
        center = tuple(a + 0.35 * d for a, d in zip(ns, axis))
        r = 0.86 * h if tag != 'C' else 0.95 * max(c.bW, 0.8 * h)
        ring, u, v = neck_ring(c, center, axis, r, neck)
        m.loft(neck, 'iron', ring, [(0.18, 0.18)] * len(ring), sides=6, steps=1, smooth=False, cap_round=0.0)
        for i in range(0, 12, 2):
            ang = TAU * i / 12
            d = u * math.cos(ang) + v * math.sin(ang)
            m.spike(neck, 'spike', tuple(Vector(center) + d * (r + 0.1)), tuple(d), 0.45 * (0.6 + 0.4 * g), 0.18, snap=False)
        collars.append((tag, neck, center, r))
        # flaming mane along the top of the neck
        for k, t in enumerate((0.3, 0.6, 0.85)):
            p = tuple(a + t * d for a, d in zip(ns, axis))
            top = c.add(p, (0, 0.25, 0.55 * h))
            m.spike(neck, 'flame' if k % 2 == 0 else 'flame2', top, (0, 0.6, 1), (0.5 + 0.45 * g) * (1.1 - 0.25 * k), 0.32, 0.14)
            if k < 2:
                m.socket(f'Fire{tag}{k + 1}', neck, c.add(top, (0, 0.3, 0.5)))
    # hanging chains between the collars (side collar -> centre collar)
    cC = next(x for x in collars if x[0] == 'C')
    for tag, neck, center, r in collars:
        if tag == 'C':
            continue
        a = Vector(center) + Vector((0, -0.2, -r * 0.7))
        b = Vector(cC[2]) + Vector((0, -0.2, -cC[3] * 0.7))
        links = 7
        for i in range(links):
            t = (i + 0.5) / links
            p = a.lerp(b, t) + Vector((0, 0, -0.55 * math.sin(math.pi * t)))
            ring, _, _ = neck_ring(c, tuple(p), (1, 0, 0) if i % 2 else (0, 0, 1), 0.13, 'Chest', n=6)
            m.loft(['Chest', neck], 'iron', ring, [(0.045, 0.045)] * len(ring), sides=4, steps=1, smooth=False, cap_round=0.0)
    # spiked iron armour plates down the spine
    for i, ya in enumerate((-0.9, 0.0, 0.9)):
        p = c.body_pt(ya, 3.7)
        bone = c.spine_bone(p[1])
        m.box(bone, 'iron', (0, p[1], p[2] - 0.2), (1.6 * c.bW, 0.8, 0.28), rot=(8, 0, 0), bevel=0.1, segs=1)
        for x in (-0.45, 0.0, 0.45):
            m.spike(bone, 'spike', (x * c.bW, p[1], p[2] - 0.05), (x * 0.5, 0.3, 1), (0.45 + 0.35 * g) * (1.2 if x == 0 else 0.8), 0.22, snap=False)
    # glowing lava cracks over the hide (zigzags on both flanks), sitting on the body's surface
    def surface_x(ya, za):
        # body loft radii (quadruped.py body_pts) at this point along the body
        keys = ((-1.3, 1.36, 1.18), (-0.3, 1.66, 1.36), (0.9, 1.62, 1.36), (2.1, 1.12, 1.0))
        for (y0, w0, h0), (y1, w1, h1) in zip(keys, keys[1:]):
            if ya <= y1:
                f = max(0.0, min(1.0, (ya - y0) / (y1 - y0)))
                rw, rh = w0 + (w1 - w0) * f, h0 + (h1 - h0) * f
                break
        else:
            rw, rh = keys[-1][1], keys[-1][2]
        g_ = c.spec['body'].get('girth', 1)
        rw, rh = rw * c.bW * g_, rh * c.bH * g_
        dz = (za - 2.45) * c.bH
        return rw * math.sqrt(max(0.05, 1 - (dz / rh) ** 2)) * 1.01
    k = 0
    for side, s in c.SIDES:
        for ya0, za0 in ((-0.7, 2.55), (0.2, 2.2), (0.9, 2.85)):
            pts = []
            for j in range(5):
                ya = ya0 + j * 0.26
                za = za0 + (0.2 if j % 2 else -0.14)
                p = c.body_pt(ya, za)
                pts.append((s * surface_x(ya, za), p[1], p[2]))
            m.loft(c.spine_bone(pts[2][1]), 'lava', pts, [(0.13, 0.13)] * len(pts), sides=4, steps=1, smooth=False)
            m.loft(c.spine_bone(pts[2][1]), 'flame2', [(x * 1.04, y, z) for x, y, z in pts], [(0.06, 0.06)] * len(pts), sides=4, steps=1, smooth=False)
            if k < 4:
                k += 1
                m.socket(f'Lava{k}', c.spine_bone(pts[2][1]), pts[2])
    # flaming tail tip
    m.spike('Tail3', 'flame', c.tailEnd, (0, 0.6, 0.8), 0.8, 0.4, 0.2)
    m.spike('Tail3', 'flame2', c.tailEnd, (0.4, 0.5, 0.9), 0.55, 0.3, 0.15)
    m.socket('TailFlame', 'Tail3', c.add(c.tailEnd, (0, 0.3, 0.5)))


def pose(c, clip, t, p):
    """the side heads follow the centre head with their own sway, glances and snaps"""
    E = c.E
    base_neck = p.get('Neck', ((0, 0, 0), (0, 0, 0)))[0]
    base_head = p.get('Head', ((0, 0, 0), (0, 0, 0)))[0]
    base_jaw = p.get('Jaw', ((0, 0, 0), (0, 0, 0)))[0]
    for side, s in c.SIDES:
        ph = 1.7 if s > 0 else 3.4
        if clip == 'Idle':
            look = 18 * E * math.sin(TAU * t + ph)
            jaw = max(0.0, 25 * math.sin(TAU * 2 * t + ph) - 15)   # the odd snap
            nod = 5 * math.sin(TAU * t + ph * 2)
        elif clip in ('Walk', 'Run'):
            look, jaw, nod = 6 * math.sin(TAU * t + ph), 4, 3 * math.sin(TAU * 2 * t + ph)
        elif clip == 'Sleep':
            look, jaw, nod = -20 * s, 0, 12
        else:   # Roar / Attack / Happy: all three heads together
            look, jaw, nod = 8 * s * math.sin(TAU * 3 * t), 0, 0
        # side heads are turned outward, so pitch them about their own (turned) side axis: build the
        # exact rotation and hand the kit its XYZ Euler angles
        axis = Vector((math.cos(math.radians(SIDE_YAW * s)), math.sin(math.radians(SIDE_YAW * s)), 0))

        def rot(pitch, yaw):
            mtx = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, axis)
            return tuple(math.degrees(a) for a in mtx.to_euler('XYZ'))
        p[f'Neck{side}'] = (rot(base_neck[0] + nod, base_neck[2] + look * 0.5), (0, 0, 0))
        p[f'Head{side}'] = (rot(base_head[0], base_head[2] + look * 0.6), (0, 0, 0))
        p[f'Jaw{side}'] = (rot(base_jaw[0] * 0.5 + jaw, 0), (0, 0, 0))


build(dict(
    name='Cerberus',
    palette={
        'body': '#3a2f36', 'body2': ('#4f3d44', True, True), 'belly': '#5a4248', 'nose': ('#120c0e', False),
        'horn': ('#e8dcc8', False), 'fang': ('#f6f0e2', False), 'iron': ('#3c3f48', True, True), 'spike': ('#8f949e', False),
        'flame': ('#ff8a1e', False), 'flame2': ('#ffd23a', False), 'lava': ('#ff6a1a', False),
        'foot': '#1e171b', 'claw': ('#d9cfc2', False), 'mouth': '#5a1a1e', 'tongue': '#c2303c',
        'eye_dark': ('#120709', False), 'iris': ('#ff3b1e', False), 'eye_glint': ('#ffd9a0', False),
    },
    body=dict(legL=1.15, legT=1.2, bL=1.12, bW=1.05, bH=1.1, girth=1.05, head=1.0, neck=1.0, neckUp=1.5,
              tail=1.0, tailDroop=0.6, eye=0.9),
    neckRadius=0.85,
    gait=dict(stride=1.15),
    bones=bones, head=head, decor=decor, pose=pose,
))
