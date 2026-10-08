"""Sylvan Drake - Legendary forest dragon, chunky style: a chiselled head with square fangs, glowing emerald
eyes and branching wooden horns, a leaf-blade crest, armour plates, a glowing emerald crystal spine and
chest crystals, outlined leaf wings. Faces -Y.
Extra bones WingL/WingTipL/WingR/WingTipR flap per clip. In Roblox it gets an aura,
falling-leaf particles and glowing crystals (see MonsterVfx)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quadruped import build, standard_eyes, TAU
from kit import envelope, smooth01


def bones(c):
    m, bW, bL, bH, g = c.m, c.bW, c.bL, c.bH, c.grow
    span = 0.55 + 0.45 * g      # children have stubby wings
    for side, s in c.SIDES:
        sh = (0.7 * bW * s, -0.55 * bL, c.bodyZ + 1.0 * bH)
        el = (sh[0] + 1.7 * span * s, sh[1] + 0.5, sh[2] + 1.7 * span)
        tip = (el[0] + 1.9 * span * s, el[1] + 1.2, el[2] + 0.5 * span)
        m.bone(f'Wing{side}', sh, el, 'Chest')
        m.bone(f'WingTip{side}', el, tip, f'Wing{side}')
        c.__dict__[f'wing{side}'] = (sh, el, tip)


def head(c):
    m, H, h, g = c.m, c.H, c.h, c.grow
    # chiselled skull and long snout
    m.box('Head', 'body', H(0, -0.9, 0.05), (1.9 * h, 2.2 * h, 1.5 * h), bevel=0.1 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.75, 0.75)))
    m.box('Head', 'body', H(0, -2.15, -0.1), (1.2 * h, 1.2 * h, 0.85 * h), bevel=0.08 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.72, 0.72)))
    m.box('Head', 'plate', H(0, -2.0, 0.34), (0.8 * h, 1.1 * h, 0.16 * h), rot=(-6, 0, 0), bevel=0.03 * h)   # snout ridge
    for side, s in c.SIDES:
        m.box('Head', 'plate', H(0.5 * s, -1.0, 0.72), (0.8 * h, 1.15 * h, 0.22 * h), rot=(-10, -16 * s, 0), bevel=0.03 * h)   # brow
        m.box('Head', 'plate', H(0.95 * s, -0.55, -0.15), (0.2 * h, 1.2 * h, 0.8 * h), rot=(0, 12 * s, 0), bevel=0.03 * h)   # cheek
        m.box('Head', 'dark', H(0.88 * s, -1.05, 0.3), (0.16 * h, 0.6 * h, 0.46 * h), bevel=0.03 * h)
        m.eye('Head', H(0.97 * s, -1.07, 0.3), (1 * s, -0.35, 0.1), 0.42 * h * c.eye)
        m.box('Head', 'dark', H(0.24 * s, -2.72, 0.12), (0.16 * h, 0.06 * h, 0.12 * h), bevel=0.0)   # nostril
        # sweeping wooden horns that branch like antlers
        base = H(0.55 * s, -0.4, 0.7)
        k = (0.5 + 1.3 * g) * h
        horn = [base, c.add(base, (0.25 * s * k, 0.35 * k, 0.45 * k)), c.add(base, (0.45 * s * k, 0.95 * k, 0.75 * k)),
                c.add(base, (0.55 * s * k, 1.6 * k, 0.7 * k))]
        m.loft('Head', 'horn', horn, [(0.3 * h, 0.3 * h), (0.24 * h, 0.24 * h), (0.15 * h, 0.15 * h), (0.02, 0.02)],
               sides=6, steps=2, smooth=False)
        if g > 0.4:
            for at, d, L in ((1, (0.35 * s, -0.1, 1.0), 0.55), (2, (0.6 * s, 0.2, 0.7), 0.45)):
                b = horn[at]
                tip = c.add(b, (d[0] * k * L, d[1] * k * L, d[2] * k * L))
                m.loft('Head', 'horn', [b, tip], [(0.13 * h, 0.13 * h), (0.02, 0.02)], sides=5, steps=1, smooth=False)
    # crest of outlined leaf blades behind the head
    for i, (x, yaw) in enumerate(((-0.4, -18), (0.0, 0), (0.4, 18))):
        L = (0.6 + 0.7 * g) * h * (1.15 if i == 1 else 1)
        base = H(x * 0.6, -0.1, 0.6)
        m.box('Head', 'wing', c.add(base, (x * 0.3 * L, 0.38 * L, 0.32 * L)), (0.1 * h, 0.9 * L, 0.38 * h),
              rot=(40, 0, yaw), bevel=0.02)
    # jaws: big square fangs top and bottom
    m.box('Head', 'mouth', H(0, -1.45, -0.58), (1.25 * h, 2.3 * h, 0.16 * h), bevel=0.0)
    m.box('Jaw', 'belly', H(0, -1.45, -0.75), (1.35 * h, 2.4 * h, 0.36 * h), bevel=0.06 * h,
          taper=dict(axis='y', end=-1, scale=(0.65, 0.8)))
    m.box('Jaw', 'mouth', H(0, -1.4, -0.6), (1.1 * h, 2.05 * h, 0.12 * h), bevel=0.0)
    m.box('Jaw', 'tongue', H(0, -1.6, -0.55), (0.45 * h, 1.2 * h, 0.08 * h), bevel=0.03 * h)
    for side, s in c.SIDES:
        for k_ in range(4):
            m.box('Head', 'tooth', H(0.48 * s * (1 - 0.07 * k_), -2.35 + k_ * 0.45, -0.68), (0.16 * h, 0.16 * h, 0.3 * h), rot=(0, 0, 45), bevel=0.01)
            m.box('Jaw', 'tooth', H(0.44 * s * (1 - 0.07 * k_), -2.15 + k_ * 0.45, -0.55), (0.14 * h, 0.14 * h, 0.26 * h), rot=(0, 0, 45), bevel=0.01)


def decor(c):
    m, g = c.m, c.grow
    # glowing emerald crystal spine, each crystal set in a dark armour plate
    for ya, za, size, region in ((-1.0, 3.6, 0.95, 'body'), (-0.1, 3.7, 1.2, 'body'), (0.8, 3.62, 1.05, 'body'),
                                 (1.7, 3.35, 0.9, 'tail'), (2.8, 2.9, 0.75, 'tail'), (3.8, 2.45, 0.6, 'tail'),
                                 (4.7, 2.05, 0.45, 'tail')):
        p = c.body_pt(ya, za) if region == 'body' else c.tail_pt(ya, za)
        bone = c.spine_bone(p[1])
        k = size * (0.4 + 0.6 * g)
        m.box(bone, 'plate', (0, p[1], p[2] - 0.32 * c.bH), (0.95 * k + 0.2, 0.8 * k + 0.2, 0.2), rot=(12, 0, 0), bevel=0.04)
        m.spike(bone, 'crystal', (0, p[1], p[2] - 0.3 * c.bH), (0, 0.3, 1), 1.15 * k, 0.42 * k, 0.42 * k, twist=45)
        if size >= 0.85:
            m.spike(bone, 'crystal2', (0, p[1] + 0.12 * k, p[2] - 0.25 * c.bH), (0.4, 0.4, 1), 0.6 * k, 0.24 * k, 0.24 * k, twist=45)
            m.spike(bone, 'crystal2', (0, p[1] + 0.12 * k, p[2] - 0.25 * c.bH), (-0.4, 0.4, 1), 0.6 * k, 0.24 * k, 0.24 * k, twist=45)
            m.socket(f'Crystal{len(getattr(m, "sockets", [])) + 1}', bone, (0, p[1] + 0.25 * k, p[2] + 0.6 * k))
    # armour plates down the flanks
    for side, s in c.SIDES:
        for ya in (-0.8, 0.0, 0.8):
            p = c.body_pt(ya, 3.15)
            m.box(c.spine_bone(p[1]), 'plate', (0.95 * c.bW * s, p[1], p[2]), (0.8, 0.75, 0.2), rot=(10, 35 * s, 0), bevel=0.04)
    # crystal heart cluster on the chest
    heart = c.body_pt(-1.15, 2.3)
    heart = (0, heart[1] - 0.95 * c.bL, heart[2])
    for d in ((0, -1, 0.3), (0.5, -1, 0.1), (-0.5, -1, 0.1), (0, -1, -0.4)):
        m.spike('Chest', 'crystal', heart, d, 0.55 * (0.5 + 0.5 * g), 0.28, 0.28, twist=45, snap=False)
    m.socket('Heart', 'Chest', c.body_pt(-0.4, 2.5))
    # leaf fin on the tail tip (outlined)
    m.box('Tail3', 'wing', c.tailEnd, (0.12, 1.5 * (0.5 + 0.5 * g), 1.0 * (0.5 + 0.5 * g)), bevel=0.03,
          taper=dict(axis='y', end=1, scale=(1, 0.2)))
    # wings: one continuous leaf membrane per side from shoulder to tip, with a scalloped
    # trailing edge, a thick leading-edge "arm" and finger ribs fanning out from the elbow.
    # Skin weights blend Wing -> WingTip along the span, so the wing bends at the elbow.
    k = 0.55 + 0.45 * g
    n = 13
    for side, s in c.SIDES:
        sh, el, tip = c.__dict__[f'wing{side}']
        bones = [f'Wing{side}', f'WingTip{side}']
        lead, trail = [], []
        chord_dir = (0.1 * s, 1.0, -0.5)
        cl = math.sqrt(sum(x * x for x in chord_dir))
        chord_dir = tuple(x / cl for x in chord_dir)
        for i in range(n):
            u = i / (n - 1)
            if u <= 0.45:
                a, b, f = sh, el, u / 0.45
            else:
                a, b, f = el, tip, (u - 0.45) / 0.55
            p = tuple(x + (y - x) * f for x, y in zip(a, b))
            lead.append(p)
            # chord shrinks toward the tip; three scallops between the finger ribs
            chord = (2.7 * (1 - u) ** 0.75 + 0.25) * k * (0.74 + 0.26 * abs(math.cos(u * 3 * math.pi)))
            trail.append(tuple(x + d * chord for x, d in zip(p, chord_dir)))
        m.strip(bones, 'wing', lead, trail, thickness=0.12)
        # wingtip trail: two points across the tip of the wing
        m.socket(f'WingTip{side}', bones[1], tip)
        m.socket(f'WingTrail{side}', bones[1], trail[-3])
        # leading-edge arm, thick at the shoulder and tapering to a claw at the tip
        m.loft(bones, 'vein', [sh, el, tip], [(0.2, 0.2), (0.15, 0.15), (0.07, 0.07)], sides=6, steps=3, smooth=False)
        m.spike(bones[1], 'claw', el, (0.3 * s, -0.4, 1.0), 0.35 * k, 0.14, snap=False)
        # finger ribs from the elbow to each scallop point
        for j in (4, 8, 12):
            m.loft(bones[1] if j > 4 else bones, 'vein', [el, trail[j]], [(0.09, 0.09), (0.045, 0.045)],
                   sides=5, steps=1, smooth=False)
        m.loft([bones[0]], 'vein', [sh, trail[0]], [(0.1, 0.1), (0.05, 0.05)], sides=5, steps=1, smooth=False)
        # rounded shoulder joint so the wing grows out of the body
        m.blob(['Chest', bones[0]], 'body', sh, (0.42, 0.42, 0.38), u=8, v=5)


def pose(c, clip, t, p):
    """Wing flaps per clip. Positive 'up' raises the wing for both sides."""
    if clip == 'Idle':
        up, fold, tipf = 8 * math.sin(TAU * t), 10, 6 * math.sin(TAU * t - 0.6)
    elif clip == 'Walk':
        up, fold, tipf = -6 + 5 * math.sin(TAU * 2 * t), 25, 10
    elif clip == 'Run':
        up, fold, tipf = 34 * math.sin(TAU * t), 0, 22 * math.sin(TAU * t - 0.9)
    elif clip == 'Sleep':
        up, fold, tipf = -32, 40, 35
    elif clip == 'Roar':
        e = envelope(t, 0.2, 0.75)
        up, fold, tipf = 38 * e + 6 * math.sin(TAU * 6 * t) * e, -15 * e, -10 * e
    elif clip == 'Attack':
        w = envelope(t, 0.3, 0.5, 0.9)
        up, fold, tipf = 30 * w, -10 * w, -12 * w
    else:  # Happy
        up, fold, tipf = 28 * math.sin(TAU * 3 * t) * envelope(t, 0.1, 0.7), 0, 15 * math.sin(TAU * 3 * t - 0.8)
    for side, s in c.SIDES:
        # flap = roll about the body's forward axis, fold = sweep backwards about Z
        p[f'Wing{side}'] = ((0, -up * s, fold * s), (0, 0, 0))
        p[f'WingTip{side}'] = ((0, -tipf * s, fold * 0.6 * s), (0, 0, 0))


build(dict(
    name='SylvanDrake',
    palette={
        'body': '#3c8253', 'belly': '#c6e294', 'plate': ('#1f5034', True, True), 'wing': ('#5fb84a', True, True),
        'vein': '#5a3e26', 'crystal': ('#6dffb0', False), 'crystal2': ('#c8ffe4', False), 'horn': ('#a07a4a', True, True),
        'tooth': ('#fbf7ee', False), 'dark': ('#0b120d', False), 'foot': '#1a2e22', 'claw': ('#f2f2e6', False),
        'mouth': ('#4a1a22', False), 'tongue': '#d6405c', 'eye_dark': ('#071009', False), 'iris': ('#6dffb0', False),
        'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=0.95, legT=0.9, bL=1.05, bW=0.85, bH=0.85, girth=0.92, head=0.95, neck=1.5, neckUp=1.6,
              tail=1.5, eye=1.0),
    neckRadius=0.8,
    sides=6,
    kneePlates='plate',
    bones=bones, head=head, decor=decor, pose=pose,
))
