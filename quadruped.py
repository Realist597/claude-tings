"""Shared four-legged body plan, rig and animation set (grown out of thornhorn.py).

A species script calls build(spec) with:
    name      model base name; stages export as <name>_Child, <name>_Teen and <name> (Adult)
    palette   {key: '#hex' | ('#hex', dots) | ('#hex', dots, edges)} - needs at least 'body', 'belly', 'foot', 'claw',
              'mouth', 'tongue', 'eye_dark', 'iris', 'eye_glint'
    body      species proportions (multipliers on the Thornhorn baseline): legL legT bL bW bH head
              neck neckUp tail eye girth (body radius), tailDroop
    stages    optional per-stage overrides merged over STAGE_DEFAULTS
    gait      optional {'stride': x, 'duty': x} multipliers
    sides     optional: facets round the body and legs (default 8; 6 = chunkier, chiselled look)
    kneePlates optional: palette key for armour plates over the knees (chunky style)
    head(c)   adds head geometry (head box, snout, jaw, eyes, horns/ears...)
    decor(c)  optional: back/tail decorations
    bones(c)  optional: extra bones (e.g. wings) - add with c.m.bone(...)
    pose(c, clip, t, pose) optional: animate the extra bones per clip

Conventions match kit.py: Z up, faces -Y, ground at Z = 0. Everything is authored in
adult-design units and multiplied by the stage size S.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Monster, envelope, smooth01

TAU = 2 * math.pi

STAGE_DEFAULTS = {
    'Adult': dict(S=1.0, legL=1.0, legT=1.0, bL=1.0, bW=1.0, bH=1.0, head=1.0, eye=1.0, tail=1.0,
                  neck=1.0, grow=1.0, energy=1.0, tint=0.0),
    'Teen': dict(S=0.78, legL=1.1, legT=0.86, bL=0.95, bW=0.84, bH=0.86, head=1.02, eye=1.15, tail=1.0,
                 neck=1.05, grow=0.6, energy=1.25, tint=0.08),
    'Child': dict(S=0.55, legL=0.86, legT=1.05, bL=0.74, bW=0.95, bH=0.95, head=1.45, eye=1.7, tail=0.65,
                  neck=0.65, grow=0.3, energy=1.6, tint=0.16),
}


def _hex(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lighten(hexv, k):
    r, g, b = _hex(hexv)
    return '#%02x%02x%02x' % tuple(int(c + (255 - c) * k) for c in (r, g, b))


class Scaled(Monster):
    """Definition calls are in adult-design units; positions and sizes are multiplied by S."""
    def __init__(self, name, S):
        super().__init__(name)
        self.S = S

    def sv(self, v):
        return tuple(c * self.S for c in v)

    def bone(self, name, head, tail, parent=None):
        super().bone(name, self.sv(head), self.sv(tail), parent)

    def box(self, bone, color, center, size, rot=(0, 0, 0), bevel=0.12, segs=1, taper=None, smooth=False):
        if taper and 'offset' in taper:
            taper = dict(taper, offset=tuple(o * self.S for o in taper['offset']))
        super().box(bone, color, self.sv(center), self.sv(size), rot, bevel * self.S, segs, taper, smooth)

    def spike(self, bone, color, base, direction, length, width, depth=None, twist=0.0, snap=True):
        super().spike(bone, color, self.sv(base), direction, length * self.S, width * self.S,
                      None if depth is None else depth * self.S, twist, snap)

    def socket(self, name, bone, pos):
        super().socket(name, bone, self.sv(pos))

    def strip(self, bone, color, lead, trail, thickness=0.1, smooth=False):
        super().strip(bone, color, [self.sv(p) for p in lead], [self.sv(p) for p in trail], thickness * self.S, smooth)

    def eye(self, bone, center, normal, size=0.3, up=(0, 0, 1), iris='iris'):
        super().eye(bone, self.sv(center), normal, size * self.S, up, iris)

    def blob(self, bone, color, center, radii, rot=(0, 0, 0), u=10, v=7, smooth=False):
        super().blob(bone, color, self.sv(center), self.sv(radii), rot, u, v, smooth)

    def loft(self, bone, color, points, radii, **kw):
        super().loft(bone, color, [self.sv(p) for p in points], [(a * self.S, b * self.S) for a, b in radii], **kw)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


class Ctx:
    """Everything a species hook needs: the monster, stage params and body anchors."""


def build(spec):
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
    stage = args[1] if len(args) > 1 else 'Adult'

    st = dict(STAGE_DEFAULTS[stage])
    st.update(spec.get('stages', {}).get(stage, {}))
    body = dict(legL=1, legT=1, bL=1, bW=1, bH=1, head=1, neck=1, neckUp=1, tail=1, eye=1, girth=1, tailDroop=1)
    body.update(spec.get('body', {}))

    S = st['S']
    name = spec['name'] if stage == 'Adult' else f"{spec['name']}_{stage}"
    m = Scaled(name, S)
    c = Ctx()
    c.m, c.stage, c.S, c.st, c.spec = m, stage, S, st, spec
    c.grow, c.E = st['grow'], st['energy']
    bL, bW, bH = body['bL'] * st['bL'], body['bW'] * st['bW'], body['bH'] * st['bH']
    h, t = body['head'] * st['head'], body['tail'] * st['tail']
    L, T = body['legL'] * st['legL'], body['legT'] * st['legT']
    c.bL, c.bW, c.bH, c.h, c.t, c.L, c.T = bL, bW, bH, h, t, L, T
    c.eye = body['eye'] * st['eye']

    # palette: younger stages are a little lighter
    for key, val in spec['palette'].items():
        hexv, dots, edges = (val, True, False) if isinstance(val, str) else (tuple(val) + (False,))[:3]
        m.color(key, lighten(hexv, st['tint']) if dots else hexv, dots=dots, edges=edges)

    # ---------- anchors ----------
    c.hipZ = hipZ = 2.05 * L
    c.bodyZ = bodyZ = hipZ + 0.4 * bH
    c.ankZ = ankZ = 0.42 * T
    c.kneeZ = kneeZ = ankZ + (hipZ - ankZ) * (0.78 / 1.63)
    nk = body['neck'] * st['neck']
    c.neckStart = neckStart = (0, -1.4 * bL, bodyZ + 0.1 * bH)
    c.hp = hp = add(neckStart, (0, -0.9 * nk, 0.3 * nk * body['neckUp']))
    c.hipsHead = hipsHead = (0, 1.3 * bL, bodyZ - 0.1 * bH)
    c.yF, c.yB = yF, yB = -0.9 * bL, 1.4 * bL
    droop = body['tailDroop']

    def H(dx, dy, dz):
        return add(hp, (dx * h, dy * h, dz * h))

    def tail_pt(ya, za):
        return (0, 1.3 * bL + (ya - 1.3) * t, hipsHead[2] + (za - 2.35) * t * droop)

    def body_pt(ya, za):
        return (0, ya * bL, bodyZ + (za - 2.45) * bH)

    def spine_bone(y):
        return ('Chest' if y < 0.0 else 'Hips' if y < 1.3 * bL else
                'Tail1' if y < 1.3 * bL + 1.4 * t else 'Tail2' if y < 1.3 * bL + 2.7 * t else 'Tail3')

    c.H, c.tail_pt, c.body_pt, c.spine_bone, c.add = H, tail_pt, body_pt, spine_bone, add
    SIDES = c.SIDES = (('L', 1), ('R', -1))

    # ---------- rig ----------
    m.bone('MonsterRoot', (0, 0.3 * bL, 0), (0, 0.3 * bL, 1.0))
    m.bone('Hips', hipsHead, (0, 0, bodyZ), 'MonsterRoot')
    m.bone('Chest', (0, 0, bodyZ), neckStart, 'Hips')
    m.bone('Neck', neckStart, hp, 'Chest')
    m.bone('Head', hp, H(0, -2.1, -0.05), 'Neck')
    m.bone('Jaw', H(0, -0.3, -0.7), H(0, -1.8, -0.8), 'Head')
    t1 = add(hipsHead, (0, 1.4 * t, -0.2 * t * droop))
    t2 = add(t1, (0, 1.3 * t, -0.3 * t * droop))
    t3 = add(t2, (0, 1.3 * t, -0.3 * t * droop))
    c.tailEnd = t3
    m.bone('Tail1', hipsHead, t1, 'Hips')
    m.bone('Tail2', t1, t2, 'Tail1')
    m.bone('Tail3', t2, t3, 'Tail2')
    for side, s in SIDES:
        x = 1.15 * bW * s
        m.bone(f'UpperF{side}', (x, yF, hipZ), (x, yF + 0.2 * L, kneeZ), 'Chest')
        m.bone(f'LowerF{side}', (x, yF + 0.2 * L, kneeZ), (x, yF - 0.05, ankZ), f'UpperF{side}')
        m.bone(f'FootF{side}', (x, yF - 0.05, ankZ), (x, yF - 0.7 * T, 0.15 * T), f'LowerF{side}')
        x = 1.2 * bW * s
        m.bone(f'UpperB{side}', (x, yB, hipZ), (x, yB - 0.4 * L, kneeZ), 'Hips')
        m.bone(f'LowerB{side}', (x, yB - 0.4 * L, kneeZ), (x, yB - 0.05, ankZ), f'UpperB{side}')
        m.bone(f'FootB{side}', (x, yB - 0.05, ankZ), (x, yB - 0.65 * T, 0.15 * T), f'LowerB{side}')
    if spec.get('bones'):
        spec['bones'](c)

    # ---------- body ----------
    g = body['girth']
    tail_pts = [((5.55, 1.5), (0.14, 0.12)), ((4.5, 1.75), (0.36, 0.3)), ((3.3, 2.05), (0.62, 0.54)), ((2.1, 2.3), (1.12, 1.0))]
    body_pts = [((0.9, 2.45), (1.62, 1.36)), ((-0.3, 2.5), (1.66, 1.36)), ((-1.3, 2.6), (1.36, 1.18))]
    pts, radii = [], []
    for (ya, za), (rw, rh) in tail_pts:
        pts.append(tail_pt(ya, za))
        radii.append((rw * bW * g, rh * bH * g))
    for (ya, za), (rw, rh) in body_pts:
        pts.append(body_pt(ya, za))
        radii.append((rw * bW * g, rh * bH * g))
    nr = spec.get('neckRadius', 1.0)
    pts.append(add(hp, (0, 0.2 * nk, -0.1 * nk * (body['neckUp'] - 1))))
    radii.append((1.0 * max(bW * g, 0.8 * h) * nr, 0.95 * max(bH * g, 0.8 * h) * nr))
    pts.append(H(0, -0.4, 0.1))
    radii.append((0.8 * h * nr, 0.8 * h * nr))
    sides = spec.get('sides', 8)
    m.loft(['Tail3', 'Tail2', 'Tail1', 'Hips', 'Chest', 'Neck'], 'body', pts, radii, sides=sides, steps=2 if sides >= 8 else 1, smooth=False)
    if spec.get('belly', True):
        m.box(['Hips', 'Chest'], 'belly', (0, 0.3 * bL, bodyZ - 0.95 * bH * g), (2.1 * bW * g, 3.4 * bL, 0.4 * bH),
              bevel=0.15, segs=1)

    spec['head'](c)
    if spec.get('decor'):
        spec['decor'](c)

    # ---------- legs ----------
    for side, s in SIDES:
        for end, x, y, r0, top in (('F', 1.15 * bW * s, yF, (0.62, 0.62), 0.1), ('B', 1.2 * bW * s, yB, (0.8, 0.88), 0.15)):
            knee = (x, y + (0.2 if end == 'F' else -0.4) * L, kneeZ)
            m.loft([f'Upper{end}{side}', f'Lower{end}{side}', f'Foot{end}{side}'], 'body',
                   [(x, y + (-0.05 if end == 'F' else 0.05), hipZ + top), knee, (x, y - 0.05, ankZ + 0.08)],
                   [(r0[0] * T, r0[1] * T), (0.5 * T, 0.5 * T), (0.43 * T, 0.43 * T)],
                   sides=sides, steps=2 if sides >= 8 else 1, smooth=False, up=(0, -1, 0))
            if spec.get('kneePlates'):
                m.box(f'Upper{end}{side}', spec['kneePlates'], (x * 1.06, knee[1] - 0.32 * T, kneeZ + 0.1), (0.75 * T, 0.3 * T, 0.7 * T),
                      rot=(10, 0, 0), bevel=0.04)
            fy = y - (0.25 if end == 'F' else 0.4) * T
            m.box(f'Foot{end}{side}', 'foot', (x, fy, 0.24 * T), (1.0 * T, 1.2 * T, 0.48 * T), bevel=0.15 * T, segs=1)
            for dx in (-0.29, 0.0, 0.29):
                m.spike(f'Foot{end}{side}', 'claw', (x + dx * T, fy - 0.55 * T, 0.2 * T), (0, -1, -0.3), 0.25 * T, 0.16 * T)

    _animations(c, spec)
    m.refs = c.refs
    m.build(out)


def _animations(c, spec):
    m, S, E, L = c.m, c.S, c.E, c.L
    gait = spec.get('gait', {})
    LEGS = {f'{e}{side}': (f'Upper{e}{side}', f'Lower{e}{side}', f'Foot{e}{side}') for e in 'FB' for side, _ in c.SIDES}
    FRONT_LEVER = abs(c.hipsHead[1] - c.yF) * S
    WALK = dict(stride=1.1 * L * gait.get('stride', 1), lift=0.4 * L, duty=0.64 * gait.get('duty', 1), frames=32)
    RUN = dict(stride=1.8 * L * gait.get('stride', 1), lift=0.6 * L, duty=0.4 * gait.get('duty', 1), frames=20)
    extra = spec.get('pose')

    def finish(clip, t_, pose):
        if extra:
            extra(c, clip, t_, pose)
        return pose

    def step(u, stride, lift, duty):
        u %= 1.0
        if u < duty:
            s = u / duty
            roll = smooth01((s - 0.7) / 0.3)
            return -stride / 2 + stride * s, 0.12 * S * roll, 22 * roll
        s = (u - duty) / (1 - duty)
        dz = lift * math.sin(math.pi * s) ** 0.8 + 0.12 * S * (1 - smooth01(s / 0.25))
        tilt = 22 * (1 - smooth01(s / 0.6)) - 8 * math.sin(math.pi * smooth01((s - 0.5) / 0.5))
        return stride / 2 - stride * smooth01(s), dz, tilt

    def legs(pose, t_, phases, g, shift_front=(0, 0), shift_back=(0, 0)):
        for leg, ph in phases.items():
            dy, dz, tilt = step(t_ + ph, g['stride'] * S, g['lift'] * S, g['duty'])
            ay, az = m.rest_ankle(LEGS[leg][1])
            shift = shift_front if leg[0] == 'F' else shift_back
            m.ik_leg(pose, *LEGS[leg], (ay + dy, az + dz), shift, tilt)

    def planted(pose, shift_front=(0, 0), shift_back=(0, 0), only=None):
        for leg, chain in LEGS.items():
            if only and leg[0] not in only:
                continue
            m.ik_leg(pose, *chain, m.rest_ankle(chain[1]), shift_front if leg[0] == 'F' else shift_back)

    def tail(pose, p, amp, pitch=(0, 0, 0)):
        for i, b in enumerate(('Tail1', 'Tail2', 'Tail3')):
            pose[b] = ((pitch[i], 0, amp * E * (1 + 0.4 * i) * math.sin(p - 0.6 * (i + 1))), (0, 0, 0))

    def idle(t_):
        p = TAU * t_
        bob = 0.035 * S * E * math.sin(p)
        pose = {
            'Hips': ((0, 0, 0), (0, 0, bob)),
            'Chest': ((1.0 * E * math.sin(p), 0, 0), (0, 0, 0)),
            'Neck': ((2 * E * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
            'Head': ((2 * E * math.sin(p + 1), 0, 6 * E * math.sin(p)), (0, 0, 0)),
            'Jaw': ((2 + 2 * math.sin(2 * p), 0, 0), (0, 0, 0)),
        }
        tail(pose, p, 5)
        planted(pose, (0, bob), (0, bob))
        return finish('Idle', t_, pose)

    def walk(t_):
        p = TAU * t_
        lean = math.cos(TAU * (t_ - 0.435))
        bob = -0.06 * S * E * math.cos(2 * TAU * (t_ - 0.3))
        flex = math.sin(TAU * (t_ - 0.1))
        pose = {
            'Hips': ((0, -3 * lean, 3 * flex), (0.07 * S * lean, 0, bob)),
            'Chest': ((0, 2 * lean, -5 * flex), (0, 0, 0)),
            'Neck': ((3 * E * math.cos(2 * TAU * (t_ - 0.36)), 0, 3 * flex), (0, 0, 0)),
            'Head': ((2.5 * E * math.cos(2 * TAU * (t_ - 0.42)), 0, 2 * flex), (0, 0, 0)),
            'Jaw': ((3, 0, 0), (0, 0, 0)),
            'Tail1': ((2 * math.cos(2 * p), 0, -7 * E * flex), (0, 0, 0)),
            'Tail2': ((0, 0, -10 * E * math.sin(TAU * (t_ - 0.22))), (0, 0, 0)),
            'Tail3': ((0, 0, -13 * E * math.sin(TAU * (t_ - 0.34))), (0, 0, 0)),
        }
        legs(pose, t_, {'BL': 0.0, 'FL': 0.25, 'BR': 0.5, 'FR': 0.75}, WALK, (0, bob), (0, bob))
        return finish('Walk', t_, pose)

    def run(t_):
        p = TAU * t_
        bob = (0.16 * math.sin(p) + 0.06) * S * E
        pitch = 4 * E * math.sin(p)
        pose = {
            'Hips': ((pitch, 0, 0), (0, 0, bob)),
            'Chest': ((-3 * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
            'Neck': ((-6, 0, 0), (0, 0, 0)),
            'Head': ((-4 + 4 * E * math.sin(p + 1), 0, 0), (0, 0, 0)),
            'Jaw': ((12, 0, 0), (0, 0, 0)),
        }
        tail(pose, p, 3, pitch=(10 + 5 * math.sin(p), 5 * math.sin(p - 1), 4 * math.sin(p - 1.6)))
        front_dz = bob - FRONT_LEVER * math.sin(math.radians(pitch))
        legs(pose, t_, {'BL': 0.0, 'BR': 0.1, 'FL': 0.5, 'FR': 0.6}, RUN, (0, front_dz), (0, bob))
        return finish('Run', t_, pose)

    def sleep(t_):
        p = TAU * t_
        drop = -(c.bodyZ - 1.15 * c.bH * c.spec.get('body', {}).get('girth', 1) - 0.35) * S + 0.04 * S * math.sin(p)
        pose = {
            'MonsterRoot': ((0, 0, 0), (0, 0, drop)),
            'Chest': ((1.0 * math.sin(p), 0, 0), (0, 0, 0)),
            'Neck': ((10 + 4 * (c.spec.get('body', {}).get('neckUp', 1) - 1), 0, 0), (0, 0, 0)),
            'Head': ((10 + 1.5 * math.sin(p + 0.5), 0, 0), (0, 0, 0)),
            'Tail1': ((-6, 0, 18), (0, 0, 0)),
            'Tail2': ((-4, 0, 28), (0, 0, 0)),
            'Tail3': ((0, 0, 35), (0, 0, 0)),
        }
        for leg, chain in LEGS.items():
            ay, az = m.rest_ankle(chain[1])
            target = (ay - 0.55 * S * L, 0.32 * S * c.T) if leg[0] == 'F' else (ay + 0.15 * S * L, 0.3 * S * c.T)
            m.ik_leg(pose, *chain, target, (0, drop))
        return finish('Sleep', t_, pose)

    def roar(t_):
        e = envelope(t_, 0.22, 0.75)
        shake = math.sin(TAU * 7 * t_) * envelope(t_, 0.3, 0.7, 0.8)
        pose = {
            'MonsterRoot': ((0, 0, 0), (0, 0.25 * S * e, 0)),
            'Hips': ((-4 * e, 0, 0), (0, 0, 0)),
            'Chest': ((-10 * e, 0, 0), (0, 0, 0)),
            'Neck': ((-14 * e, 0, 0), (0, 0, 0)),
            'Head': ((-16 * e, 0, 9 * shake), (0, 0, 0)),
            'Jaw': ((40 * e, 0, 0), (0, 0, 0)),
            'Tail1': ((10 * e, 0, 0), (0, 0, 0)),
            'Tail2': ((8 * e, 0, 6 * shake), (0, 0, 0)),
            'Tail3': ((6 * e, 0, 8 * shake), (0, 0, 0)),
        }
        for side, _ in c.SIDES:
            pose[f'UpperF{side}'] = ((-14 * e, 0, 0), (0, 0, 0))
            pose[f'LowerF{side}'] = ((22 * e, 0, 0), (0, 0, 0))
            pose[f'FootF{side}'] = ((-8 * e, 0, 0), (0, 0, 0))
        planted(pose, shift_back=(0.25 * S * e, 0), only='B')
        return finish('Roar', t_, pose)

    def attack(t_):
        w = envelope(t_, 0.3, 0.3, 0.45)
        s = smooth01((t_ - 0.33) / 0.15) if t_ < 0.6 else 1 - smooth01((t_ - 0.6) / 0.4)
        dy = (0.4 * w - 0.9 * s) * S
        pose = {
            'MonsterRoot': ((0, 0, 0), (0, dy, 0)),
            'Chest': ((-5 * w + 5 * s, 0, 0), (0, 0, 0)),
            'Neck': ((-8 * w + 12 * s, 0, 0), (0, 0, 0)),
            'Head': ((-14 * w + 18 * s, 0, 0), (0, 0, 0)),
            'Jaw': ((12 * w + 30 * s * (1 - s), 0, 0), (0, 0, 0)),
            'Tail1': ((10 * w, 0, 0), (0, 0, 0)),
        }
        planted(pose, (dy, 0), (dy, 0))
        return finish('Attack', t_, pose)

    def happy(t_):
        hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
        settle = envelope(t_, 0.1, 0.55, 1.0)
        pose = {
            'MonsterRoot': ((0, 0, 0), (0, 0, 0.5 * S * E * hop)),
            'Chest': ((-8 * settle, 0, 0), (0, 0, 0)),
            'Neck': ((-12 * settle, 0, 0), (0, 0, 0)),
            'Head': ((-10 * settle, 0, 10 * math.sin(TAU * 2 * t_) * settle), (0, 0, 0)),
            'Jaw': ((25 * settle, 0, 0), (0, 0, 0)),
        }
        tail(pose, TAU * 2 * t_, 10 * settle)
        for leg, chain in LEGS.items():
            ay, az = m.rest_ankle(chain[1])
            m.ik_leg(pose, *chain, (ay, az + 0.15 * S * hop), (0, 0.5 * S * E * hop))
        return finish('Happy', t_, pose)

    m.anim('Idle', 72, True, idle, key_step=4)
    m.anim('Walk', WALK['frames'], True, walk, key_step=2)
    m.anim('Run', RUN['frames'], True, run, key_step=1)
    m.anim('Sleep', 96, True, sleep, key_step=8)
    m.anim('Roar', 54, False, roar, key_step=3)
    m.anim('Attack', 30, False, attack, key_step=2)
    m.anim('Happy', 36, False, happy, key_step=2)
    c.refs = {k: g['stride'] * S / (g['duty'] * g['frames'] / 30) for k, g in (('Walk', WALK), ('Run', RUN))}


def standard_eyes(c, x=0.97, y=-1.05, z=0.2, size=0.4, normal_y=-0.3):
    """Eyes on the sides of a Thornhorn-proportioned head; scales up for children."""
    for side, s in c.SIDES:
        k = 1.0 if c.h <= 1 else 1.05
        c.m.eye('Head', c.H(x * s * k, y - (0.05 if c.h > 1 else 0), z + (0.08 if c.h > 1 else 0)),
                (1 * s, normal_y, 0.1), size * c.h * c.eye)


def standard_jaw(c, width=1.6, length=2.0, color='belly'):
    H, h = c.H, c.h
    c.m.box('Head', 'mouth', H(0, -1.0, -0.65), (width * 0.94 * h, length * 0.92 * h, 0.22 * h), bevel=0.0)
    c.m.box('Jaw', color, H(0, -1.1, -1.0), (width * h, length * h, 0.45 * h), bevel=0.15 * h, segs=1,
            taper=dict(axis='y', end=-1, scale=(0.75, 0.8)))
    c.m.box('Jaw', 'mouth', H(0, -1.0, -0.89), (width * 0.875 * h, length * 0.875 * h, 0.2 * h), bevel=0.0)
    c.m.box('Jaw', 'tongue', H(0, -1.15, -0.83), (0.65 * h, 1.0 * h, 0.1 * h), bevel=0.04 * h)
