"""Scarecrow Crow - Rare Haunted monster (Haunted Pumpkin featured egg): a tall, lean crow that has
become its own scarecrow. A patched burlap coat with stitched seams, a ragged hem of hanging strips
and a rope belt; straw bursting from the collar, cuffs and hem and poking through tattered black
wings; a long cracked black beak; mismatched eyes - one a glowing orange button with thread holes,
the other stitched shut with an X; a crooked, battered witch-brim hat with a band and buckle; a
wooden crossbeam lashed across its shoulders; rope-bound talons; and a little jack-o'-lantern hung
from a crooked pole, held out in one wing. Hops on the ground, flaps low when running. Faces -Y.
    blender -b --python scarecrow.py -- <out_dir> [Child|Teen|Adult] [--live]
Sockets: Lantern (foxfire), Hat, Eye."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, refs, envelope, smooth01, add, TAU

m, st, OUT = setup('ScarecrowCrow', {
    'feather': '#1e1c2a', 'feather2': ('#34304a', True, True), 'coat': ('#8a6a42', True, True), 'patch': ('#5e7a48', True, True),
    'patch2': ('#7a3a3a', True, True), 'stitch': ('#e8dcc0', False), 'rope': ('#c8a868', True, True), 'straw': ('#e2c060', False, True),
    'beak': ('#16141a', False, True), 'crack': ('#ff8a1a', False), 'hat': ('#2a2430', True, True), 'band': ('#6a2a3a', False, True),
    'buckle': ('#d8b048', False), 'wood': ('#5a4028', True, True), 'pumpkin': ('#f06a1a', True, True), 'glow': ('#ffc23a', False),
    'button': ('#ff8a1a', False), 'dark': ('#0a080c', False), 'talon': ('#141016', False), 'foot': '#3a3440',
    'eye_dark': ('#0a080c', False), 'iris': ('#ff8a1a', False), 'eye_glint': ('#fff0c0', False),
}, {'Child': dict(head=1.3, eye=1.25), 'Teen': dict(head=1.1, eye=1.1)})
S, E, g, h = st['S'], st['energy'], st['grow'], st['head']
SIDES = (('L', 1), ('R', -1))
HEAD = (0, -0.25, 4.15 + 0.35 * (h - 1))


def disc(bone, color, c, n, r, d, seg):
    """kit's disc in stage-scaled units (Scaled doesn't wrap disc)"""
    m.disc(bone, color, m.sv(c), n, r * S, d * S, seg)


def Hd(x, y, z):
    return (HEAD[0] + x * h, HEAD[1] + y * h, HEAD[2] + z * h)


span = 0.7 + 0.3 * g
# ---------------- rig ----------------
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Hips', (0, 0.15, 1.3), (0, 0, 2.5), 'MonsterRoot')
m.bone('Chest', (0, 0, 2.5), (0, -0.15, 3.5), 'Hips')
m.bone('Head', (0, -0.15, 3.5), Hd(0, -1.1, 0.05), 'Chest')
m.bone('Hat', Hd(0, 0.0, 0.6), Hd(0.15, 0.1, 1.6), 'Head')
m.bone('Tail', (0, 0.7, 1.6), (0, 1.6, 0.9), 'Hips')
for side, s in SIDES:
    sh = (0.85 * s, 0.05, 3.2)
    wr = (1.15 * s, 0.25, 3.2 - 1.2 * span)
    tip = (1.0 * s, 0.9, 3.2 - 2.35 * span)
    m.bone(f'Wing{side}', sh, wr, 'Chest')
    m.bone(f'WingTip{side}', wr, tip, f'Wing{side}')
    m.bone(f'Leg{side}', (0.38 * s, 0.0, 1.2), (0.38 * s, -0.1, 0.38), 'Hips')
    m.bone(f'Foot{side}', (0.38 * s, -0.1, 0.38), (0.38 * s, -0.65, 0.05), f'Leg{side}')

# ---------------- body: feathered torso inside a patched burlap coat ----------------
m.loft(['Hips', 'Chest', 'Head'], 'feather', [(0, 0.15, 1.0), (0, 0.05, 1.8), (0, 0, 2.7), (0, -0.08, 3.4), Hd(0, 0.0, -0.35)],
       [(0.7, 0.66), (0.98, 0.9), (0.92, 0.86), (0.72, 0.68), (0.62 * h, 0.6 * h)], sides=7, steps=2, smooth=False, up=(0, -1, 0))
# the coat: a looser, outlined shell over the torso, open at the front
coat_pts = [(0, 0.12, 1.25), (0, 0.05, 1.9), (0, 0.0, 2.6), (0, -0.05, 3.2)]
m.loft(['Hips', 'Chest'], 'coat', coat_pts, [(1.06, 1.0), (1.1, 1.02), (1.02, 0.96), (0.86, 0.8)], sides=7, steps=2, smooth=False, up=(0, -1, 0))
m.box(['Hips', 'Chest'], 'feather2', (0, -0.98, 2.25), (0.5, 0.12, 1.7), bevel=0.04)   # dark shirt showing at the front
# patches stitched on
for (x, y, z, w, hh, col, rot) in ((0.62, -0.72, 2.6, 0.4, 0.38, 'patch', 12), (-0.7, -0.6, 1.75, 0.45, 0.4, 'patch2', -8),
                                    (0.95, 0.25, 2.1, 0.12, 0.5, 'patch', 0), (-0.5, 0.75, 2.45, 0.45, 0.36, 'patch2', 20)):
    m.box(['Hips', 'Chest'][int(z > 2.2)], col, (x, y, z), (w, 0.1, hh) if abs(y) > 0.5 else (0.1, w, hh), rot=(0, rot, 0), bevel=0.02)
    for k in range(3):   # cross stitches along one edge
        sx = x + (k - 1) * w * 0.3
        m.box(['Hips', 'Chest'][int(z > 2.2)], 'stitch', (sx, y - 0.06 if y < 0 else y + 0.06, z + hh * 0.5), (0.03, 0.03, 0.14), rot=(0, 30, 0), bevel=0.0)
# stitched seam down the chest
for k in range(6):
    z = 1.55 + 0.27 * k
    m.box(['Hips', 'Chest'][int(z > 2.5)], 'stitch', (0.27, -1.05, z), (0.16, 0.03, 0.03), rot=(0, 35, 0), bevel=0.0)
    m.box(['Hips', 'Chest'][int(z > 2.5)], 'stitch', (-0.27, -1.05, z), (0.16, 0.03, 0.03), rot=(0, -35, 0), bevel=0.0)
# rope belt with a knot, ragged hem strips hanging below, straw bursting out
belt = [(math.cos(TAU * i / 14) * 1.12, 0.05 + math.sin(TAU * i / 14) * 1.04, 1.55) for i in range(15)]
m.loft('Hips', 'rope', belt, [(0.07, 0.09)] * len(belt), sides=5, steps=1, smooth=False, cap_round=0.0)
m.blob('Hips', 'rope', (0.35, -1.05, 1.52), (0.14, 0.1, 0.14), u=6, v=4)
for i in range(12):
    a = TAU * i / 12 + 0.2
    p = (math.cos(a) * 1.0, 0.05 + math.sin(a) * 0.94, 1.2)
    d = (math.cos(a) * 0.15, math.sin(a) * 0.15, -1)
    m.spike('Hips', 'coat' if i % 3 else 'patch2', p, d, 0.35 + 0.15 * (i % 2), 0.28, 0.05, snap=False)
    if i % 2 == 0:
        m.spike('Hips', 'straw', add(p, (0, 0, 0.05)), (math.cos(a) * 0.4, math.sin(a) * 0.4, -1), 0.45, 0.06, 0.04, snap=False)
# straw ruff bursting out of the collar
for i in range(14):
    a = TAU * i / 14
    p = (math.cos(a) * 0.62, -0.1 + math.sin(a) * 0.56, 3.35)
    m.spike('Chest', 'straw', p, (math.cos(a), math.sin(a), 0.7 - 0.4 * (i % 2)), 0.42 + 0.12 * (i % 3), 0.07, 0.05, snap=False)
# the crossbeam lashed across the shoulders
beam_y, beam_z = 0.55, 3.25
m.box('Chest', 'wood', (0, beam_y, beam_z), (3.2 * (0.7 + 0.3 * g), 0.3, 0.26), bevel=0.04)
m.box('Chest', 'wood', (0, beam_y + 0.05, beam_z - 0.6), (0.28, 0.26, 2.0), bevel=0.04)
for side, s in SIDES:
    m.loft('Chest', 'rope', [(0.45 * s, beam_y - 0.2, beam_z + 0.2), (0.5 * s, beam_y + 0.2, beam_z - 0.2)], [(0.05, 0.05)] * 2, sides=4, steps=1, smooth=False)

# ---------------- head ----------------
m.blob('Head', 'feather', Hd(0, -0.25, 0.0), (0.62 * h, 0.7 * h, 0.6 * h), u=8, v=6)
for k in range(5):   # shaggy feathers on the crown and nape
    m.spike('Head', 'feather2', Hd(0.2 * (k - 2), 0.15, 0.4), (0.2 * (k - 2), 0.8, 0.6), 0.4 * h, 0.2 * h, 0.06 * h)
# the long cracked beak, glowing through the crack
m.box('Head', 'beak', Hd(0, -1.0, -0.05), (0.42 * h, 0.75 * h, 0.36 * h), bevel=0.06 * h, taper=dict(axis='y', end=-1, scale=(0.45, 0.5)))
m.spike('Head', 'beak', Hd(0, -1.35, -0.02), (0, -1, -0.25), 0.55 * h, 0.22 * h, 0.2 * h, snap=False)
m.box('Head', 'crack', Hd(0.12, -1.05, 0.12), (0.04 * h, 0.4 * h, 0.03 * h), rot=(0, 0, 18), bevel=0.0)
m.box('Head', 'beak', Hd(0, -0.95, -0.25), (0.34 * h, 0.6 * h, 0.1 * h), bevel=0.03 * h, taper=dict(axis='y', end=-1, scale=(0.4, 0.6)))
# the button eye (glowing, four thread holes) and the stitched-shut eye
bx = Hd(0.36, -0.62, 0.15)
disc('Head', 'button', bx, (0.6, -1, 0.1), 0.2 * h * st['eye'], 0.06, 12)
for dx, dz in ((-0.05, 0.05), (0.05, 0.05), (-0.05, -0.05), (0.05, -0.05)):
    disc('Head', 'dark', add(bx, (dx * h + 0.02, -0.04, dz * h)), (0.6, -1, 0.1), 0.025 * h, 0.04, 6)
m.socket('Eye', 'Head', add(bx, (0.03, -0.06, 0)))
ex = Hd(-0.36, -0.62, 0.15)
disc('Head', 'dark', ex, (-0.6, -1, 0.1), 0.17 * h, 0.04, 10)
for ang in (40, -40):
    m.box('Head', 'stitch', add(ex, (0.0, -0.05, 0.0)), (0.3 * h, 0.03, 0.04), rot=(0, ang, -30), bevel=0.0)
# angry brow plates
for side, s in SIDES:
    m.box('Head', 'feather2', Hd(0.34 * s, -0.66, 0.4), (0.38 * h, 0.14 * h, 0.1 * h), rot=(12, 0, -25 * s), bevel=0.02 * h)
# the crooked witch-brim hat: wide brim, crumpled bent cone, band and buckle
brim = [Hd(math.cos(TAU * i / 14) * 0.95, math.sin(TAU * i / 14) * 0.9, 0.55 + 0.06 * math.sin(TAU * i / 7)) for i in range(15)]
m.loft('Hat', 'hat', brim, [(0.18 * h, 0.04 * h)] * len(brim), sides=4, steps=1, smooth=False, cap_round=0.0)
m.blob('Hat', 'hat', Hd(0, 0.0, 0.58), (0.92 * h, 0.88 * h, 0.06 * h), u=10, v=3)
cone = [Hd(0, 0, 0.6), Hd(0.02, 0.05, 1.0), Hd(0.1, 0.12, 1.35), Hd(0.35, 0.3, 1.55), Hd(0.55, 0.42, 1.48)]
m.loft('Hat', 'hat', cone, [(0.5 * h, 0.48 * h), (0.38 * h, 0.37 * h), (0.25 * h, 0.24 * h), (0.12 * h, 0.12 * h), (0.05 * h, 0.05 * h)], sides=6, steps=2, smooth=False)
band = [Hd(math.cos(TAU * i / 12) * 0.47, math.sin(TAU * i / 12) * 0.46, 0.7) for i in range(13)]
m.loft('Hat', 'band', band, [(0.05 * h, 0.08 * h)] * len(band), sides=4, steps=1, smooth=False, cap_round=0.0)
m.box('Hat', 'buckle', Hd(0, -0.48, 0.7), (0.2 * h, 0.05 * h, 0.16 * h), bevel=0.0)
m.box('Hat', 'dark', Hd(0, -0.5, 0.7), (0.1 * h, 0.05 * h, 0.07 * h), bevel=0.0)
for k in range(3):   # straw poking out under the brim
    m.spike('Hat', 'straw', Hd(0.45 * (k - 1), 0.4, 0.5), (0.4 * (k - 1), 0.7, -0.4), 0.4 * h, 0.06 * h, 0.04 * h, snap=False)
m.socket('Hat', 'Hat', Hd(0.55, 0.42, 1.5))

# ---------------- wings: ragged black feathers with straw poking through ----------------
for side, s in SIDES:
    sh = (0.85 * s, 0.05, 3.2)
    wr = (1.15 * s, 0.25, 3.2 - 1.2 * span)
    tip = (1.0 * s, 0.9, 3.2 - 2.35 * span)
    bones = [f'Wing{side}', f'WingTip{side}']
    lead, trail = [], []
    n = 11
    for i in range(n):
        u = i / (n - 1)
        a, b, f = (sh, wr, u / 0.5) if u <= 0.5 else (wr, tip, (u - 0.5) / 0.5)
        p = tuple(x + (y - x) * f for x, y in zip(a, b))
        lead.append(p)
        chord = (1.0 * (1 - u) ** 0.6 + 0.12) * span * (0.7 + 0.3 * abs(math.cos(u * 5 * math.pi)))   # ragged
        trail.append(add(p, (0.12 * s * chord, chord, 0.15 * chord)))
    m.strip(bones, 'feather', lead, trail, thickness=0.16)
    m.loft(bones, 'feather2', [sh, wr, tip], [(0.18, 0.18), (0.13, 0.13), (0.05, 0.05)], sides=4, steps=3, smooth=False)
    for k, u in enumerate((0.3, 0.45, 0.6, 0.75, 0.9)):
        i = int(u * (n - 1))
        m.spike(bones[0] if u < 0.5 else bones[1], 'feather2' if k % 2 else 'feather', trail[i], (0.1 * s, 1, -0.6),
                (0.5 + 0.3 * g) * span, 0.24, 0.05, snap=False)
        if k % 2 == 0:
            m.spike(bones[0] if u < 0.5 else bones[1], 'straw', lead[i], (s, -0.2, -0.2), 0.32, 0.05, 0.04, snap=False)
    m.blob(['Chest', bones[0]], 'coat', sh, (0.42, 0.42, 0.4), u=6, v=4)   # coat shoulders
    m.loft(bones[0], 'coat', [sh, wr], [(0.3, 0.3), (0.24, 0.24)], sides=6, steps=1, smooth=False)   # ragged sleeve
    for k in range(3):
        m.spike(bones[0], 'straw', wr, (s * 0.6 + 0.2 * (k - 1), 0.2 * (k - 1), -1), 0.35, 0.06, 0.04, snap=False)

# ---------------- the lantern on its crooked pole, held out in the right wing ----------------
wr_r = (1.15 * -1, 0.25, 3.2 - 1.2 * span)
pole_top = add(wr_r, (-0.25, -0.75, 0.9))
m.loft('WingTipR', 'wood', [add(wr_r, (0.05, 0.3, -0.5)), wr_r, add(wr_r, (-0.1, -0.35, 0.45)), pole_top],
       [(0.06, 0.06)] * 4, sides=5, steps=1, smooth=False)
hang = add(pole_top, (0, -0.25, -0.15))
m.loft('WingTipR', 'rope', [pole_top, hang, add(hang, (0, 0, -0.35))], [(0.025, 0.025)] * 3, sides=4, steps=1, smooth=False)
lc = add(hang, (0, 0, -0.62))
m.blob('WingTipR', 'pumpkin', lc, (0.3, 0.28, 0.26), u=8, v=6)
m.blob('WingTipR', 'glow', add(lc, (0, -0.24, 0.02)), (0.16, 0.05, 0.08), u=6, v=4)
m.loft('WingTipR', 'wood', [add(lc, (0, 0, 0.24)), add(lc, (0.05, 0, 0.36))], [(0.04, 0.04)] * 2, sides=4, steps=1, smooth=False)
m.socket('Lantern', 'WingTipR', lc)

# ---------------- tail and legs ----------------
for yaw in (-0.35, -0.12, 0.12, 0.35):
    m.spike('Tail', 'feather' if yaw > 0 else 'feather2', (0, 0.75, 1.5), (yaw, 1.0, -0.6), 0.95 + 0.4 * g, 0.36, 0.08, snap=False)
for side, s in SIDES:
    m.loft([f'Leg{side}'], 'foot', [(0.38 * s, 0.0, 1.2), (0.38 * s, -0.08, 0.42)], [(0.16, 0.16), (0.12, 0.12)], sides=5, steps=1, smooth=False)
    for k in range(3):   # rope binding
        m.loft([f'Leg{side}'], 'rope', [(0.38 * s - 0.17, -0.05, 0.7 + 0.12 * k), (0.38 * s + 0.17, -0.05, 0.66 + 0.12 * k)], [(0.04, 0.04)] * 2, sides=4, steps=1, smooth=False)
    m.box(f'Foot{side}', 'foot', (0.38 * s, -0.25, 0.14), (0.36, 0.5, 0.22), bevel=0.05)
    for dx in (-0.14, 0.0, 0.14):
        m.spike(f'Foot{side}', 'talon', (0.38 * s + dx, -0.48, 0.12), (dx, -1, -0.6), 0.36, 0.1, snap=False)
    m.spike(f'Foot{side}', 'talon', (0.38 * s, 0.05, 0.1), (0, 1, -0.6), 0.28, 0.1, snap=False)


# ---------------- animation ----------------
WALK = dict(stride=1.0, frames=24)
RUN = dict(stride=4.0, frames=20)


def wings(pose, spread, fold=0.0, tip=0.0, fwd=0.0):
    for side, s in SIDES:
        pose[f'Wing{side}'] = ((fwd, -spread * s, fold * s), (0, 0, 0))
        pose[f'WingTip{side}'] = ((0, -tip * s, 0), (0, 0, 0))


def idle(t_):
    p = TAU * t_
    tilt = 25 * smooth01((t_ - 0.3) / 0.1) * (1 - smooth01((t_ - 0.6) / 0.15))   # a creepy head tilt
    pose = {
        'Hips': ((0, 0, 0), (0, 0, 0.03 * S * math.sin(2 * p))),
        'Chest': ((2 * math.sin(p), 0, 3 * math.sin(p)), (0, 0, 0)),
        'Head': ((0, tilt, 12 * math.sin(p)), (0, 0, 0)),
        'Hat': ((4 * math.sin(p + 1), 0, 6 * math.sin(p * 2)), (0, 0, 0)),
        'Tail': ((0, 0, 6 * math.sin(2 * p)), (0, 0, 0)),
    }
    wings(pose, 6 + 4 * math.sin(2 * p))
    pose['WingR'] = ((-35, 8, 0), (0, 0, 0))    # the lantern held out in front
    return pose


def walk(t_):
    u = t_ % 1.0
    hop = math.sin(math.pi * u) if u < 0.6 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, 0.42 * S * E * hop)),
        'Hips': ((-6 * hop, 0, 0), (0, 0, 0)),
        'Head': ((8 * hop, 0, 6 * math.sin(TAU * u)), (0, 0, 0)),
        'Hat': ((-12 * hop, 0, 0), (0, 0, 0)),
        'Tail': ((-10 * hop, 0, 0), (0, 0, 0)),
    }
    wings(pose, 15 + 18 * hop, tip=10 * hop)
    pose['WingR'] = ((-35 - 8 * hop, 8, 0), (0, 0, 0))
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((20 * hop, 0, 0), (0, 0, 0))
        pose[f'Foot{side}'] = ((-25 * hop, 0, 0), (0, 0, 0))
    return pose


def run(t_):
    p = TAU * t_
    beat = math.sin(p)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, 0, (1.1 + 0.25 * beat) * S)),
        'Hips': ((32, 0, 0), (0, 0, 0)),
        'Head': ((-28, 0, 0), (0, 0, 0)),
        'Hat': ((-25, 0, 0), (0, 0, 0)),
        'Tail': ((-15, 0, 0), (0, 0, 0)),
    }
    wings(pose, 92 + 38 * beat, tip=25 * math.sin(p - 0.8), fwd=-10)
    for side, s in SIDES:
        pose[f'Leg{side}'] = ((55, 0, 0), (0, 0, 0))
        pose[f'Foot{side}'] = ((40, 0, 0), (0, 0, 0))
    return pose


def sleep(t_):
    p = TAU * t_
    pose = {
        'Hips': ((0, 0, 0), (0, 0, -0.25 * S + 0.03 * S * math.sin(p))),
        'Chest': ((6 + 1.5 * math.sin(p), 0, 0), (0, 0, 0)),
        'Head': ((28, 0, 15), (0, 0, 0)),
        'Hat': ((20, 0, 10), (0, 0, 0)),
    }
    wings(pose, -4)
    pose['WingR'] = ((-15, 0, 0), (0, 0, 0))
    return pose


def caw(t_):     # wings thrown wide, lantern swung high, beak open to caw
    e = envelope(t_, 0.2, 0.75)
    sh = math.sin(TAU * 7 * t_) * envelope(t_, 0.25, 0.7, 0.8)
    pose = {
        'Hips': ((-6 * e, 0, 0), (0, 0, 0)),
        'Head': ((-30 * e, 0, 8 * sh), (0, 0, 0)),
        'Hat': ((-15 * e, 0, 10 * sh), (0, 0, 0)),
    }
    wings(pose, 95 * e + 8 * sh, tip=15 * e, fwd=-20 * e)
    return pose


def attack(t_):  # swings the lantern like a flail
    w = envelope(t_, 0.3, 0.32, 0.42)
    c = smooth01((t_ - 0.32) / 0.14) if t_ < 0.65 else 1 - smooth01((t_ - 0.65) / 0.35)
    pose = {
        'MonsterRoot': ((0, 0, 0), (0, -0.4 * S * c, 0.15 * S * w)),
        'Chest': ((-8 * w + 12 * c, 0, 25 * w - 30 * c), (0, 0, 0)),
        'Head': ((10 * c, 0, 0), (0, 0, 0)),
    }
    wings(pose, 30 * w)
    pose['WingR'] = ((-60 * w - 40 * c, 60 * w - 90 * c, 0), (0, 0, 0))
    return pose


def happy(t_):
    e = envelope(t_, 0.1, 0.75)
    hop = math.sin(math.pi * smooth01(t_ / 0.5)) if t_ < 0.5 else 0.0
    pose = {
        'MonsterRoot': ((0, 0, 360 * smooth01(t_ / 0.6) if t_ < 0.6 else 0), (0, 0, 0.6 * S * E * hop)),
        'Head': ((-8 * e, 20 * e * math.sin(TAU * 2 * t_), 0), (0, 0, 0)),
        'Hat': ((0, 0, 30 * math.sin(TAU * 3 * t_) * e), (0, 0, 0)),
    }
    wings(pose, 60 * e + 30 * e * math.sin(TAU * 4 * t_), tip=20 * e)
    return pose


m.anim('Idle', 96, True, idle, key_step=2)
m.anim('Walk', WALK['frames'], True, walk, key_step=1)
m.anim('Run', RUN['frames'], True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 48, False, caw, key_step=2)
m.anim('Attack', 36, False, attack, key_step=2)
m.anim('Happy', 40, False, happy, key_step=2)
m.refs = refs({'Walk': WALK, 'Run': RUN}, S)
m.build(OUT)
