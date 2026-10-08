"""Headless Horseman - SECRET Haunted monster (Haunted Pumpkin featured egg): a headless rider on a
nightmare horse. The horse is a gaunt black charger with an iron chanfron and a bone skull mask over
its long face, purple ghost-fire eyes, a mane and tail of ghost flame, an armoured breast plate,
spiked barding, a skull bridle on chains, and hooves wreathed in ghost fire. The rider sits in a
tattered crimson-lined saddle: a long ragged black coat with gold buttons and a high spiked collar,
a jagged cape streaming behind, belt and bandolier, tall riding boots in iron stirrups - and where its
head should be, purple flame pours out of the collar. In its left hand it holds its own head high: a
grinning jack-o'-lantern blazing orange; in its right it carries a long jagged sword with a burning
edge. Faces -Y.
Sockets: PumpkinHead, NeckFire, HoofFL/FR/BL/BR, BladeTip, BladeBase, EyeL/EyeR, ManeFire1-4, TailFire."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from quadruped import build, TAU
from kit import envelope


def lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def flame(m, bone, base, d, length, width, core=True, col='glow', col2='glow2'):
    m.spike(bone, col, base, d, length, width, width * 0.45, snap=False)
    if core:
        m.spike(bone, col2, base, d, length * 0.6, width * 0.5, width * 0.25, snap=False)


def tri(m, bone, color, center, w, hgt, slant, depth):
    m.box(bone, color, center, (w, depth, hgt), rot=(0, slant, 0), bevel=0.0, taper=dict(axis='z', end=1, scale=(0.05, 1)))


# ---------------- extra bones: the rider ----------------
def bones(c):
    m, bW, bH, bL = c.m, c.bW, c.bH, c.bL
    k = 1.2 + 0.2 * c.grow           # the rider is a touch smaller on young horses
    c.k = k
    seat = (0, 0.15 * bL, c.bodyZ + 1.28 * bH * c.spec['body']['girth'])
    c.seat = seat
    R = lambda x, y, z: add(seat, (x * k, y * k, z * k))
    c.R = R
    m.bone('RiderHips', R(0, 0.05, 0.05), R(0, 0.0, 0.75), 'Hips')
    m.bone('RiderChest', R(0, 0.0, 0.75), R(0, -0.05, 1.85), 'RiderHips')
    # left arm raised, holding the head up and out; right arm out with the sword
    c.armL = (R(0.62, 0.0, 1.62), R(1.05, -0.3, 2.2), R(1.15, -0.55, 2.85))
    c.armR = (R(-0.62, 0.0, 1.62), R(-1.05, -0.2, 1.05), R(-1.15, -0.75, 0.85))
    for side, (sh, el, wr) in (('L', c.armL), ('R', c.armR)):
        m.bone(f'RiderArm{side}', sh, el, 'RiderChest')
        m.bone(f'RiderFore{side}', el, wr, f'RiderArm{side}')


def head(c):
    """the nightmare horse's long head: dark muzzle under a bone skull mask and an iron chanfron"""
    m, H, h = c.m, c.H, c.h
    m.box('Head', 'body', H(0, -0.6, 0.15), (1.2 * h, 1.3 * h, 1.15 * h), bevel=0.3 * h, segs=1)
    m.box('Head', 'body', H(0, -1.75, -0.15), (0.85 * h, 1.7 * h, 0.85 * h), bevel=0.2 * h, segs=1,
          taper=dict(axis='y', end=-1, scale=(0.82, 0.85)))
    m.box('Head', 'mouth', H(0, -1.9, -0.55), (0.72 * h, 1.3 * h, 0.08 * h), bevel=0.0)
    m.box('Jaw', 'body2', H(0, -1.75, -0.66), (0.72 * h, 1.3 * h, 0.2 * h), bevel=0.05 * h, taper=dict(axis='y', end=-1, scale=(0.75, 0.85)))
    # bone skull mask over the muzzle: nasal ridge, cheek plates, exposed teeth
    m.box('Head', 'bone', H(0, -1.75, 0.3), (0.7 * h, 1.7 * h, 0.14 * h), rot=(-4, 0, 0), bevel=0.04 * h,
          taper=dict(axis='y', end=-1, scale=(0.75, 1)))
    for side, s in c.SIDES:
        m.box('Head', 'bone', H(0.45 * s, -1.5, -0.05), (0.1 * h, 1.1 * h, 0.32 * h), rot=(0, 0, 4 * s), bevel=0.03 * h)
        for i in range(5):   # bared bone teeth along the side
            m.box('Head', 'bone', H(0.36 * s, -2.35 + 0.22 * i, -0.47), (0.08 * h, 0.12 * h, 0.16 * h), bevel=0.0)
            m.box('Jaw', 'bone', H(0.34 * s, -2.25 + 0.22 * i, -0.6), (0.08 * h, 0.12 * h, 0.12 * h), bevel=0.0)
        m.blob('Head', 'dark', H(0.22 * s, -2.55, -0.05), (0.1 * h, 0.06 * h, 0.12 * h), u=5, v=4)   # nostrils
        flame(m, 'Head', H(0.22 * s, -2.58, -0.1), (0.3 * s, -1, -0.3), 0.35 * h, 0.1 * h, core=False)   # snorting ghost-fire
        # eyes: sunken sockets burning with ghost fire, swept back
        m.box('Head', 'dark', H(0.55 * s, -0.95, 0.35), (0.18 * h, 0.4 * h, 0.24 * h), rot=(0, 0, -15 * s), bevel=0.02 * h)
        m.eye('Head', H(0.6 * s, -0.98, 0.36), (1 * s, -0.5, 0.1), 0.17 * h * c.eye)
        flame(m, 'Head', H(0.6 * s, -0.85, 0.42), (0.4 * s, 1, 0.5), 0.5 * h, 0.12 * h)
        m.socket(f'Eye{side}', 'Head', H(0.62 * s, -1.0, 0.36))
        # ears pinned back, tipped with flame
        e0 = H(0.35 * s, -0.25, 0.7)
        m.spike('Head', 'body2', e0, (0.25 * s, 0.7, 0.7), 0.7 * h, 0.32 * h, 0.12 * h)
        # bridle: straps and a skull rosette on the cheek, reins of chain back to the rider
        m.box('Head', 'leather', H(0.5 * s, -1.25, 0.05), (0.06 * h, 0.12 * h, 0.9 * h), bevel=0.0)
        m.box('Head', 'leather', H(0.47 * s, -1.75, -0.2), (0.06 * h, 1.0 * h, 0.12 * h), bevel=0.0)
        m.blob('Head', 'skull', H(0.54 * s, -1.25, -0.2), (0.06 * h, 0.12 * h, 0.12 * h), u=6, v=4)
        m.blob('Head', 'glow', H(0.6 * s, -1.29, -0.18), (0.03 * h, 0.04 * h, 0.04 * h), u=4, v=3)
    # iron chanfron plate over the brow with a curved spike horn
    m.box('Head', 'iron', H(0, -0.95, 0.72), (0.8 * h, 1.1 * h, 0.14 * h), rot=(-10, 0, 0), bevel=0.04 * h,
          taper=dict(axis='y', end=-1, scale=(0.6, 1)))
    m.box('Head', 'gold', H(0, -0.95, 0.8), (0.12 * h, 0.95 * h, 0.06 * h), rot=(-10, 0, 0), bevel=0.0)
    m.spike('Head', 'iron', H(0, -0.75, 0.82), (0, -0.4, 1), 0.85 * h, 0.22 * h, snap=False)
    m.spike('Head', 'gold', H(0, -0.75, 0.82), (0, -0.4, 1), 0.3 * h, 0.25 * h, snap=False)


def decor(c):
    m, g, bW, bH, bL, k, R = c.m, c.grow, c.bW, c.bH, c.bL, c.k, c.R
    gk = c.spec['body']['girth']
    # ---- ghost-fire mane down the neck and a forelock ----
    for i in range(6):
        t = i / 5
        p = lerp(add(c.hp, (0, 0.35 * c.h, 0.75 * c.h)), add(c.neckStart, (0, 0.3, 0.95 * bH)), t)
        bone = 'Neck' if t < 0.7 else 'Chest'
        flame(m, bone, p, (0, 0.8, 0.6), (1.3 - 0.35 * abs(t - 0.4)) * (0.7 + 0.3 * g), 0.4)
        if i % 2 == 0:
            m.socket(f'ManeFire{i // 2 + 1}', bone, add(p, (0, 0.3, 0.5)))
    flame(m, 'Head', c.H(0, -0.45, 0.85), (0, -0.4, 1), 0.7 * c.h, 0.25 * c.h)
    # ---- the tail: a long sweeping plume of ghost fire ----
    tip = c.tailEnd
    for i, d in enumerate(((0, 1, -0.4), (0.35, 0.9, -0.5), (-0.35, 0.9, -0.5), (0, 0.8, -0.1))):
        flame(m, 'Tail3', add(tip, (0, -0.3, 0)), d, (2.0 - 0.25 * i) * (0.7 + 0.3 * g), 0.75, core=i < 2)
    for t, bone in ((0.35, 'Tail2'), (0.7, 'Tail3')):
        p = c.tail_pt(1.3 + 4.2 * t, 2.35 - 0.8 * t)
        flame(m, bone, p, (0, 0.5, -0.4), 0.8, 0.4, core=False)
    m.socket('TailFire', 'Tail3', add(tip, (0, 0.6, -0.3)))
    # ---- barding: breastplate with a skull boss, spiked crupper plate, rib-straps ----
    bp = c.body_pt(-1.75, 2.45)
    m.box('Chest', 'iron', add(bp, (0, -0.15, -0.1)), (1.9 * bW * gk, 0.3, 1.5 * bH), rot=(14, 0, 0), bevel=0.08,
          taper=dict(axis='z', end=-1, scale=(0.8, 1)))
    m.box('Chest', 'gold', add(bp, (0, -0.32, 0.55)), (1.6 * bW * gk, 0.1, 0.12), rot=(14, 0, 0), bevel=0.0)
    m.blob('Chest', 'skull', add(bp, (0, -0.35, 0.0)), (0.3, 0.18, 0.3), u=7, v=5)
    m.box('Chest', 'skull', add(bp, (0, -0.4, -0.25)), (0.3, 0.12, 0.12), bevel=0.02)
    for e in (-1, 1):
        m.blob('Chest', 'glow', add(bp, (0.11 * e, -0.5, 0.03)), (0.07, 0.04, 0.07), u=5, v=3)
        m.spike('Chest', 'iron', add(bp, (0.75 * bW * e, -0.3, 0.3)), (0.5 * e, -1, 0.2), 0.5, 0.18, 0.14, snap=False)
    cp = c.body_pt(1.25, 3.7)
    m.box('Hips', 'iron', cp, (2.2 * bW * gk, 1.4, 0.18), rot=(-12, 0, 0), bevel=0.06)
    for i in range(4):
        m.spike('Hips', 'iron', add(cp, (0, -0.45 + 0.32 * i, 0.12 - 0.07 * i)), (0, 0.5, 1), 0.38, 0.16, 0.14, snap=False)
    # ---- saddle: crimson-lined, with a tattered blanket and a high cantle ----
    seat = c.seat
    m.box('Hips', 'leather', add(seat, (0, 0.05, -0.12)), (1.5 * k, 1.6 * k, 0.24), bevel=0.06)
    m.box('Hips', 'leather', add(seat, (0, 0.75 * k, 0.12)), (1.1 * k, 0.18, 0.5 * k), rot=(-15, 0, 0), bevel=0.04)   # cantle
    m.box('Hips', 'leather', add(seat, (0, -0.7 * k, 0.08)), (0.5 * k, 0.2, 0.42 * k), rot=(15, 0, 0), bevel=0.04)    # pommel
    m.blob('Hips', 'gold', add(seat, (0, -0.78 * k, 0.32 * k)), (0.12, 0.1, 0.1), u=6, v=4)
    for side, s in c.SIDES:
        for j in range(5):   # ragged blanket hanging down each flank
            y0 = seat[1] - 0.8 * k + 0.4 * k * j
            top = (1.0 * bW * gk * s, y0, seat[2] - 0.35)
            bot = (1.55 * bW * gk * s, y0 + 0.05, seat[2] - 1.25 - 0.22 * (j % 2))
            m.loft('Hips' if y0 > 0 else 'Chest', 'cloth', [top, lerp(top, bot, 0.5), bot],
                   [(0.05, 0.22 * k), (0.05, 0.22 * k), (0.04, 0.1 * k)], sides=4, steps=1, smooth=False)
        m.box('Hips', 'gold', (1.55 * bW * gk * s, seat[1], seat[2] - 1.0), (0.05, 1.9 * k, 0.08), bevel=0.0)
    # ---- chain reins from the bridle to the rider's left hand ----
    for side, s in c.SIDES:
        a, b = c.H(0.48 * s, -1.75, -0.2), R(0.45 * s, -0.55, 1.05)
        for i in range(7):
            p = lerp(a, b, (i + 0.5) / 7)
            p = add(p, (0, 0, -0.25 * math.sin(math.pi * (i + 0.5) / 7)))
            m.box('Neck' if i < 4 else 'Chest', 'iron', p, (0.06, 0.16, 0.06) if i % 2 else (0.14, 0.06, 0.06), bevel=0.0)
    # ---- hooves wreathed in ghost fire, iron shod ----
    for end, y, xk in (('F', c.yF, 1.15), ('B', c.yB, 1.2)):
        for side, s in c.SIDES:
            x = xk * bW * s
            fy = y - (0.25 if end == 'F' else 0.4) * c.T
            ring = [(x + math.cos(TAU * i / 10) * 0.56 * c.T, fy + math.sin(TAU * i / 10) * 0.64 * c.T, 0.5 * c.T) for i in range(11)]
            m.loft(f'Foot{end}{side}', 'iron', ring, [(0.08, 0.1)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
            for i in range(5):
                a = TAU * i / 5 + 0.3
                flame(m, f'Foot{end}{side}', (x + math.cos(a) * 0.5 * c.T, fy + math.sin(a) * 0.55 * c.T, 0.55 * c.T),
                      (math.cos(a) * 0.4, math.sin(a) * 0.4 + 0.4, 1), 0.65 * c.T, 0.22 * c.T, core=i % 2 == 0)
            m.socket(f'Hoof{end}{side}', f'Foot{end}{side}', (x, fy, 0.5 * c.T))
    # ---- ghost-fire ribs glowing through the hide ----
    for side, s in c.SIDES:
        for j, ya in enumerate((-0.95, -0.6, -0.25)):
            pts = []
            for q in range(4):
                za = 2.95 - 0.35 * q
                p = c.body_pt(ya + 0.05 * q, za)
                rw = 1.64 * bW * gk * math.sqrt(max(0.05, 1 - ((za - 2.45) / 1.36) ** 2)) * 1.01
                pts.append((rw * s, p[1], p[2]))
            m.loft('Chest', 'glow', pts, [(0.05, 0.05)] * 4, sides=4, steps=1, smooth=False)

    rider(c)


class SizeK:
    """wraps the model so part SIZES scale by k (positions already come scaled from c.R)"""
    def __init__(self, m, k):
        self.m, self.k = m, k

    def box(self, bone, color, center, size, **kw):
        if 'bevel' in kw:
            kw['bevel'] *= self.k
        self.m.box(bone, color, center, tuple(x * self.k for x in size), **kw)

    def blob(self, bone, color, center, radii, **kw):
        self.m.blob(bone, color, center, tuple(x * self.k for x in radii), **kw)

    def loft(self, bone, color, points, radii, **kw):
        self.m.loft(bone, color, points, [tuple(x * self.k for x in r) for r in radii], **kw)

    def spike(self, bone, color, base, d, length, width, depth=None, **kw):
        self.m.spike(bone, color, base, d, length * self.k, width * self.k, None if depth is None else depth * self.k, **kw)

    def socket(self, *a):
        self.m.socket(*a)


def rider(c):
    m, k, R = c.m, c.k, c.R
    mk = SizeK(m, k)
    # pelvis, torso in a long buttoned coat, a belt and a bandolier
    mk.box('RiderHips', 'coat', R(0, 0.05, 0.4), (0.95, 0.7, 0.6), bevel=0.1)
    mk.box('RiderChest', 'coat', R(0, 0.0, 1.25), (1.05, 0.72, 1.1), bevel=0.14, taper=dict(axis='z', end=-1, scale=(0.85, 0.9)))
    mk.box('RiderChest', 'vest', R(0, -0.33, 1.2), (0.4, 0.12, 1.0), bevel=0.03)          # crimson waistcoat
    for i in range(4):
        mk.blob('RiderChest', 'gold', R(0, -0.4, 0.85 + 0.22 * i), (0.05, 0.03, 0.05), u=5, v=3)
    mk.box('RiderHips', 'leather', R(0, 0.0, 0.72), (1.0, 0.76, 0.14), bevel=0.02)
    mk.box('RiderHips', 'gold', R(0, -0.4, 0.72), (0.2, 0.06, 0.16), bevel=0.0)
    mk.box('RiderChest', 'leather', R(0, -0.02, 1.25), (0.12, 0.8, 1.35), rot=(0, 38, 0), bevel=0.0)  # bandolier
    for i in range(4):
        mk.box('RiderChest', 'skull', R(0.12 - 0.17 * i, -0.38, 1.6 - 0.2 * i), (0.08, 0.06, 0.1), bevel=0.0)
    # coat lapels and coat tails hanging down over the horse's flanks in ragged strips
    for side, s in c.SIDES:
        mk.box('RiderChest', 'coat2', R(0.25 * s, -0.36, 1.45), (0.22, 0.08, 0.6), rot=(0, 20 * s, 0), bevel=0.02)
        for j in range(4):
            y0 = -0.3 + 0.25 * j
            top = R(0.4 * s, y0, 0.45)
            bot = R(0.75 * s, y0 + 0.1, -0.55 - 0.2 * (j % 2))
            mk.loft('RiderHips', 'coat', [top, lerp(top, bot, 0.5), bot], [(0.05, 0.17), (0.05, 0.17), (0.04, 0.06)], sides=4, steps=1, smooth=False)
    # the high spiked collar, and ghost fire pouring out where the head should be
    for i in range(10):
        a = TAU * i / 10
        p = R(math.cos(a) * 0.4, math.sin(a) * 0.32, 1.85)
        mk.spike('RiderChest', 'coat2', p, (math.cos(a) * 0.4, math.sin(a) * 0.4 + 0.25, 1), (0.5 if math.sin(a) > -0.3 else 0.3), 0.22, 0.05)
    mk.blob('RiderChest', 'dark', R(0, 0, 1.88), (0.28, 0.24, 0.06), u=7, v=4)
    mk.blob('RiderChest', 'glow', R(0, 0, 1.9), (0.18, 0.15, 0.05), u=6, v=4)
    for i, (dx, dy, L) in enumerate(((0, 0, 1.0), (0.12, 0.08, 0.7), (-0.12, 0.1, 0.65), (0.0, -0.12, 0.55))):
        flame(mk, 'RiderChest', R(dx, dy, 1.9), (dx, dy + 0.2, 1), L, 0.24, core=i < 2)
    mk.socket('NeckFire', 'RiderChest', R(0, 0.05, 2.3))
    # the cape: a jagged sheet streaming back off the shoulders
    for j in range(5):
        x = -0.6 + 0.3 * j
        top = R(x, 0.36, 1.75)
        mid = R(x * 1.25, 0.95, 0.85)
        bot = R(x * 1.45, 1.55 + 0.15 * (j % 2), 0.15 - 0.25 * (j % 2))
        mk.loft('RiderChest', 'cape', [top, mid, bot], [(0.17, 0.05), (0.2, 0.05), (0.05, 0.04)], sides=4, steps=2, smooth=False, up=(0, 1, 0))
        mk.loft('RiderChest', 'cloth', [add(top, (0, 0.04, -0.02)), add(mid, (0, 0.04, -0.02)), add(bot, (0, 0.04, 0))],
               [(0.13, 0.03), (0.15, 0.03), (0.04, 0.03)], sides=4, steps=2, smooth=False, up=(0, 1, 0))   # crimson lining
    # shoulders: tattered iron pauldrons
    for side, s in c.SIDES:
        sh = R(0.62 * s, 0.0, 1.68)
        mk.blob('RiderChest', 'iron', sh, (0.32, 0.32, 0.22), u=7, v=5)
        for i in range(3):
            mk.spike('RiderChest', 'iron', add(sh, (0.1 * s, -0.12 + 0.12 * i, 0.12)), (0.6 * s, 0, 1), 0.3, 0.1, 0.08, snap=False)
    # legs astride the horse, tall boots in iron stirrups
    gk = c.spec['body']['girth']
    for side, s in c.SIDES:
        hip = R(0.35 * s, -0.05, 0.25)
        knee = (1.25 * c.bW * gk * s, hip[1] - 0.45 * k, c.seat[2] - 0.55 * k)
        ank = (1.35 * c.bW * gk * s, hip[1] - 0.3 * k, c.seat[2] - 1.55 * k)
        mk.loft('RiderHips', 'trousers', [hip, knee], [(0.2, 0.2), (0.17, 0.17)], sides=6, steps=1, smooth=False)
        mk.loft('RiderHips', 'boot', [knee, ank], [(0.2, 0.2), (0.16, 0.16)], sides=6, steps=1, smooth=False)
        mk.box('RiderHips', 'boot', add(knee, (0, -0.06, 0.1)), (0.34, 0.3, 0.3), bevel=0.04)       # boot cuff
        mk.box('RiderHips', 'boot', add(ank, (0, -0.15, -0.1)), (0.3, 0.6, 0.22), bevel=0.05)
        mk.spike('RiderHips', 'gold', add(ank, (0, 0.18, -0.05)), (0, 1, 0), 0.18, 0.1, snap=False)  # spur
        mk.loft('RiderHips', 'iron', [add(ank, (0, -0.15, 0.4)), add(ank, (0, -0.15, -0.25))], [(0.03, 0.03)] * 2, sides=4, steps=1, smooth=False)
    # arms in coat sleeves, iron gauntlets
    for side, (sh, el, wr) in (('L', c.armL), ('R', c.armR)):
        bones_ = [f'RiderArm{side}', f'RiderFore{side}']
        mk.loft(bones_, 'coat', [sh, el, wr], [(0.27, 0.27), (0.23, 0.23), (0.19, 0.19)], sides=6, steps=2, smooth=False)
        mk.loft(bones_[1], 'cloth', [lerp(el, wr, 0.65), lerp(el, wr, 0.75)], [(0.19, 0.19)] * 2, sides=6, steps=1, smooth=False)  # cuff
        mk.blob(bones_[1], 'iron', wr, (0.17, 0.17, 0.17), u=6, v=4)
        for q in range(2):
            mk.spike(bones_[1], 'iron', lerp(el, wr, 0.4 + 0.2 * q), (1 if side == 'L' else -1, 0.3, 0.2), 0.18, 0.08, snap=False)
    # LEFT: its own head held high - a grinning jack-o'-lantern blazing from inside
    wr = c.armL[2]
    hc = add(wr, (0.05, -0.1, 0.45 * k))
    hr = (0.55 * k, 0.5 * k, 0.45 * k)
    m.blob('RiderForeL', 'pumpkin', hc, hr, u=12, v=8)

    def hs(az, el, out=0.0):
        x, y, z = math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)
        return (hc[0] + x * (hr[0] + out), hc[1] + y * (hr[1] + out), hc[2] + z * (hr[2] + out))
    for i in range(10):
        az = (i + 0.5) * TAU / 10
        if abs(((az + math.pi) % TAU) - math.pi) < 0.6:
            continue
        pts = [hs(az, el, 0.01) for el in (-1.2, -0.6, 0.0, 0.6, 1.2)]
        m.loft('RiderForeL', 'rib', pts, [(0.035 * k, 0.05 * k)] * 5, sides=4, steps=2, smooth=False)
    for side, s in c.SIDES:
        cc = hs(0.38 * s, 0.25, -0.02)
        tri(m, 'RiderForeL', 'dark', cc, 0.3 * k, 0.28 * k, 25 * s, 0.1 * k)
        tri(m, 'RiderForeL', 'fire', add(cc, (0, -0.02, 0)), 0.22 * k, 0.2 * k, 25 * s, 0.09 * k)
        tri(m, 'RiderForeL', 'flame', add(cc, (0, -0.035, -0.02 * k)), 0.1 * k, 0.09 * k, 25 * s, 0.07 * k)
    for q in range(9):   # a wide, cruel grin
        f = (q - 4) / 4
        cc = hs(0.65 * f, -0.3 + 0.2 * f * f, -0.01)
        m.box('RiderForeL', 'dark', cc, (0.13 * k, 0.08 * k, 0.1 * k), bevel=0.0)
        if q % 2:
            tri(m, 'RiderForeL', 'pumpkin', add(cc, (0, -0.03, -0.04 * k)), 0.08 * k, 0.1 * k, 180, 0.05 * k)
    m.blob('RiderForeL', 'fire', hs(0, -0.4, -0.12), (0.35 * k, 0.15 * k, 0.1 * k), u=7, v=4)
    m.loft('RiderForeL', 'stem', [hs(0, 1.4, 0), add(hs(0, 1.4, 0), (0.08 * k, 0.12 * k, 0.25 * k))], [(0.07 * k,) * 2, (0.04 * k,) * 2],
           sides=5, steps=1, smooth=False)
    for i, (dx, dy, L) in enumerate(((0.12, 0, 0.6), (-0.1, 0.06, 0.45), (0.02, -0.1, 0.4))):
        flame(m, 'RiderForeL', add(hs(0, 1.3, 0), (dx * k, dy * k, 0)), (dx, dy + 0.15, 1), L * k, 0.16 * k, core=i == 0, col='fire', col2='flame')
    m.socket('PumpkinHead', 'RiderForeL', add(hc, (0, 0, 0.5 * k)))
    # RIGHT: a long jagged sword, burning edge, skull pommel
    wr = c.armR[2]
    base = add(wr, (0, -0.05, 0.12))
    d = (-0.15, -0.55, 0.82)
    n = math.sqrt(sum(x * x for x in d))
    d = tuple(x / n for x in d)
    Lb = 2.6 * k
    tipp = add(base, tuple(x * Lb for x in d))
    m.loft('RiderForeR', 'leather', [add(base, tuple(-x * 0.35 for x in d)), add(base, tuple(x * 0.1 for x in d))], [(0.06, 0.06)] * 2, sides=6, steps=1, smooth=False)
    m.blob('RiderForeR', 'skull', add(base, tuple(-x * 0.42 for x in d)), (0.1, 0.1, 0.1), u=6, v=4)
    guard = add(base, tuple(x * 0.12 for x in d))
    m.box('RiderForeR', 'gold', guard, (0.65 * k, 0.12, 0.12), bevel=0.02)
    for e in (-1, 1):
        m.spike('RiderForeR', 'gold', add(guard, (0.32 * k * e, 0, 0)), (e, -0.2, 0.5), 0.2, 0.08, snap=False)
    perp = (0.3, d[2], -d[1])   # blade faces sideways so it reads in profile
    lead_, trail_, ga, gb = [], [], [], []
    for i in range(7):
        f = i / 6
        p = lerp(guard, tipp, f)
        w = (0.24 - 0.17 * f) * k * (1.0 if i % 2 == 0 else 0.8)    # jagged, serrated profile
        lead_.append(add(p, tuple(w * q for q in perp)))
        trail_.append(add(p, tuple(-w * q for q in perp)))
        ga.append(add(p, tuple(-(w + 0.01) * q for q in perp)))
        gb.append(add(p, tuple(-(w + 0.09 * k) * q for q in perp)))
    m.strip('RiderForeR', 'blade', lead_, trail_, thickness=0.07)
    m.strip('RiderForeR', 'glow', ga, gb, thickness=0.08)
    m.loft('RiderForeR', 'glow2', [lerp(guard, tipp, 0.1), lerp(guard, tipp, 0.75)], [(0.02, 0.02)] * 2, sides=4, steps=1, smooth=False)  # fuller
    m.socket('BladeBase', 'RiderForeR', lerp(guard, tipp, 0.15))
    m.socket('BladeTip', 'RiderForeR', tipp)


def pose(c, clip, t, p):
    """the rider: sways with the horse, brandishes the head and sword"""
    sway = 0
    hl, hr, fl, fr, lean = 0, 0, 0, 0, 0
    if clip == 'Idle':
        sway = 3 * math.sin(TAU * t)
        hl = 6 * math.sin(TAU * t)
        hr = 4 * math.sin(TAU * t + 1)
    elif clip == 'Walk':
        sway = 4 * math.sin(TAU * 2 * t)
        hl = 5 * math.sin(TAU * 2 * t)
        lean = 6
    elif clip == 'Run':
        lean = 18 + 5 * math.sin(TAU * 2 * t)
        hl = -15
        hr = -35
        fr = -20
    elif clip == 'Sleep':
        lean = 28
        hl, hr, fl, fr = 50, 20, 30, 10
    elif clip == 'Roar':   # thrusts the burning head skyward and raises the sword
        e = envelope(t, 0.2, 0.8)
        hl = -40 * e
        hr = -100 * e
        fr = -30 * e
        lean = -12 * e
        sway = 6 * math.sin(TAU * 6 * t) * e
    elif clip == 'Attack':  # sword hauled back, then a cleaving overhead slash
        w = envelope(t, 0.3, 0.32, 0.4)
        s_ = envelope(t, 0.32, 0.45, 0.85)
        hr = -130 * w + 60 * s_
        fr = -40 * w + 20 * s_
        lean = -8 * w + 18 * s_
    else:   # Happy: twirls the sword overhead and holds the head up
        e = envelope(t, 0.1, 0.85)
        hl = -35 * e
        hr = -140 * e
        sway = 25 * math.sin(TAU * 2 * t) * e
    p['RiderHips'] = ((lean, 0, sway), (0, 0, 0))
    p['RiderChest'] = ((lean * 0.3, sway * 0.5, 0), (0, 0, 0))
    p['RiderArmL'] = ((hl, 0, 0), (0, 0, 0))
    p['RiderForeL'] = ((fl, 0, 0), (0, 0, 0))
    p['RiderArmR'] = ((hr, 0, 0), (0, 0, 0))
    p['RiderForeR'] = ((fr, 0, 0), (0, 0, 0))


build(dict(
    sides=6,
    kneePlates='iron',
    name='HeadlessHorseman',
    palette={
        'body': '#2c2840', 'body2': ('#463e62', True, True), 'belly': '#3a3452', 'bone': ('#e6dece', False, True),
        'skull': ('#ece3cf', False, True), 'iron': ('#3a3846', False, True), 'gold': ('#d8a838', False, True),
        'leather': ('#3a2418', True, True), 'cloth': ('#7a1420', True, True), 'cape': ('#121018', True, True),
        'coat': ('#2a2634', True, True), 'coat2': ('#3c3650', True, True), 'vest': ('#8a1a26', True, True),
        'trousers': '#2a2632', 'boot': ('#140e0c', False, True),
        'glow': ('#a25cff', False), 'glow2': ('#e8d4ff', False), 'fire': ('#ff8a1a', False), 'flame': ('#ffe27a', False),
        'pumpkin': '#e8641c', 'rib': ('#3a160c', False, True), 'stem': ('#2a1a10', True, True),
        'blade': ('#8a8896', False, True), 'dark': ('#06040a', False), 'nose': ('#0a080e', False),
        'foot': '#2c2840', 'claw': ('#3a3846', False), 'mouth': '#2a0a20', 'tongue': '#a82a5a',
        'eye_dark': ('#06040a', False), 'iris': ('#c88cff', False), 'eye_glint': ('#ffffff', False),
    },
    body=dict(legL=1.45, legT=0.72, bL=1.2, bW=0.82, bH=0.9, girth=0.92, head=0.95, neck=1.35, neckUp=2.3,
              tail=0.6, tailDroop=1.6, eye=0.9),
    neckRadius=0.8,
    gait=dict(stride=1.3),
    bones=bones, head=head, decor=decor, pose=pose,
))
