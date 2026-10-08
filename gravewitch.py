"""Grave Witch - the Halloween raid boss (never hatches). A towering crone riding a twisted broomstick.

Body:   a gaunt, hunched figure in a laced bodice under layers of tattered robes and a ragged shawl;
        the hem and cape shred into tatters that burn with ghost fire. A belt hung with glowing
        potion bottles, a chained spellbook and a little skull.
Head:   long sunken face with sharp cheekbones, deep wrinkles, a crooked warty hooked nose, a jutting
        chin, a grin of snaggled teeth, hollow sockets with burning eyes under wild brows, pointed
        ears with iron rings, and a mane of wild white hair whipping back.
Hat:    an enormous crooked, patched and stitched pointed hat with a buckled band, cobwebs on the
        brim, three melting candles and a bent tip with a tiny bat charm dangling from it.
Hands:  long bony fingers with knuckles, iron rings and hooked claws; the right hand conjures a
        ghost-fire orb.
Broom:  a gnarled, twisting handle carved with glowing runes, a horned skull mounted on the front,
        a lantern swinging under it, bristles bound with rope and chain and roaring with ghost fire.
Rides:  a bubbling cauldron with skull handles swinging off the back on chains (stolen eggs go
        here), and her familiar - a scrawny black cat with glowing eyes - perched behind her.

Phases are told apart in the game by recolouring the glow (green -> purple -> blood red), the
model is the same. Faces -Y.
    blender -b --python gravewitch.py -- <out_dir> [Adult] [--live]
Animations: Idle Walk Run Sleep Roar Attack Happy + Cast Summon Slam Stagger Enrage Death.
Sockets: BroomFire, Cauldron, Orb (spell hand), HandL, EyeL/EyeR, Candle1-3, Lantern, Skull, CatEyes."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as _kit
_kit.CHUNKY = True   # faceted chunky style
from creature import setup, envelope, smooth01, add, TAU

m, st, OUT = setup('GraveWitch', {
    'skin': ('#93b28a', True, True), 'skin2': ('#748f6c', True, True), 'skin3': ('#5c7556', True, True),
    'wrinkle': ('#4a5e44', False), 'wart': ('#6b8a5a', True, True), 'hair': ('#ece8f4', True, True), 'hair2': ('#c9c2d8', True, True),
    'hat': ('#33254a', True, True), 'hat2': ('#4a3668', True, True), 'patch': ('#4e3a2a', True, True), 'stitch': ('#c8b88a', False),
    'band': ('#6a2438', True, True), 'gold': ('#d8b040', False, True), 'web': ('#e8eaf2', False),
    'robe': ('#4a3266', True, True), 'robe2': ('#33234a', True, True), 'robe3': ('#6a4a88', True, True), 'shawl': ('#6a2e48', True, True),
    'lace': ('#d8c8a0', False), 'leather': ('#4a3020', True, True), 'claw': ('#ece6d2', False), 'ring': ('#3c3a46', False, True),
    'bark': ('#5c3c26', True, True), 'bark2': ('#432a1a', True, True), 'straw': ('#c8a050', True, True), 'straw2': ('#9a7a34', True, True),
    'rope': ('#c8b080', True, True), 'iron': ('#2c2a34', False, True), 'iron2': ('#45424e', False, True), 'bone': ('#ece4d0', False, True),
    'book': ('#5a2030', True, True), 'page': ('#e8dcc0', False), 'glass': ('#9ad8c8', False),
    'cat': ('#1c1820', True, True), 'cat2': ('#2c2632', True, True),
    'ghost': ('#5affb0', False), 'ghost2': ('#d0ffe8', False), 'glow': ('#8aff5a', False), 'glow2': ('#b48aff', False),
    'flame': ('#ffd24a', False), 'brew': ('#7aff5a', False), 'candle': ('#f2e8d0', True, True), 'mouth': '#1a0a14',
    'tooth': ('#e8dcb0', False), 'eye_dark': ('#0c0a10', False), 'iris': ('#a8ff6a', False), 'eye_glint': ('#ffffff', False),
}, {})
S = st['S']
SIDES = (('L', 1), ('R', -1))
HOVER = 4.4                       # broom height above the ground
SEAT = (0, 0.5, HOVER)
NECK = (0, -0.05, HOVER + 2.6)
HEAD = (0, -0.45, HOVER + 3.25)   # centre of the skull


def Hd(x, y, z):
    return (HEAD[0] + x, HEAD[1] + y, HEAD[2] + z)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def ring(bone, col, c, rx, ry, z, r, n=12, sides=4):
    pts = [(c[0] + math.cos(TAU * i / n) * rx, c[1] + math.sin(TAU * i / n) * ry, z) for i in range(n + 1)]
    m.loft(bone, col, pts, [(r, r)] * (n + 1), sides=sides, steps=1, smooth=False, cap_round=0.0)


# ================================================================ rig
m.bone('MonsterRoot', (0, 0, 0), (0, 0, 1))
m.bone('Broom', (0, 2.8, HOVER), (0, -3.2, HOVER + 0.35), 'MonsterRoot')
m.bone('Hips', SEAT, (0, 0.35, HOVER + 1.3), 'Broom')
m.bone('Chest', (0, 0.35, HOVER + 1.3), NECK, 'Hips')
m.bone('Neck', NECK, Hd(0, 0.15, -0.55), 'Chest')
m.bone('Head', Hd(0, 0.15, -0.55), Hd(0, -0.3, 0.6), 'Neck')
m.bone('Jaw', Hd(0, -0.45, -0.3), Hd(0, -0.95, -0.62), 'Head')
m.bone('Hat', Hd(0, 0.15, 0.62), Hd(0.1, 0.45, 2.0), 'Head')
m.bone('HatTip', Hd(0.1, 0.45, 2.0), Hd(1.1, 1.4, 2.7), 'Hat')
m.bone('Robe', (0, 0.7, HOVER - 0.1), (0, 1.9, HOVER - 2.3), 'Hips')
m.bone('Cape', (0, 0.55, HOVER + 2.3), (0, 2.6, HOVER + 0.4), 'Chest')
m.bone('Cauldron', (0, 3.75, HOVER - 0.15), (0, 3.75, HOVER - 1.8), 'Broom')
m.bone('Lantern', (0, -2.6, HOVER + 0.15), (0, -2.6, HOVER - 0.9), 'Broom')
m.bone('Cat', (0, 1.75, HOVER + 0.25), (0, 1.75, HOVER + 1.1), 'Broom')
m.bone('CatTail', (0, 2.15, HOVER + 0.35), (0, 2.9, HOVER + 1.0), 'Cat')
ARM = {   # shoulder, elbow, wrist, fingertips: L grips the broom, R raised conjuring
    'L': ((0.8, 0.25, HOVER + 2.25), (1.35, -0.45, HOVER + 1.45), (0.45, -1.35, HOVER + 0.75), (0.15, -1.75, HOVER + 0.5)),
    'R': ((-0.8, 0.25, HOVER + 2.25), (-1.75, -0.05, HOVER + 3.0), (-2.0, -0.55, HOVER + 4.0), (-2.05, -0.95, HOVER + 4.55)),
}
for side, s in SIDES:
    sh, el, wr, tip = ARM[side]
    m.bone(f'Arm{side}', sh, el, 'Chest')
    m.bone(f'Fore{side}', el, wr, f'Arm{side}')
    m.bone(f'Hand{side}', wr, tip, f'Fore{side}')

# ================================================================ the broom
handle = [(0, -3.4, HOVER + 0.45), (0.1, -2.2, HOVER + 0.3), (-0.1, -0.9, HOVER + 0.12), (0.08, 0.5, HOVER + 0.02),
          (-0.06, 1.8, HOVER - 0.04), (0, 2.85, HOVER)]
m.loft('Broom', 'bark', handle, [(0.16, 0.16), (0.2, 0.2), (0.21, 0.21), (0.2, 0.2), (0.21, 0.21), (0.24, 0.24)], sides=7, steps=3, smooth=False)
# a second thinner branch twisting round the handle
twist = [(math.cos(i * 1.1) * 0.22, -3.0 + i * 0.55, HOVER + 0.38 - i * 0.035 + math.sin(i * 1.1) * 0.22) for i in range(11)]
m.loft('Broom', 'bark2', twist, [(0.07, 0.07)] * len(twist), sides=5, steps=2, smooth=False)
for y in (-2.5, -1.2, 0.3, 1.5):          # knots, twigs and glowing carved rune bands
    m.blob('Broom', 'bark2', (0.12, y, HOVER + 0.28 - 0.04 * y), (0.25, 0.3, 0.25), u=6, v=4)
    ring('Broom', 'glow2', (0, y + 0.35, 0), 0.215, 0.0, HOVER + 0.2 - 0.04 * y, 0.035, n=10)
for y, d in ((-1.8, (0.7, -0.3, 0.5)), (0.9, (-0.6, 0.2, 0.7)), (-0.4, (0.5, 0.4, -0.6))):
    m.spike('Broom', 'bark2', (0.05, y, HOVER + 0.2), d, 0.6, 0.09, snap=False)
# the horned skull mounted on the front, lantern swinging beneath
sk = (0, -3.55, HOVER + 0.55)
m.blob('Broom', 'bone', sk, (0.38, 0.42, 0.36), u=8, v=6)
m.box('Broom', 'bone', add(sk, (0, -0.22, -0.28)), (0.36, 0.3, 0.2), bevel=0.05)
for s in (-1, 1):
    m.blob('Broom', 'eye_dark', add(sk, (0.15 * s, -0.33, 0.05)), (0.1, 0.06, 0.1), u=5, v=4)
    m.blob('Broom', 'glow', add(sk, (0.15 * s, -0.37, 0.05)), (0.05, 0.03, 0.05), u=4, v=3)
    m.loft('Broom', 'bone', [add(sk, (0.25 * s, 0, 0.25)), add(sk, (0.6 * s, 0.2, 0.55)), add(sk, (0.7 * s, 0.45, 0.95))],
           [(0.09, 0.09), (0.06, 0.06), (0.02, 0.02)], sides=5, steps=2, smooth=False)
m.socket('Skull', 'Broom', add(sk, (0, -0.45, 0)))
lc = (0, -2.6, HOVER - 0.75)
for i in range(4):
    m.box('Lantern', 'iron2', lerp((0, -2.6, HOVER + 0.05), add(lc, (0, 0, 0.35)), (i + 0.5) / 4), (0.05, 0.13, 0.16) if i % 2 else (0.13, 0.05, 0.16), bevel=0.0)
m.box('Lantern', 'iron', add(lc, (0, 0, 0.3)), (0.42, 0.42, 0.08), bevel=0.02)
m.box('Lantern', 'ghost', lc, (0.3, 0.3, 0.46), bevel=0.03)
m.box('Lantern', 'iron', add(lc, (0, 0, -0.28)), (0.38, 0.38, 0.08), bevel=0.02)
for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    m.box('Lantern', 'iron', add(lc, (0.16 * dx, 0.16 * dy, 0)), (0.05, 0.05, 0.6), bevel=0.0)
m.socket('Lantern', 'Lantern', lc)
# bristles: a fat flared bundle, bound with rope and chain, roaring with ghost fire
bb = (0, 2.85, HOVER)
for layer, (r, n) in enumerate(((0.3, 9), (0.55, 12), (0.8, 15))):
    for k in range(n):
        a = TAU * (k + 0.5 * layer) / n
        base = add(bb, (math.cos(a) * r * 0.55, 0.12 * layer, math.sin(a) * r * 0.55))
        d = (math.cos(a) * r * 0.55, 1.0, math.sin(a) * r * 0.55 - 0.1)
        m.spike('Broom', 'straw' if (k + layer) % 2 else 'straw2', base, d, 2.1 + 0.3 * layer, 0.24, 0.06, snap=False)
ring('Broom', 'rope', (0, 0, 0), 0.44, 0.44, HOVER, 0.07)   # (placed round the binding below)
for y, col in ((2.95, 'rope'), (3.25, 'iron2'), (3.5, 'rope')):
    m.loft('Broom', col, [(math.cos(TAU * i / 12) * 0.46, y, HOVER + math.sin(TAU * i / 12) * 0.46) for i in range(13)],
           [(0.07, 0.07)] * 13, sides=4, steps=1, smooth=False, cap_round=0.0)
for k in range(9):
    a = TAU * k / 9
    base = add((0, 4.7, HOVER), (math.cos(a) * 0.5, 0, math.sin(a) * 0.5))
    m.spike('Broom', 'ghost' if k % 2 else 'ghost2', base, (math.cos(a) * 0.3, 1.0, math.sin(a) * 0.3 + 0.2), 1.6 + 0.45 * (k % 3), 0.45, snap=False)
m.socket('BroomFire', 'Broom', (0, 5.6, HOVER + 0.2))

# ================================================================ the cauldron
cc = (0, 3.75, HOVER - 2.35)
for s in (-1, 1):
    for i in range(6):
        p = lerp((0.06 * s, 3.75, HOVER - 0.15), (0.62 * s, 3.75, HOVER - 1.65), (i + 0.5) / 6)
        m.box('Cauldron', 'iron2', p, (0.07, 0.16, 0.2) if i % 2 else (0.16, 0.07, 0.2), bevel=0.0)
m.blob('Cauldron', 'iron', cc, (0.92, 0.92, 0.75), u=12, v=8)
ring('Cauldron', 'iron2', cc, 0.82, 0.82, cc[2] + 0.66, 0.12, n=16, sides=5)
for i in range(3):
    a = TAU * i / 3 + 0.5
    m.box('Cauldron', 'iron2', (cc[0] + math.cos(a) * 0.6, cc[1] + math.sin(a) * 0.6, cc[2] - 0.75), (0.2, 0.2, 0.35), bevel=0.04)
for s in (-1, 1):   # skull handles
    h = (cc[0] + 0.98 * s, cc[1], cc[2] + 0.3)
    m.blob('Cauldron', 'bone', h, (0.2, 0.22, 0.22), u=6, v=5)
    m.blob('Cauldron', 'eye_dark', add(h, (0.12 * s, -0.08, 0.03)), (0.05, 0.05, 0.06), u=4, v=3)
    m.blob('Cauldron', 'eye_dark', add(h, (0.12 * s, 0.08, 0.03)), (0.05, 0.05, 0.06), u=4, v=3)
m.blob('Cauldron', 'brew', (cc[0], cc[1], cc[2] + 0.6), (0.72, 0.72, 0.1), u=10, v=3)
for i in range(6):
    a = TAU * i / 6 + 0.3
    r = 0.12 + 0.05 * (i % 2)
    m.blob('Cauldron', 'glow', (cc[0] + math.cos(a) * 0.4, cc[1] + math.sin(a) * 0.4, cc[2] + 0.72 + r * 0.4), (r, r, r), u=5, v=4)
for k in range(5):   # brew slopping over the rim and dripping
    a = TAU * k / 5 + 0.2
    top = (cc[0] + math.cos(a) * 0.82, cc[1] + math.sin(a) * 0.82, cc[2] + 0.62)
    m.loft('Cauldron', 'brew', [top, add(top, (math.cos(a) * 0.06, math.sin(a) * 0.06, -0.4 - 0.15 * (k % 2)))], [(0.07, 0.07), (0.05, 0.05)],
           sides=4, steps=1, smooth=False)
m.loft('Cauldron', 'bone', [(cc[0] - 0.35, cc[1] - 0.2, cc[2] + 0.5), (cc[0] + 0.3, cc[1] + 0.3, cc[2] + 1.2)], [(0.07, 0.07)] * 2, sides=5, steps=1, smooth=False)
m.socket('Cauldron', 'Cauldron', (cc[0], cc[1], cc[2] + 0.95))

# ================================================================ the familiar: a black cat on the broom
cat = (0, 1.75, HOVER + 0.55)
m.blob('Cat', 'cat', cat, (0.32, 0.45, 0.32), u=8, v=6)
m.blob('Cat', 'cat', add(cat, (0, -0.2, 0.42)), (0.26, 0.24, 0.24), u=8, v=6)
for s in (-1, 1):
    m.spike('Cat', 'cat2', add(cat, (0.15 * s, -0.15, 0.6)), (0.3 * s, 0.1, 1), 0.3, 0.16, 0.05)
    m.blob('Cat', 'glow', add(cat, (0.1 * s, -0.42, 0.45)), (0.06, 0.03, 0.05), u=5, v=4)
    for dy in (-0.25, 0.25):
        m.loft('Cat', 'cat', [add(cat, (0.18 * s, dy, -0.1)), add(cat, (0.24 * s, dy, -0.45))], [(0.06, 0.06), (0.05, 0.05)], sides=5, steps=1, smooth=False)
m.socket('CatEyes', 'Cat', add(cat, (0, -0.48, 0.45)))
tail = [(0, 2.15, HOVER + 0.5), (0, 2.5, HOVER + 0.6), (0, 2.75, HOVER + 0.95), (0, 2.65, HOVER + 1.3)]
m.loft('CatTail', 'cat2', tail, [(0.07, 0.07), (0.06, 0.06), (0.05, 0.05), (0.03, 0.03)], sides=5, steps=2, smooth=False)

# ================================================================ robes, shawl and cape
m.blob('Hips', 'robe', (0, 0.45, HOVER + 0.6), (1.1, 1.05, 0.8), u=10, v=7)
for layer, (col, r, ln) in enumerate((('robe2', 1.3, 2.8), ('robe', 1.1, 2.4), ('robe3', 0.9, 2.0))):
    for k in range(10):
        a = math.pi * 0.12 + math.pi * 1.76 * k / 9
        top = (math.sin(a) * r * 0.85, 0.45 + math.cos(a) * 0.4 * r, HOVER + 0.65 - 0.15 * layer)
        bottom = (math.sin(a) * r * 1.3, 1.4 + 0.7 * abs(math.cos(a)), HOVER - ln + 0.45 * ((k + layer) % 2))
        m.loft('Robe', col, [top, lerp(top, bottom, 0.5), bottom], [(0.42, 0.06), (0.4, 0.06), (0.1, 0.04)],
               sides=4, steps=2, smooth=False, up=(0, -1, 0))
        if layer == 0 and k % 2 == 0:
            m.spike('Robe', 'ghost', bottom, (0, 0.5, -1), 1.0, 0.32, snap=False)
        if layer == 1 and k % 3 == 1:   # a patch sewn on
            p = lerp(top, bottom, 0.4)
            m.box('Robe', 'patch', add(p, (math.sin(a) * 0.05, 0, 0)), (0.32, 0.06, 0.3), rot=(0, 0, math.degrees(a)), bevel=0.0)
# bodice with criss-cross lacing
m.box('Chest', 'robe', (0, 0.3, HOVER + 1.85), (1.35, 1.0, 1.45), bevel=0.25, taper=dict(axis='z', end=1, scale=(0.72, 0.78)))
m.box('Chest', 'robe2', (0, -0.22, HOVER + 1.8), (0.55, 0.14, 1.3), bevel=0.05)
for i in range(5):
    z = HOVER + 1.25 + 0.27 * i
    for s in (-1, 1):
        m.box('Chest', 'lace', (0, -0.31, z), (0.5, 0.04, 0.04), rot=(0, 30 * s, 0), bevel=0.0)
    for s in (-1, 1):
        m.blob('Chest', 'gold', (0.22 * s, -0.31, z), (0.035, 0.03, 0.035), u=4, v=3)
# belt: potion bottles, a chained spellbook, a skull
ring('Hips', 'leather', (0, 0.35, 0), 0.82, 0.62, HOVER + 1.18, 0.13, n=14)
m.box('Hips', 'gold', (0, -0.3, HOVER + 1.18), (0.28, 0.06, 0.24), bevel=0.02)
for i, (x, col) in enumerate(((0.55, 'glow'), (0.72, 'glow2'), (-0.6, 'ghost'))):
    b = (x, -0.12 + 0.18 * i, HOVER + 0.92)
    m.blob('Hips', col, b, (0.11, 0.11, 0.14), u=6, v=5)
    m.loft('Hips', 'glass', [add(b, (0, 0, 0.12)), add(b, (0, 0, 0.26))], [(0.04, 0.04)] * 2, sides=5, steps=1, smooth=False)
    m.blob('Hips', 'leather', add(b, (0, 0, 0.29)), (0.05, 0.05, 0.04), u=4, v=3)
bk = (-0.75, 0.55, HOVER + 0.75)
m.box('Hips', 'book', bk, (0.18, 0.55, 0.62), rot=(0, 0, -20), bevel=0.03)
m.box('Hips', 'page', add(bk, (0.02, 0, 0)), (0.16, 0.5, 0.56), rot=(0, 0, -20), bevel=0.0)
m.box('Hips', 'gold', add(bk, (-0.1, -0.03, 0)), (0.02, 0.25, 0.25), rot=(0, 0, -20), bevel=0.0)
for i in range(3):
    m.box('Hips', 'iron2', lerp((-0.7, 0.3, HOVER + 1.1), add(bk, (0, 0, 0.32)), (i + 0.5) / 3), (0.06, 0.12, 0.12), bevel=0.0)
m.blob('Hips', 'bone', (0.25, -0.35, HOVER + 0.9), (0.12, 0.1, 0.13), u=6, v=4)
# ragged shawl over the shoulders, and a long torn cape streaming behind
for k in range(11):
    a = math.pi * 0.15 + math.pi * 1.7 * k / 10
    top = (math.sin(a) * 0.62, 0.3 + math.cos(a) * 0.5, HOVER + 2.45)
    bot = (math.sin(a) * 0.95, 0.3 + math.cos(a) * 0.7, HOVER + 1.75 - 0.18 * (k % 2))
    m.loft('Chest', 'shawl', [top, bot], [(0.3, 0.05), (0.08, 0.04)], sides=4, steps=1, smooth=False, up=(0, -1, 0))
for k in range(7):
    x = -0.9 + 0.3 * k
    top = (x * 0.8, 0.75, HOVER + 2.35)
    mid = (x * 1.1, 1.8, HOVER + 1.6)
    bot = (x * 1.3, 2.8 + 0.3 * (k % 2), HOVER + 0.6 - 0.4 * (k % 2))
    m.loft('Cape', 'robe2', [top, mid, bot], [(0.17, 0.04), (0.19, 0.04), (0.05, 0.03)], sides=4, steps=2, smooth=False, up=(0, 1, 0))
    if k % 2 == 0:
        m.spike('Cape', 'ghost', bot, (0, 1, -0.3), 0.8, 0.25, snap=False)
# tattered high collar
for k in range(8):
    a = math.pi * 0.55 + math.pi * 0.9 * k / 7
    m.spike('Chest', 'robe2', (math.cos(a) * 0.55, 0.25 + math.sin(a) * 0.42, HOVER + 2.55), (math.cos(a), math.sin(a) * 0.6 + 0.35, 1.2), 0.8, 0.3, 0.05)

# ================================================================ arms and long bony hands
for side, s in SIDES:
    sh, el, wr, tip = ARM[side]
    m.loft([f'Arm{side}', f'Fore{side}'], 'robe', [sh, el, wr], [(0.3, 0.3), (0.28, 0.28), (0.45, 0.45)], sides=7, steps=2, smooth=False)
    for k in range(6):   # ragged flared cuff
        a = TAU * k / 6
        m.spike(f'Fore{side}', 'robe2' if k % 2 else 'robe3', lerp(el, wr, 0.88), (math.cos(a) * 0.7, 0.2, math.sin(a) * 0.7 - 0.6), 0.65, 0.24, 0.05)
    m.loft(f'Fore{side}', 'skin2', [lerp(el, wr, 0.8), wr], [(0.13, 0.13), (0.11, 0.11)], sides=6, steps=1, smooth=False)   # bony wrist
    palm = lerp(wr, tip, 0.3)
    m.box(f'Hand{side}', 'skin', palm, (0.32, 0.12, 0.3), rot=(0, 0, 0), bevel=0.05)
    fwd = tuple((b - a) for a, b in zip(wr, tip))
    n = math.sqrt(sum(v * v for v in fwd))
    fwd = tuple(v / n for v in fwd)
    for k in range(4):   # four long knuckled fingers with claws, and rings
        off = (-0.15 + 0.1 * k) * s
        base = add(palm, (off, 0, 0))
        knuckle = add(base, tuple(v * 0.3 for v in fwd))
        end = add(knuckle, (fwd[0] * 0.3, fwd[1] * 0.3 - 0.1, fwd[2] * 0.3 - 0.08))
        m.loft(f'Hand{side}', 'skin2', [base, knuckle, end], [(0.045, 0.045), (0.05, 0.05), (0.035, 0.035)], sides=4, steps=1, smooth=False)
        m.blob(f'Hand{side}', 'skin3', knuckle, (0.06, 0.06, 0.06), u=4, v=3)
        m.spike(f'Hand{side}', 'claw', end, (fwd[0], fwd[1] - 0.4, fwd[2] - 0.5), 0.22, 0.045, snap=False)
        if k in (1, 3):
            ring(f'Hand{side}', 'ring', (base[0], base[1], 0), 0.06, 0.06, base[2] + 0.12, 0.025, n=8)
    m.loft(f'Hand{side}', 'skin2', [add(palm, (0.18 * s, 0, 0)), add(palm, (0.3 * s, -0.15, 0.12))], [(0.05, 0.05), (0.035, 0.035)], sides=4, steps=1, smooth=False)   # thumb
m.socket('HandL', 'HandL', ARM['L'][3])
orb = add(ARM['R'][3], (0, -0.15, 0.45))
m.blob('HandR', 'ghost', orb, (0.42, 0.42, 0.42), u=8, v=6)
m.blob('HandR', 'ghost2', orb, (0.22, 0.22, 0.22), u=6, v=4)
for k in range(5):   # wisps curling off the orb
    a = TAU * k / 5
    m.spike('HandR', 'ghost', add(orb, (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.1)), (math.cos(a), math.sin(a), 0.8), 0.45, 0.13, snap=False)
m.socket('Orb', 'HandR', orb)

# ================================================================ the head
m.loft('Neck', 'skin2', [(0, 0.15, HOVER + 2.3), Hd(0, 0.05, -0.6)], [(0.25, 0.25), (0.2, 0.2)], sides=6, steps=1, smooth=False)
for s in (-1, 1):   # stringy neck tendons
    m.loft('Neck', 'skin3', [(0.12 * s, -0.02, HOVER + 2.4), Hd(0.1 * s, -0.12, -0.55)], [(0.05, 0.05)] * 2, sides=4, steps=1, smooth=False)
m.blob('Head', 'skin', Hd(0, -0.1, 0.1), (0.6, 0.6, 0.72), u=10, v=8)
m.box('Head', 'skin2', Hd(0, -0.3, -0.45), (0.62, 0.55, 0.45), bevel=0.15, taper=dict(axis='z', end=-1, scale=(0.42, 0.55)))
m.spike('Head', 'skin2', Hd(0, -0.55, -0.82), (0, -0.55, -1), 0.45, 0.2)          # jutting pointed chin
m.blob('Head', 'wart', Hd(0.05, -0.75, -0.95), (0.05, 0.05, 0.05), u=4, v=3)
for s in (-1, 1):   # sharp cheekbones and hollow cheeks
    m.box('Head', 'skin', Hd(0.38 * s, -0.42, 0.05), (0.18, 0.3, 0.14), rot=(0, 0, -20 * s), bevel=0.04)
    m.blob('Head', 'skin3', Hd(0.36 * s, -0.42, -0.25), (0.12, 0.08, 0.14), u=5, v=4)
nose = [Hd(0, -0.62, 0.22), Hd(0.05, -0.98, 0.1), Hd(-0.03, -1.32, -0.12), Hd(0.02, -1.42, -0.35), Hd(0, -1.3, -0.48)]
m.loft('Head', 'skin2', nose, [(0.15, 0.17), (0.12, 0.13), (0.09, 0.1), (0.06, 0.06), (0.03, 0.03)], sides=6, steps=2, smooth=False)
for p in (Hd(0.09, -1.05, 0.12), Hd(-0.07, -1.3, -0.05)):
    m.blob('Head', 'wart', p, (0.06, 0.06, 0.06), u=5, v=4)
# deep wrinkles: forehead, crow's feet, around the mouth
for i in range(3):
    z = 0.42 + 0.1 * i
    m.loft('Head', 'wrinkle', [Hd(-0.3, -0.62 + 0.03 * i, z), Hd(0, -0.68, z + 0.03), Hd(0.3, -0.62 + 0.03 * i, z)], [(0.018, 0.018)] * 3, sides=3, steps=1, smooth=False)
for s in (-1, 1):
    for k in range(3):
        m.loft('Head', 'wrinkle', [Hd(0.42 * s, -0.5, 0.22), Hd(0.55 * s, -0.42, 0.14 + 0.08 * k)], [(0.015, 0.015)] * 2, sides=3, steps=1, smooth=False)
    m.loft('Head', 'wrinkle', [Hd(0.18 * s, -0.66, -0.12), Hd(0.27 * s, -0.66, -0.4)], [(0.02, 0.02)] * 2, sides=3, steps=1, smooth=False)
# the grin: dark mouth, snaggled teeth top and bottom
m.box('Head', 'mouth', Hd(0, -0.62, -0.38), (0.52, 0.16, 0.12), bevel=0.0)
m.box('Jaw', 'skin2', Hd(0, -0.62, -0.52), (0.5, 0.22, 0.12), bevel=0.03)
for i, (x, ln) in enumerate(((-0.18, 0.16), (-0.05, 0.1), (0.07, 0.14), (0.19, 0.11))):
    m.spike('Head', 'tooth', Hd(x, -0.7, -0.33), (0.1 * (i % 2 - 0.5), -0.15, -1), ln, 0.06, snap=False)
for x in (-0.12, 0.13):
    m.spike('Jaw', 'tooth', Hd(x, -0.7, -0.48), (0, -0.15, 1), 0.1, 0.05, snap=False)
# hollow sockets, burning eyes, wild brows
for side, s in SIDES:
    m.blob('Head', 'eye_dark', Hd(0.24 * s, -0.53, 0.26), (0.19, 0.1, 0.15), u=6, v=4)
    m.eye('Head', Hd(0.24 * s, -0.6, 0.26), (0.3 * s, -1, 0.1), 0.15)
    m.socket(f'Eye{side}', 'Head', Hd(0.24 * s, -0.7, 0.26))
    for k in range(4):   # bushy angry brow tufts
        m.spike('Head', 'hair2', Hd((0.1 + 0.08 * k) * s, -0.58, 0.44 - 0.02 * k), (0.6 * s, -0.4, 0.35 - 0.15 * k), 0.24, 0.07, 0.04)
    # long pointed ears with iron rings
    m.spike('Head', 'skin', Hd(0.56 * s, -0.05, 0.12), (s, 0.5, 0.35), 0.55, 0.22, 0.06)
    ring('Head', 'ring', (HEAD[0] + 0.66 * s, HEAD[1] + 0.02, 0), 0.07, 0.07, HEAD[2] + 0.05, 0.025, n=8)
# a mane of wild white hair whipping back from under the hat
for k in range(17):
    a = math.pi * 0.2 + math.pi * 1.6 * k / 16
    base = Hd(math.sin(a) * 0.56, math.cos(a) * 0.38 + 0.15, 0.3)
    d = (math.sin(a) * 0.9, 1.0 + 0.3 * abs(math.cos(a)), -0.4 - 0.25 * (k % 3))
    m.spike('Head', 'hair' if k % 2 else 'hair2', base, d, 1.4 + 0.45 * (k % 3), 0.28, 0.08)

# ================================================================ the hat
brim_c = Hd(0, 0.3, 0.78)   # set back on the skull so the face shows
m.loft('Hat', 'hat', [add(brim_c, (0, 0, -0.06)), add(brim_c, (0, 0, 0.08))], [(1.3, 1.2), (1.24, 1.15)], sides=13, steps=1, smooth=False)
for k in range(13):   # a wavy, drooping brim edge
    a = TAU * k / 13
    m.blob('Hat', 'hat', add(brim_c, (math.cos(a) * 1.22, math.sin(a) * 1.12, 0.02 + 0.1 * (k % 2))), (0.24, 0.24, 0.07), u=5, v=3)
cone = [add(brim_c, (0, 0, 0.05)), add(brim_c, (0.04, 0.12, 0.7)), add(brim_c, (0.1, 0.33, 1.34))]
m.loft('Hat', 'hat2', cone, [(0.86, 0.82), (0.62, 0.6), (0.42, 0.4)], sides=10, steps=2, smooth=False)
tipc = [add(brim_c, (0.1, 0.33, 1.34)), add(brim_c, (0.3, 0.6, 1.85)), add(brim_c, (0.75, 1.0, 2.2)), add(brim_c, (1.15, 1.35, 2.05))]
m.loft('HatTip', 'hat2', tipc, [(0.42, 0.4), (0.27, 0.26), (0.13, 0.12), (0.04, 0.04)], sides=9, steps=3, smooth=False)
# patches and big stitches
for p, rot in ((add(brim_c, (0.62, -0.42, 0.6)), 30), (add(brim_c, (-0.48, -0.5, 0.95)), -25)):
    m.box('Hat', 'patch', p, (0.36, 0.06, 0.34), rot=(0, 0, rot), bevel=0.01)
    for k in range(4):
        m.box('Hat', 'stitch', add(p, (-0.13 + 0.09 * k, -0.04, 0.18)), (0.03, 0.03, 0.1), rot=(0, 0, rot), bevel=0.0)
ring('Hat', 'band', brim_c, 0.86, 0.82, brim_c[2] + 0.22, 0.13, n=14)
m.box('Hat', 'gold', add(brim_c, (0, -0.87, 0.22)), (0.42, 0.06, 0.34), bevel=0.02)
m.box('Hat', 'hat', add(brim_c, (0, -0.89, 0.22)), (0.22, 0.06, 0.16), bevel=0.0)
# cobweb strung under one side of the brim
for k in range(5):
    a = -0.9 + 0.45 * k
    m.loft('Hat', 'web', [add(brim_c, (math.cos(a) * 0.9, math.sin(a) * 0.8 - 0.2, 0.02)), add(brim_c, (math.cos(a) * 1.18, math.sin(a) * 1.08, -0.02))],
           [(0.015, 0.015)] * 2, sides=3, steps=1, smooth=False)
for rr in (0.95, 1.12):
    pts = [add(brim_c, (math.cos(a) * rr, math.sin(a) * rr * 0.9, -0.06)) for a in (-0.9, -0.45, 0.0, 0.45, 0.9)]
    m.loft('Hat', 'web', pts, [(0.012, 0.012)] * 5, sides=3, steps=1, smooth=False)
# candles on the brim, melting, lit
for i, ang in enumerate((-2.2, -0.2, 2.0)):
    base = add(brim_c, (math.sin(ang) * 1.0, -math.cos(ang) * 0.95, 0.08))
    top = add(base, (0, 0, 0.6 - 0.12 * i))
    m.loft('Hat', 'candle', [base, top], [(0.11, 0.11), (0.1, 0.1)], sides=6, steps=1, smooth=False)
    for k in range(2):
        a = k * 2.5 + i
        m.loft('Hat', 'candle', [add(top, (math.cos(a) * 0.09, math.sin(a) * 0.09, -0.02)), add(top, (math.cos(a) * 0.11, math.sin(a) * 0.11, -0.35))],
               [(0.03, 0.03), (0.04, 0.04)], sides=4, steps=1, smooth=False)
    m.spike('Hat', 'flame', add(top, (0, 0, 0.04)), (0, 0, 1), 0.32, 0.11, snap=False)
    m.socket(f'Candle{i + 1}', 'Hat', add(top, (0, 0, 0.25)))
# a tiny bat charm dangling from the bent tip
tip = tipc[-1]
m.loft('HatTip', 'iron2', [tip, add(tip, (0, 0, -0.45))], [(0.015, 0.015)] * 2, sides=3, steps=1, smooth=False)
bat = add(tip, (0, 0, -0.55))
m.blob('HatTip', 'cat', bat, (0.09, 0.08, 0.11), u=5, v=4)
for s in (-1, 1):
    m.strip('HatTip', 'cat2', [add(bat, (0, 0, 0.05)), add(bat, (0.25 * s, 0, 0.0)), add(bat, (0.3 * s, 0, -0.15))],
            [add(bat, (0, 0, -0.05)), add(bat, (0.15 * s, 0, -0.08)), add(bat, (0.2 * s, 0, -0.15))], thickness=0.03)


# ================================================================ animation
def pose0():
    return {}


def fly(pose, p, bob, lean, sway, cape=0.0):
    pose['MonsterRoot'] = ((0, 0, 0), (0, 0, bob))
    pose['Broom'] = ((lean, sway, 0), (0, 0, 0))
    pose['Robe'] = ((-8 + 6 * math.sin(p * 2) - cape * 0.5, 0, 6 * math.sin(p * 3)), (0, 0, 0))
    pose['Cape'] = ((-10 - cape + 8 * math.sin(p * 2.5), 0, 7 * math.sin(p * 1.7)), (0, 0, 0))
    pose['Cauldron'] = ((10 * math.sin(p + 1) - lean * 0.7, 0, 6 * math.sin(p * 0.7)), (0, 0, 0))
    pose['Lantern'] = ((14 * math.sin(p * 1.3 + 2) - lean * 0.8, 0, 8 * math.sin(p)), (0, 0, 0))
    pose['CatTail'] = ((20 * math.sin(p * 2), 0, 25 * math.sin(p * 1.5)), (0, 0, 0))
    pose['HatTip'] = ((-cape * 0.6 + 8 * math.sin(p * 2 + 1), 0, 10 * math.sin(p * 1.4)), (0, 0, 0))


def arms(pose, l=0.0, r=0.0, fl=0.0, fr=0.0, hl=0.0, hr=0.0, rzl=0.0, rzr=0.0):
    pose['ArmL'] = ((l, 0, rzl), (0, 0, 0))
    pose['ArmR'] = ((r, 0, rzr), (0, 0, 0))
    pose['ForeL'] = ((fl, 0, 0), (0, 0, 0))
    pose['ForeR'] = ((fr, 0, 0), (0, 0, 0))
    pose['HandL'] = ((hl, 0, 0), (0, 0, 0))
    pose['HandR'] = ((hr, 0, 0), (0, 0, 0))


def body(pose, chest=0.0, neck=0.0, head=0.0, jaw=4.0, turn=0.0, tilt=0.0, hat=0.0, cat=0.0):
    pose['Chest'] = ((chest, 0, turn * 0.4), (0, 0, 0))
    pose['Neck'] = ((neck, 0, turn * 0.3), (0, 0, 0))
    pose['Head'] = ((head, tilt, turn * 0.5), (0, 0, 0))
    pose['Jaw'] = ((jaw, 0, 0), (0, 0, 0))
    pose['Hat'] = ((hat, 0, 0), (0, 0, 0))
    pose['Cat'] = ((cat, 0, 0), (0, 0, 0))


def idle(t_):   # hovering menacingly: rocking, peering round, fingers flexing, the orb pulsing
    p = TAU * t_
    pose = {}
    fly(pose, p, 0.35 * S * math.sin(p * 2), 3 * math.sin(p), 4 * math.sin(p * 0.5))
    body(pose, chest=3 * math.sin(p), neck=-4 * math.sin(p * 2), head=6 * math.sin(p * 2 + 1), jaw=4 + 4 * math.sin(p * 3),
         turn=24 * math.sin(p), tilt=6 * math.sin(p * 0.5), hat=3 * math.sin(p * 2 + 1), cat=5 * math.sin(p * 2))
    arms(pose, r=8 * math.sin(p * 2), fr=-6 * math.sin(p * 2), hl=8 * math.sin(p * 3), hr=-15 * math.sin(p * 4))
    return pose


def walk(t_):   # cruising: leaning into it, cape and hat streaming
    p = TAU * t_
    pose = {}
    fly(pose, p, 0.3 * S * math.sin(p * 2), 8, 8 * math.sin(p), cape=15)
    body(pose, chest=10, neck=-6, head=-8, jaw=6, turn=10 * math.sin(p), hat=-10)
    arms(pose, r=-12, fr=-10)
    return pose


def run(t_):    # full speed: low, flat and banking hard
    p = TAU * t_
    pose = {}
    fly(pose, p, 0.2 * S * math.sin(p * 2), 15, 18 * math.sin(p), cape=30)
    body(pose, chest=22, neck=-10, head=-16, jaw=14, hat=-22, cat=-15)
    arms(pose, r=-45, fr=-20)
    return pose


def sleep(t_):   # slumped, drifting, muttering
    p = TAU * t_
    pose = {}
    fly(pose, p, 0.15 * S * math.sin(p), 0, 0)
    body(pose, chest=18, neck=12, head=20, jaw=6 * math.sin(p * 2), tilt=10, hat=8, cat=15)
    arms(pose, r=40, fr=30, hr=20)
    return pose


def roar(t_):    # the cackle: head thrown back, jaw wide, both arms flung out, shaking with laughter
    e = envelope(t_, 0.12, 0.85)
    sh = math.sin(TAU * 12 * t_) * e
    pose = {}
    fly(pose, TAU * t_, 0.7 * S * e, -12 * e, 5 * sh, cape=20 * e)
    body(pose, chest=-18 * e + 3 * sh, neck=-15 * e, head=-25 * e + 5 * sh, jaw=42 * e, tilt=8 * sh, hat=-15 * e, cat=-20 * e)
    arms(pose, l=-55 * e, r=-75 * e, fl=-30 * e, fr=-20 * e, hl=-30 * e, hr=-30 * e, rzl=-35 * e, rzr=35 * e)
    return pose


def attack(t_):  # the swoop: rear up, then dive and snatch with a clawed hand
    w = envelope(t_, 0.3, 0.32, 0.45)
    d = smooth01((t_ - 0.32) / 0.15) if t_ < 0.6 else 1 - smooth01((t_ - 0.6) / 0.4)
    pose = {}
    fly(pose, TAU * t_, (1.0 * w - 1.8 * d) * S, -22 * w + 32 * d, 0, cape=30 * d)
    body(pose, chest=-15 * w + 35 * d, neck=-10 * d, head=10 * w - 20 * d, jaw=10 + 25 * d, hat=-20 * d)
    arms(pose, l=-30 * w + 70 * d, fl=-20 * d, hl=-40 * d + 30 * w, r=-60 * w + 40 * d, fr=-30 * w)
    pose['MonsterRoot'] = ((0, 0, 0), (0, -2.5 * S * d, (1.0 * w - 1.8 * d) * S))
    return pose


def cast(t_):    # ghost bolt: draw the orb back over the shoulder, then hurl it forward
    w = envelope(t_, 0.35, 0.38, 0.5)
    f = smooth01((t_ - 0.38) / 0.1) if t_ < 0.7 else 1 - smooth01((t_ - 0.7) / 0.3)
    pose = {}
    fly(pose, TAU * t_, 0.2 * S * math.sin(TAU * t_ * 2), -8 * w + 10 * f, 0, cape=10 * f)
    body(pose, chest=-12 * w + 18 * f, head=8 * w - 10 * f, jaw=8 + 30 * f, turn=-30 * w + 20 * f, hat=-10 * f)
    arms(pose, r=-70 * w + 130 * f, fr=-40 * w + 50 * f, hr=-50 * w + 60 * f, rzr=30 * w - 20 * f, l=-10 * w)
    return pose


def summon(t_):  # both arms raised, the broom rising and spinning: the bats come
    e = envelope(t_, 0.25, 0.8)
    pulse = math.sin(TAU * 4 * t_) * e
    pose = {}
    fly(pose, TAU * t_, 1.4 * S * e, -6 * e, 0, cape=25 * e)
    pose['MonsterRoot'] = ((0, 0, 360 * smooth01(t_ / 0.9) if t_ < 0.9 else 360), (0, 0, 1.4 * S * e))
    body(pose, chest=-20 * e, neck=-12 * e, head=-30 * e, jaw=30 * e + 8 * pulse, hat=-15 * e, cat=-25 * e)
    arms(pose, l=-150 * e, r=-150 * e, fl=-10 * e + 6 * pulse, fr=-10 * e - 6 * pulse, hl=-30 * e, hr=-30 * e, rzl=-25 * e, rzr=25 * e)
    return pose


def slam(t_):    # rise high, then plunge to the ground: shockwave
    up = smooth01(t_ / 0.4) if t_ < 0.4 else 1.0
    down = smooth01((t_ - 0.45) / 0.1) if t_ > 0.45 else 0.0
    rec = smooth01((t_ - 0.75) / 0.25) if t_ > 0.75 else 0.0
    h = (4.0 * up - 8.0 * down + 4.0 * rec) * S
    pose = {}
    fly(pose, TAU * t_, h, -25 * up + 55 * down - 30 * rec, 0, cape=-20 * down + 35 * up)
    body(pose, chest=-20 * up + 45 * down - 25 * rec, head=-20 * up + 25 * down, jaw=10 + 35 * down, hat=30 * down - 20 * up)
    arms(pose, l=-160 * up + 190 * down - 30 * rec, r=-160 * up + 190 * down - 30 * rec, fl=-20 * up, fr=-20 * up, rzl=-20 * up, rzr=20 * up)
    pose['MonsterRoot'] = ((0, 0, 0), (0, 0, h))
    return pose


def stagger(t_):  # bonked: knocked back, broom tipping wildly, head lolling, dizzy, then recovers
    hit = 1 - smooth01(t_ / 0.25)
    wob = math.sin(TAU * 3 * t_) * envelope(t_, 0.05, 0.75, 1.0)
    rec = smooth01((t_ - 0.75) / 0.25) if t_ > 0.75 else 0.0
    k = 1 - rec
    pose = {}
    fly(pose, TAU * t_, (-0.8 * k + 0.3 * wob) * S, -35 * hit * k + 10 * wob * k, 25 * wob * k, cape=-25 * hit)
    pose['MonsterRoot'] = ((0, 0, 15 * wob * k), (0, 1.5 * S * (1 - hit) * k * 0.5, (-0.8 * k + 0.3 * wob) * S))
    body(pose, chest=-28 * hit * k + 8 * wob * k, neck=20 * k, head=25 * k + 12 * wob * k, jaw=25 * k, tilt=25 * wob * k, hat=-25 * hit + 15 * wob * k, cat=-40 * hit)
    arms(pose, l=-40 * k, r=10 * k, fl=-30 * k * wob, fr=40 * k, hl=30 * k, hr=40 * k, rzl=-40 * k, rzr=50 * k)
    return pose


def enrage(t_):  # phase change: curls up tight, then bursts out screaming, arms wide
    curl = envelope(t_, 0.15, 0.4, 0.5)
    burst = smooth01((t_ - 0.45) / 0.1) if t_ < 0.85 else 1 - smooth01((t_ - 0.85) / 0.15)
    sh = math.sin(TAU * 16 * t_) * burst
    pose = {}
    fly(pose, TAU * t_, (0.4 * curl + 1.6 * burst) * S, 20 * curl - 18 * burst, 4 * sh, cape=45 * burst)
    body(pose, chest=35 * curl - 30 * burst, neck=25 * curl - 15 * burst, head=25 * curl - 35 * burst + 4 * sh, jaw=50 * burst, tilt=6 * sh,
         hat=20 * curl - 25 * burst, cat=-30 * burst)
    arms(pose, l=60 * curl - 110 * burst, r=60 * curl - 110 * burst, fl=60 * curl - 20 * burst, fr=60 * curl - 20 * burst,
         hl=40 * curl - 40 * burst, hr=40 * curl - 40 * burst, rzl=20 * curl - 60 * burst, rzr=-20 * curl + 60 * burst)
    return pose


def death(t_):   # defeated: a long shriek, then she spirals down and crashes (holds the last frame)
    e = envelope(t_, 0.1, 0.35, 0.45)
    fall = smooth01((t_ - 0.35) / 0.55) if t_ > 0.35 else 0.0
    pose = {}
    fly(pose, TAU * t_, -HOVER * 0.95 * fall * S, -15 * e + 40 * fall, 0, cape=30 * e)
    pose['MonsterRoot'] = ((0, 0, 540 * fall), (0, 0, -HOVER * 0.95 * fall * S))
    body(pose, chest=-25 * e + 45 * fall, neck=-15 * e + 25 * fall, head=-30 * e + 35 * fall, jaw=50 * e + 20 * fall, tilt=25 * fall, hat=-30 * e + 40 * fall, cat=-50 * fall)
    arms(pose, l=-90 * e + 60 * fall, r=-100 * e + 70 * fall, fl=-30 * e, fr=-30 * e, rzl=-40 * e - 30 * fall, rzr=40 * e + 30 * fall)
    return pose


def happy(t_):   # a loop-the-loop, cackling
    e = envelope(t_, 0.08, 0.85)
    spin = 360 * smooth01(t_ / 0.85) if t_ < 0.85 else 360
    pose = {}
    fly(pose, TAU * t_, 1.4 * S * math.sin(math.pi * min(1.0, t_ / 0.85)), -spin, 0, cape=20 * e)
    body(pose, head=-15 * e, jaw=30 * e)
    arms(pose, r=-90 * e, fr=-20 * e)
    return pose


m.anim('Idle', 80, True, idle, key_step=2)
m.anim('Walk', 40, True, walk, key_step=2)
m.anim('Run', 30, True, run, key_step=1)
m.anim('Sleep', 96, True, sleep, key_step=8)
m.anim('Roar', 60, False, roar, key_step=1)
m.anim('Attack', 42, False, attack, key_step=1)
m.anim('Cast', 36, False, cast, key_step=1)
m.anim('Summon', 72, False, summon, key_step=1)
m.anim('Slam', 60, False, slam, key_step=1)
m.anim('Stagger', 54, False, stagger, key_step=1)
m.anim('Enrage', 66, False, enrage, key_step=1)
m.anim('Death', 90, False, death, key_step=1)
m.anim('Happy', 48, False, happy, key_step=1)
m.refs = {'Walk': 8.0 * S, 'Run': 14.0 * S}
m.build(OUT)
