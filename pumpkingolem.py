"""Jack-o'-Lantern Golem (PumpkinGolem) - Mythic Haunted monster (Haunted Pumpkin featured egg): a
hulking golem of stacked pumpkins and graveyard roots. Its chest is one huge cracked pumpkin bound in
riveted iron bands, a molten core blazing through a carved hole; its head is a jack-o'-lantern hunched
low between the shoulders, fire pouring out of its carved eyes and grin and roaring up through the
broken crown. Pumpkin pauldrons rimmed with iron spikes vent flame, the arms are twisted bundles of
mossy roots ending in giant gnarled fists (the right one wrapped in chain), tombstones are lashed over
its knees and its feet are spreading root stumps. Thorned vines and a broken iron grave cross jut from
its back. Faces -Y.
    blender -b --python pumpkingolem.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Face, ShoulderL/R (flame vents), Core, HandL/R."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, ik, envelope, smooth01, add, TAU

m, st, OUT = setup('PumpkinGolem', {
    'pumpkin': '#e8641c', 'pumpkin2': ('#b8401a', True, True), 'rib': ('#2e1008', False, True), 'dark': ('#120402', False),
    'glow': ('#ffd23a', False), 'glow2': ('#ff6a12', False), 'fire': ('#ff9a1a', False), 'flame': ('#ffe27a', False),
    'stem': ('#2a1a10', True, True), 'thorn': ('#0e0809', False), 'leaf': ('#24401c', True, True),
    'bark': ('#553722', True, True), 'bark2': ('#774c2a', True, True), 'moss': ('#3e5a24', True, False),
    'iron': ('#34323c', False, True), 'rivet': ('#6a6872', False), 'stone': ('#6e6a74', True, True), 'stone2': ('#4e4a54', False),
    'rope': ('#5a4428', True, True),
    'eye_dark': ('#120402', False), 'iris': ('#ffd23a', False), 'eye_glint': ('#ffffff', False),
}, {'Child': dict(head=1.3), 'Teen': dict(head=1.12)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))

CC, CR = (0, 0.05, 3.15), (1.45, 1.2, 1.12)                 # chest pumpkin
HC = (0, -0.6, 4.7 + 0.1 * (h - 1))                        # head pumpkin, hunched low and forward
HR = (0.82 * h, 0.74 * h, 0.64 * h)


def surf(C, R, az, el, out=0.0):
    """point on a pumpkin's surface: azimuth az (0 = front, -Y), elevation el (radians)"""
    x, y, z = math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)
    return (C[0] + x * (R[0] + out), C[1] + y * (R[1] + out), C[2] + z * (R[2] + out))


def pumpkin(bone, C, R, color, ribs=10, clear=0.0, rib_w=0.08):
    """a ribbed pumpkin: the body plus dark outlined ribs pole to pole (none within `clear` of the front)"""
    m.blob(bone, color, C, R, u=12, v=8)
    for i in range(ribs):
        az = (i + 0.5) * TAU / ribs
        if abs(((az + math.pi) % TAU) - math.pi) < clear:
            continue
        pts = [surf(C, R, az, el, 0.02) for el in (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25)]
        m.loft(bone, 'rib', pts, [(rib_w, rib_w * 1.4)] * len(pts), sides=5, steps=2, smooth=False)


def tri(bone, color, center, w, hgt, slant, depth):
    """a carved triangle facing -Y: flat bottom, point on top, tipped by `slant` degrees"""
    m.box(bone, color, center, (w, depth, hgt), rot=(0, slant, 0), bevel=0.0, taper=dict(axis='z', end=1, scale=(0.05, 1)))


def flame(bone, base, d, length, width, core=True):
    m.spike(bone, 'fire', base, d, length, width, width * 0.45, snap=False)
    if core:
        m.spike(bone, 'flame', base, d, length * 0.6, width * 0.5, width * 0.25, snap=False)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ---------------- rig ----------------
ARM, LEG = {}, {}
for side, s in SIDES:
    sh = (1.5 * s, 0.1, 3.75)
    el = (2.05 * s, -0.05, 2.75)
    wr = (2.15 * s, -0.4, 1.7)
    hd = (2.15 * s, -0.6, 1.05)
    ARM[side] = (sh, el, wr, hd)
    LEG[side] = ((0.7 * s, 0.2, 2.05), (0.85 * s, -0.2, 1.2), (0.85 * s, 0.2, 0.4), (0.85 * s, -0.45, 0.08))

m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0.15, 1.95), (0, 0.1, 2.5), 'MonsterRoot')
m.bone('Chest', (0, 0.1, 2.5), (0, 0.05, 3.9), 'Hips')
m.bone('Head', (0, 0.0, 3.95), (0, -0.6, 4.9), 'Chest')
m.bone('Jaw', add(HC, (0, -0.3 * h, -0.25 * h)), add(HC, (0, -0.85 * h, -0.4 * h)), 'Head')
for side, s in SIDES:
    sh, el, wr, hd = ARM[side]
    m.bone(f'Shoulder{side}', (0.9 * s, 0.1, 3.8), sh, 'Chest')
    m.bone(f'Arm{side}', sh, el, f'Shoulder{side}')
    m.bone(f'Fore{side}', el, wr, f'Arm{side}')
    m.bone(f'Hand{side}', wr, hd, f'Fore{side}')
    hip, knee, ank, toe = LEG[side]
    m.bone(f'Thigh{side}', hip, knee, 'Hips')
    m.bone(f'Shin{side}', knee, ank, f'Thigh{side}')
    m.bone(f'Foot{side}', ank, toe, f'Shin{side}')

# ---------------- chest: the great cracked pumpkin ----------------
pumpkin('Chest', CC, CR, 'pumpkin', ribs=10, clear=0.0, rib_w=0.055)
# molten fissures branching across the chest and back
for az0, el0, n, dz in ((0.55, 0.7, 6, -0.28), (-0.6, 0.55, 5, -0.3), (2.7, 0.9, 7, -0.3), (3.6, 0.6, 6, -0.28), (-2.2, 0.3, 4, -0.3)):
    pts = [surf(CC, CR, az0 + 0.12 * ((k % 2) * 2 - 1) + 0.04 * k, el0 + dz * k, 0.035) for k in range(n)]
    m.loft('Chest', 'glow2', pts, [(0.06, 0.06)] * n, sides=4, steps=1, smooth=False)
    m.loft('Chest', 'glow', pts[1:-1], [(0.025, 0.025)] * (n - 2), sides=4, steps=1, smooth=False)
# carved diamond hole in the breast, the molten core blazing inside
core = surf(CC, CR, 0.0, 0.12, -0.12)
m.box('Chest', 'dark', core, (0.72, 0.2, 0.72), rot=(0, 45, 0), bevel=0.0)
m.box('Chest', 'rib', add(core, (0, 0.02, 0)), (0.86, 0.16, 0.86), rot=(0, 45, 0), bevel=0.02)
m.blob('Chest', 'glow2', add(core, (0, -0.06, 0)), (0.32, 0.12, 0.32), u=8, v=5)
m.blob('Chest', 'flame', add(core, (0, -0.12, 0)), (0.17, 0.08, 0.17), u=6, v=4)
for k in range(4):   # jagged carved teeth round the hole
    a = math.radians(45 + 90 * k)
    m.spike('Chest', 'pumpkin2', add(core, (math.cos(a) * 0.36, -0.12, math.sin(a) * 0.36)), (-math.cos(a), -0.2, -math.sin(a)), 0.18, 0.12, 0.06, snap=False)
m.socket('Core', 'Chest', add(core, (0, -0.25, 0)))
# riveted iron bands binding the pumpkin together
for el in (0.62, -0.55):
    ring = [surf(CC, CR, TAU * i / 20, el, 0.05) for i in range(21)]
    m.loft('Chest', 'iron', ring, [(0.13, 0.08)] * 21, sides=4, steps=1, smooth=False, cap_round=0.0)
    for i in range(0, 20, 2):
        if el > 0 and abs(((TAU * i / 20 + math.pi) % TAU) - math.pi) < 0.3:
            continue
        m.box('Chest', 'rivet', surf(CC, CR, TAU * i / 20, el, 0.12), (0.08, 0.08, 0.08), bevel=0.0)
for side, s in SIDES:   # a vertical strap over each pec joining the bands
    pts = [surf(CC, CR, 0.62 * s, el, 0.05) for el in (0.62, 0.3, 0.0, -0.3, -0.55)]
    m.loft('Chest', 'iron', pts, [(0.1, 0.06)] * 5, sides=4, steps=1, smooth=False)
# heavy rope belt with hanging lanterns and a broken chain
belt = [surf(CC, CR, TAU * i / 18, -0.92, 0.04) for i in range(19)]
m.loft('Hips', 'rope', belt, [(0.12, 0.12)] * 19, sides=5, steps=1, smooth=False, cap_round=0.0)
for az in (0.9, -1.1, 2.6):
    top = surf(CC, CR, az, -0.95, 0.12)
    lc = add(top, (0, 0, -0.42))
    m.loft('Hips', 'iron', [top, add(top, (0, 0, -0.18))], [(0.02, 0.02)] * 2, sides=4, steps=1, smooth=False)
    m.box('Hips', 'iron', add(lc, (0, 0, 0.16)), (0.26, 0.26, 0.05), bevel=0.0)
    m.box('Hips', 'iron', add(lc, (0, 0, -0.16)), (0.26, 0.26, 0.05), bevel=0.0)
    for cx, cy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        m.box('Hips', 'iron', add(lc, (0.11 * cx, 0.11 * cy, 0)), (0.035, 0.035, 0.32), bevel=0.0)
    m.blob('Hips', 'glow', lc, (0.09, 0.09, 0.12), u=6, v=4)
    m.spike('Hips', 'flame', add(lc, (0, 0, -0.05)), (0, 0, 1), 0.16, 0.07, snap=False)
# back: a broken iron grave cross and thorned vines rising off the shoulders
bc = surf(CC, CR, math.pi + 0.35, 0.45, 0.0)
m.box('Chest', 'iron', add(bc, (0.15, 0.45, 0.7)), (0.16, 0.16, 1.7), rot=(-22, 12, 0), bevel=0.02)
m.box('Chest', 'iron', add(bc, (0.24, 0.6, 1.05)), (0.8, 0.14, 0.14), rot=(-22, 12, 0), bevel=0.02)
m.spike('Chest', 'iron', add(bc, (0.42, 0.6, 1.08)), (1, 0.1, 0.05), 0.25, 0.14, 0.12, snap=False)   # snapped arm
for side, s in SIDES:
    base = surf(CC, CR, (math.pi - 0.7) * s, 0.75, 0.0)
    pts = [base]
    for k in range(1, 7):
        a = k * 0.8
        pts.append(add(base, (s * (0.12 * k + 0.12 * math.cos(a)), 0.18 * k + 0.12 * math.sin(a), 0.3 * k - 0.035 * k * k)))
    m.loft('Chest', 'leaf', pts, [(max(0.03, 0.12 - 0.015 * k),) * 2 for k in range(7)], sides=5, steps=2, smooth=False)
    for k in (1, 3, 5):
        m.spike('Chest', 'thorn', pts[k], (s, 0.3 * (k % 3 - 1), 0.4), 0.22, 0.07, snap=False)
    m.spike('Chest', 'leaf', pts[2], (s * 0.6, 0.6, 0.4), 0.45, 0.24, 0.04)
    m.spike('Chest', 'leaf', pts[4], (-s * 0.2, 0.8, 0.5), 0.38, 0.2, 0.04)
# spine of jagged pumpkin-shell plates
for i in range(5):
    p = surf(CC, CR, math.pi, 0.9 - 0.4 * i, 0.0)
    m.spike('Chest', 'pumpkin2', p, (0, 1, 0.5 - 0.15 * i), 0.5 - 0.05 * i, 0.32, 0.12)

# ---------------- head: a jack-o'-lantern blazing from inside ----------------
pumpkin('Head', HC, HR, 'pumpkin', ribs=10, clear=0.6, rib_w=0.045 * h)
for side, s in SIDES:
    c = surf(HC, HR, 0.38 * s, 0.25, -0.02)
    tri('Head', 'dark', c, 0.44 * h, 0.4 * h, 25 * s, 0.14 * h)
    tri('Head', 'glow', add(c, (0, -0.03, 0)), 0.32 * h, 0.3 * h, 25 * s, 0.12 * h)
    tri('Head', 'flame', add(c, (0, -0.05, -0.04 * h)), 0.14 * h, 0.13 * h, 25 * s, 0.1 * h)
    m.box('Head', 'rib', surf(HC, HR, 0.38 * s, 0.52, 0.03), (0.46 * h, 0.12 * h, 0.1 * h), rot=(0, -30 * s, 0), bevel=0.02 * h)   # brow
    # fire streaming up out of each eye
    flame('Head', surf(HC, HR, 0.42 * s, 0.4, 0.02), (0.15 * s, 0.25, 1), 0.55 * h, 0.16 * h)
    flame('Head', surf(HC, HR, 0.28 * s, 0.38, 0.02), (0.05 * s, 0.35, 1), 0.38 * h, 0.12 * h, core=False)
tri('Head', 'dark', surf(HC, HR, 0, 0.0, -0.02), 0.2 * h, 0.2 * h, 0, 0.12 * h)
tri('Head', 'glow2', add(surf(HC, HR, 0, 0.0, -0.02), (0, -0.03, 0)), 0.12 * h, 0.12 * h, 0, 0.1 * h)
# the jagged grin: a wide carved gash with fangs, fire in it
for k in range(9):
    f = (k - 4) / 4
    c = surf(HC, HR, 0.62 * f, -0.3 + 0.12 * f * f, -0.01)
    m.box('Head', 'dark', add(c, (0, 0, 0.02)), (0.2 * h, 0.12 * h, 0.15 * h), bevel=0.0)
    if k % 2 == 1:
        tri('Head', 'pumpkin', add(c, (0, -0.04, -0.07 * h)), 0.13 * h, 0.17 * h, 180, 0.08 * h)
m.blob('Head', 'glow', surf(HC, HR, 0, -0.42, -0.2), (0.6 * h, 0.25 * h, 0.16 * h), u=8, v=5)
m.socket('Face', 'Head', surf(HC, HR, 0, 0.0, 0.3))
jaw_pts = [surf(HC, HR, az, -0.66, 0.0) for az in (-0.8, -0.4, 0.0, 0.4, 0.8)]
m.loft('Jaw', 'pumpkin', jaw_pts, [(0.18 * h, 0.14 * h)] * 5, sides=6, steps=2, smooth=False)
for k in range(5):
    f = (k - 2) / 2
    tri('Jaw', 'pumpkin', add(surf(HC, HR, 0.5 * f, -0.52, 0.0), (0, -0.05, 0.0)), 0.13 * h, 0.17 * h, 0, 0.08 * h)
# broken crown: the top is split open and fire roars up out of it round a snapped stem
for i in range(9):
    az = i * TAU / 9
    base = surf(HC, HR, az, 1.0, -0.02)
    m.spike('Head', 'pumpkin2', base, (math.sin(az) * 0.6, -math.cos(az) * 0.6, 1), (0.32 + 0.12 * (i % 2)) * h, 0.24 * h, 0.08 * h)
m.blob('Head', 'glow2', surf(HC, HR, 0, 1.4, -0.08), (0.42 * h, 0.38 * h, 0.08 * h), u=8, v=4)
for i, (ox, oy, L) in enumerate(((0, 0, 1.0), (0.22, 0.1, 0.7), (-0.22, 0.12, 0.75), (0.08, -0.22, 0.6), (-0.1, 0.28, 0.55))):
    flame('Head', add(surf(HC, HR, 0, 1.45, 0.0), (ox * h, oy * h, 0)), (ox * 0.8, oy * 0.8 + 0.1, 1), L * h, 0.22 * h, core=i < 3)
m.loft('Head', 'stem', [add(surf(HC, HR, 0, 1.4, 0), (0.15 * h, 0.2 * h, 0)), add(surf(HC, HR, 0, 1.4, 0), (0.3 * h, 0.35 * h, 0.35 * h))],
       [(0.12 * h, 0.12 * h), (0.07 * h, 0.07 * h)], sides=5, steps=1, smooth=False)

# ---------------- shoulders: spiked pumpkin pauldrons venting flame ----------------
for side, s in SIDES:
    sh = ARM[side][0]
    pc = add(sh, (0.05 * s, 0.05, 0.25))
    pr = (0.68, 0.62, 0.52)
    pumpkin(f'Shoulder{side}', pc, pr, 'pumpkin', ribs=8, rib_w=0.04)
    for az in (0.5, 1.4, 2.4):
        tri(f'Shoulder{side}', 'glow', surf(pc, pr, az * s, 0.15, 0.0), 0.14, 0.14, 0, 0.1)
    rim = [surf(pc, pr, TAU * i / 14, -0.35, 0.06) for i in range(15)]
    m.loft(f'Shoulder{side}', 'iron', rim, [(0.08, 0.06)] * 15, sides=4, steps=1, smooth=False, cap_round=0.0)
    for i in range(0, 14, 2):
        a = TAU * i / 14
        m.spike(f'Shoulder{side}', 'iron', surf(pc, pr, a, -0.3, 0.08), (math.sin(a), -math.cos(a), 0.35), 0.3, 0.1, 0.09, snap=False)
    top = surf(pc, pr, 0, 1.4, -0.02)
    m.blob(f'Shoulder{side}', 'dark', top, (0.22, 0.2, 0.05), u=7, v=4)
    for k, (dx, dy, L) in enumerate(((0, 0, 0.75), (0.15, 0.08, 0.5), (-0.12, 0.12, 0.45))):
        flame(f'Shoulder{side}', add(top, (dx, dy, 0)), (dx + 0.15 * s, dy + 0.15, 1), L, 0.18, core=k == 0)
    m.socket(f'Shoulder{side}', f'Shoulder{side}', add(top, (0, 0, 0.35)))

# ---------------- arms: twisted mossy root bundles, giant gnarled fists ----------------
for side, s in SIDES:
    sh, el, wr, hd = ARM[side]
    arm = [f'Arm{side}', f'Fore{side}', f'Hand{side}']
    for k in range(3):   # three roots twisting round each other
        a0 = TAU * k / 3
        pts, rad = [], []
        for j, (p, r) in enumerate(((sh, 0.38), (lerp(sh, el, 0.5), 0.32), (el, 0.34), (lerp(el, wr, 0.5), 0.33), (wr, 0.3))):
            a = a0 + 1.4 * j
            pts.append(add(p, (math.cos(a) * 0.17, math.sin(a) * 0.17, 0)))
            rad.append((r * 0.62, r * 0.62))
        m.loft(arm[:2], 'bark' if k else 'bark2', pts, rad, sides=5, steps=2, smooth=False)
    # moss on the upper arm, a glowing crack down the forearm
    m.blob(arm[0], 'moss', add(lerp(sh, el, 0.35), (0.12 * s, 0.05, 0.12)), (0.28, 0.26, 0.12), u=6, v=4)
    crk = [add(lerp(el, wr, t), (0.25 * s, -0.12, 0.03 * ((i % 2) * 2 - 1))) for i, t in enumerate((0.1, 0.35, 0.6, 0.85))]
    m.loft(arm[1], 'glow2', crk, [(0.035, 0.035)] * 4, sides=4, steps=1, smooth=False)
    for t, d in ((0.3, (s, 0.4, 0.4)), (0.7, (s, -0.3, -0.1))):
        m.spike(arm[0], 'thorn', lerp(sh, el, t), d, 0.28, 0.1, snap=False)
    # an iron manacle at the wrist with snapped chain
    ring = [add(wr, (math.cos(TAU * i / 10) * 0.36, math.sin(TAU * i / 10) * 0.36, 0.12)) for i in range(11)]
    m.loft(arm[1], 'iron', ring, [(0.08, 0.13)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
    for li in range(3):
        m.box(arm[1], 'iron', add(wr, (0.38 * s, -0.05, 0.0 - 0.17 * li)), (0.06, 0.14, 0.18), rot=(0, 0, 90 * (li % 2)), bevel=0.0)
    # the fist: a gnarled knot of wood with root knuckles and claws
    fc = lerp(wr, hd, 0.55)
    m.blob(arm[2], 'bark2', fc, (0.48, 0.44, 0.46), u=8, v=6)
    m.blob(arm[2], 'bark', add(fc, (0.12 * s, 0.1, 0.12)), (0.36, 0.34, 0.34), u=7, v=5)
    for k in (-1.5, -0.5, 0.5, 1.5):
        kn = add(fc, (0.13 * k, -0.38, -0.12))
        m.blob(arm[2], 'bark', kn, (0.12, 0.12, 0.13), u=5, v=4)
        m.spike(arm[2], 'thorn', kn, (0.1 * k, -0.6, -0.8), 0.2, 0.08, snap=False)
    m.spike(arm[2], 'thorn', add(fc, (0.35 * s, 0.0, 0.1)), (s, 0, 0.2), 0.32, 0.12, snap=False)
    m.socket(f'Hand{side}', arm[2], fc)
    if s < 0:   # the right fist is wrapped in heavy chain
        for i in range(7):
            a = TAU * i / 7
            c = add(fc, (math.cos(a) * 0.5, math.sin(a) * 0.46, -0.05 + 0.08 * (i % 2)))
            m.box(arm[2], 'iron', c, (0.1, 0.22, 0.14) if i % 2 else (0.22, 0.1, 0.14), rot=(0, 0, math.degrees(a)), bevel=0.0)

# ---------------- legs: root trunks, tombstone knee plates, root-stump feet ----------------
for side, s in SIDES:
    hip, knee, ank, toe = LEG[side]
    leg = [f'Thigh{side}', f'Shin{side}', f'Foot{side}']
    m.loft(leg[:2], 'bark', [hip, knee, ank], [(0.55, 0.55), (0.46, 0.46), (0.5, 0.5)], sides=6, steps=2, smooth=False)
    for k in range(3):   # roots twisting down the trunk
        a0 = TAU * k / 3 + 0.4
        pts = [add(lerp(hip, ank, t), (math.cos(a0 + 2.0 * t) * 0.5, math.sin(a0 + 2.0 * t) * 0.47, 0)) for t in (0.0, 0.33, 0.66, 1.0)]
        m.loft(leg[:2], 'bark2', pts, [(0.12, 0.12)] * 4, sides=4, steps=2, smooth=False)
    m.blob(leg[0], 'moss', add(lerp(hip, knee, 0.4), (0.3 * s, 0.1, 0)), (0.25, 0.25, 0.14), u=6, v=4)
    # a tombstone lashed over the knee: rounded top, carved cross, cracked, mossy
    ts = add(knee, (0, -0.48, 0.05))
    m.box(leg[1], 'stone', ts, (0.62, 0.16, 0.7), rot=(-8, 0, 0), bevel=0.04)
    m.blob(leg[1], 'stone', add(ts, (0, 0.0, 0.34)), (0.31, 0.08, 0.16), u=8, v=4)
    m.box(leg[1], 'stone2', add(ts, (0, -0.09, 0.08)), (0.08, 0.04, 0.4), bevel=0.0)
    m.box(leg[1], 'stone2', add(ts, (0, -0.09, 0.15)), (0.28, 0.04, 0.07), bevel=0.0)
    m.box(leg[1], 'dark', add(ts, (0.17 * s, -0.09, -0.15)), (0.03, 0.03, 0.3), rot=(0, 25, 0), bevel=0.0)
    m.blob(leg[1], 'moss', add(ts, (-0.2 * s, -0.04, 0.4)), (0.16, 0.08, 0.06), u=5, v=3)
    for z in (-0.18, 0.2):   # rope lashings round the leg
        ring = [add(knee, (math.cos(TAU * i / 10) * 0.56, -0.05 + math.sin(TAU * i / 10) * 0.56, z)) for i in range(11)]
        m.loft(leg[1], 'rope', ring, [(0.05, 0.05)] * 11, sides=4, steps=1, smooth=False, cap_round=0.0)
    # foot: a broad root stump with roots splaying out like claws
    fc = add(ank, (0, -0.3, -0.18))
    m.box(leg[2], 'bark', fc, (0.85, 1.1, 0.42), bevel=0.1, taper=dict(axis='z', end=1, scale=(0.75, 0.75)))
    for k in (-1, -0.33, 0.33, 1):
        a = 0.55 * k
        p = add(fc, (0.35 * k, -0.45, -0.1))
        m.loft(leg[2], 'bark2', [p, add(p, (math.sin(a) * 0.35, -math.cos(a) * 0.35, -0.08))], [(0.1, 0.1), (0.04, 0.04)], sides=4, steps=1, smooth=False)
    m.spike(leg[2], 'bark2', add(fc, (0.42 * s, 0.25, -0.1)), (s, 0.3, -0.1), 0.35, 0.12, snap=False)


# ---------------- animation ----------------
LEGS = {side: (f'Thigh{side}', f'Shin{side}', f'Foot{side}') for side, _ in SIDES}
WALK = dict(stride=1.3, lift=0.4, duty=0.6, frames=36)
RUN = dict(stride=2.2, lift=0.55, duty=0.48, frames=24)


def legs(pose, t_, g_, bob):
    for (side, _), ph in zip(SIDES, (0.0, 0.5)):
        u = (t_ + ph) % 1.0
        D = g_['stride'] * S
        if u < g_['duty']:
            dy, dz = D / 2 - D * u / g_['duty'], 0.0
        else:
            q = (u - g_['duty']) / (1 - g_['duty'])
            dy, dz = -D / 2 + D * smooth01(q), g_['lift'] * S * math.sin(math.pi * q)
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - dy, az + dz), shift=(0, bob))


def planted(pose, bob=0.0, dy=0.0):
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay + dy, az), shift=(0, bob))


def arms(pose, l, r, fl=0.0, fr=0.0, spread=0.0):
    pose['ArmL'] = ((-l, 0, spread), (0, 0, 0))
    pose['ArmR'] = ((-r, 0, -spread), (0, 0, 0))
    pose['ForeL'] = ((-fl, 0, 0), (0, 0, 0))
    pose['ForeR'] = ((-fr, 0, 0), (0, 0, 0))


def idle(t_):   # heavy breathing, the head rolling, fists flexing
    p = TAU * t_
    br = math.sin(p)
    bob = 0.04 * S * br
    pose = {
        'Hips': ((0, 0, 0), (0, 0, bob)),
        'Chest': ((3 * br, 0, 3 * math.sin(p * 0.5)), (0, 0, 0)),
        'Head': ((-4 * br, 0, 8 * math.sin(p * 0.5)), (0, 0, 0)),
        'Jaw': ((5 + 4 * math.sin(2 * p), 0, 0), (0, 0, 0)),
        'ShoulderL': ((0, 3 * br, 0), (0, 0, 0)), 'ShoulderR': ((0, -3 * br, 0), (0, 0, 0)),
    }
    arms(pose, 4 * br, 4 * br, 5 * br, 5 * br)
    planted(pose, bob)
    return pose


def walk(t_):   # a ground-shaking lumber, the chest swinging over each planted leg
    p = TAU * t_
    bob = 0.12 * S * abs(math.sin(p))
    pose = {
        'Hips': ((0, 6 * math.sin(p), 0), (0, 0, -bob)),
        'Chest': ((8, -8 * math.sin(p), 7 * math.sin(p)), (0, 0, 0)),
        'Head': ((-6, 0, -6 * math.sin(p)), (0, 0, 0)),
        'Jaw': ((8 + 6 * abs(math.sin(2 * p)), 0, 0), (0, 0, 0)),
    }
    arms(pose, 22 * math.sin(p), -22 * math.sin(p), 10 + 10 * math.sin(p), 10 - 10 * math.sin(p))
    legs(pose, t_, WALK, -bob)
    return pose


def run(t_):    # a gorilla charge
    p = TAU * t_
    bob = 0.18 * S * abs(math.sin(p))
    pose = {
        'Hips': ((14, 5 * math.sin(p), 0), (0, 0, bob)),
        'Chest': ((18, -6 * math.sin(p), 6 * math.sin(p)), (0, 0, 0)),
        'Head': ((-20, 0, 0), (0, 0, 0)),
        'Jaw': ((20, 0, 0), (0, 0, 0)),
    }
    arms(pose, 45 * math.sin(p), -45 * math.sin(p), 25, 25)
    legs(pose, t_, RUN, bob)
    return pose


def sleep(t_):   # sinks onto its haunches, head slumped, the fire banked low
    p = TAU * t_
    drop = -0.7 * S
    pose = {
        'Hips': ((0, 0, 0), (0, 0, drop + 0.03 * S * math.sin(p))),
        'Chest': ((16 + 2 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((28, 0, 6), (0, 0, 0)),
        'Jaw': ((0, 0, 0), (0, 0, 0)),
    }
    arms(pose, -10, -10, 20, 20)
    for side, _ in SIDES:
        ay, az = m.rest_ankle(LEGS[side][1])
        ik(m, pose, LEGS[side], (ay - 0.35 * S, az), shift=(0, drop))
    return pose


def roar(t_):    # rears back and pounds its chest, fire bellowing out of the grin
    e = envelope(t_, 0.2, 0.8)
    pound = math.sin(TAU * 5 * t_) * envelope(t_, 0.3, 0.75, 0.85)
    pose = {
        'Chest': ((-18 * e, 0, 0), (0, 0, 0)),
        'Head': ((-25 * e, 0, 5 * pound), (0, 0, 0)),
        'Jaw': ((45 * e, 0, 0), (0, 0, 0)),
    }
    arms(pose, 70 * e + 18 * pound, 70 * e - 18 * pound, 80 * e, 80 * e, 25 * e)
    planted(pose)
    return pose


def attack(t_):  # both fists hauled overhead, then a double slam into the ground
    w = envelope(t_, 0.32, 0.34, 0.42)
    c = smooth01((t_ - 0.34) / 0.1) if t_ < 0.7 else 1 - smooth01((t_ - 0.7) / 0.3)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, -0.3 * S * c, 0)),
        'Hips': ((0, 0, 0), (0, 0, -0.25 * S * c)),
        'Chest': ((-15 * w + 32 * c, 0, 0), (0, 0, 0)),
        'Head': ((10 * w - 15 * c, 0, 0), (0, 0, 0)),
        'Jaw': ((20 * w + 30 * c, 0, 0), (0, 0, 0)),
    }
    arms(pose, 170 * w - 10 * c, 170 * w - 10 * c, 20 * w, 20 * w)
    planted(pose, -0.25 * S * c, -0.3 * S * c)
    return pose


def happy(t_):   # stomps side to side, fists pumping overhead
    e = envelope(t_, 0.1, 0.85)
    sw = math.sin(TAU * 2 * t_)
    hop = abs(math.sin(TAU * 2 * t_)) * e
    pose = {
        'MonsterRoot': ((0, 0, 12 * sw * e), (0, 0, 0.35 * S * hop)),
        'Chest': ((-8 * e, 10 * sw * e, 0), (0, 0, 0)),
        'Jaw': ((30 * e, 0, 0), (0, 0, 0)),
        'Head': ((-10 * e, 0, -10 * sw * e), (0, 0, 0)),
    }
    arms(pose, (150 + 20 * sw) * e, (150 - 20 * sw) * e, 30 * e, 30 * e)
    planted(pose)
    return pose


m.anim('Idle', 80, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, walk, key_step=1)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 60, False, roar, key_step=2)
m.anim('Attack', 42, False, attack, key_step=2)
m.anim('Happy', 48, False, happy, key_step=1)
m.refs = {'Walk': WALK['stride'] * S / (WALK['duty'] * WALK['frames'] / 30), 'Run': RUN['stride'] * S / (RUN['duty'] * RUN['frames'] / 30)}
m.build(OUT)
