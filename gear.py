"""Gear props (static meshes): the baseball bat and five treadmill tiers.
    blender -b --factory-startup --python gear.py -- <out_dir> <Bat|Treadmill1..5|TreadmillBelt> [--live]

Treadmills: deck 3.2 wide x 6 long (Y), runner faces -Y toward the console. The moving belt is not
in the mesh - the game lays a scrolling belt where TreadmillBelt marks it (shared by every tier).

The treadmills are a "speed machines" line from junk to sci-fi, in clean glossy colours (no fabric
dots) - their own look, separate from the monsters:
    1 Street Sprinter sleek white gym machine: curved shell, LED strips, speakers, water bottle
    2 Turbo Trainer   hot-rod: V8 + supercharger, chrome headers, car wheels, flames, spoiler
    3 Rocket Rig      launch pad: boosters with bell nozzles, fins, trusses, dials, radar dish
    4 Scrap Runner    junkyard contraption: pallet deck, oil-barrel motor, cogs, CRT on a crate
    5 Hyperdrive      hovering sci-fi hull: hover pads, ribbed neon arches, reactor with orbit rings
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from kit import Monster

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = args[0] if args else os.path.join(os.path.dirname(__file__), 'export')
WHAT = args[1] if len(args) > 1 else 'Bat'
TAU = math.tau

# tier order chosen in Studio: 1 Street Sprinter, 2 Turbo Trainer, 3 Rocket Rig, 4 Scrap Runner, 5 Hyperdrive
TIERS = {1: 'Street Sprinter', 2: 'Turbo Trainer', 3: 'Rocket Rig', 4: 'Scrap Runner', 5: 'Hyperdrive'}

# belt marker (design units) - same for every tier
BELT = dict(center=(0, 0.45, 0.66), size=(2.2, 4.5, 0.06))

# VFX anchor points (design units) the game uses
ANCHORS = {
    2: {'Exhaust': [(1.05, 3.45, 0.62), (-1.05, 3.45, 0.62)]},
    3: {'Thruster': [(2.05, 3.55, 1.05), (-2.05, 3.55, 1.05)]},
    5: {'Core': [(0, 3.35, 1.55)], 'Hover': [(1.3, -2.2, -0.15), (-1.3, -2.2, -0.15), (1.3, 2.4, -0.15), (-1.3, 2.4, -0.15)]},
}


# ------------------------------------------------------------------ shape helpers

def C(m, key, hexv):
    m.color(key, hexv, dots=False)


def basis(axis):
    a = Vector(axis).normalized()
    ref = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
    u = a.cross(ref).normalized()
    v = u.cross(a).normalized()   # so a ring around +Y goes +X then up (+Z)
    return a, u, v


def cyl(m, col, a, b, r, sides=14, smooth=True, round_caps=False):
    """cylinder from a to b (flat caps unless round_caps)"""
    up = (0, 0, 1) if abs(Vector(b).z - Vector(a).z) < 0.9 * (Vector(b) - Vector(a)).length else (0, -1, 0)
    m.loft('Root', col, [a, b], [(r, r), (r, r)], sides=sides, steps=1, smooth=smooth,
           cap_round=0.45 if round_caps else 0.0, up=up)


def cone(m, col, a, b, r0, r1, sides=14, smooth=True):
    up = (0, 0, 1) if abs(Vector(b).z - Vector(a).z) < 0.9 * (Vector(b) - Vector(a)).length else (0, -1, 0)
    m.loft('Root', col, [a, b], [(r0, r0), (r1, r1)], sides=sides, steps=1, smooth=smooth, cap_round=0.0, up=up)


def tube(m, col, pts, r, smooth=True, sides=10):
    m.loft('Root', col, pts, [(r, r)] * len(pts), sides=sides, steps=3, smooth=smooth)


def ring(m, col, center, axis, R, r, segs=20, arc=TAU, start=0.0, sides=8):
    _, u, v = basis(axis)
    c = Vector(center)
    n = segs if arc < TAU - 1e-3 else segs + 1
    pts = [tuple(c + (u * math.cos(start + arc * i / segs) + v * math.sin(start + arc * i / segs)) * R) for i in range(n)]
    m.loft('Root', col, pts, [(r, r)] * len(pts), sides=sides, steps=2, smooth=True)


def cog(m, col, center, axis, R, thick, teeth=10):
    a, u, v = basis(axis)
    c = Vector(center)
    cyl(m, col, tuple(c - a * thick / 2), tuple(c + a * thick / 2), R, sides=teeth * 2, smooth=False)
    for i in range(teeth):
        ang = TAU * i / teeth
        d = u * math.cos(ang) + v * math.sin(ang)
        p0 = c + d * (R - 0.02)
        cyl(m, col, tuple(p0 - a * thick / 2), tuple(p0 + a * thick / 2), R * 0.16, sides=4, smooth=False)
        m.box('Root', col, tuple(c + d * (R + 0.06)), (R * 0.28, R * 0.28, R * 0.28), bevel=0.01)


def wheel(m, center, axis, R, width, tire='tire', rim='chrome', hub='hub'):
    a, _, _ = basis(axis)
    c = Vector(center)
    cyl(m, tire, tuple(c - a * width / 2), tuple(c + a * width / 2), R, sides=18)
    cyl(m, rim, tuple(c - a * (width / 2 + 0.02)), tuple(c + a * (width / 2 + 0.02)), R * 0.62, sides=14)
    cyl(m, hub, tuple(c - a * (width / 2 + 0.05)), tuple(c + a * (width / 2 + 0.05)), R * 0.22, sides=8)
    _, u, v = basis(axis)
    for i in range(5):   # spokes
        ang = TAU * i / 5
        d = u * math.cos(ang) + v * math.sin(ang)
        for s in (-1, 1):
            m.box('Root', hub, tuple(c + a * s * (width / 2 + 0.03) + d * R * 0.38), (0.09, 0.09, 0.09), bevel=0.01)


def hazard(m, ca, cb, a, b, width, height, n=8):
    A, B = Vector(a), Vector(b)
    step = (B - A) / n
    yaw = math.degrees(math.atan2(step.y, step.x))
    for i in range(n):
        p = A + step * (i + 0.5)
        m.box('Root', ca if i % 2 == 0 else cb, tuple(p), (step.length * 1.02, width, height), rot=(0, 0, yaw), bevel=0.0)


def rounded(m, col, center, size, rot=(0, 0, 0), r=0.15, segs=3, taper=None):
    m.box('Root', col, center, size, rot=rot, bevel=r, segs=segs, smooth=True, taper=taper)


# ------------------------------------------------------------------ shared treadmill anatomy

def base_deck(m, deck, rail, recess='recess', hood=None, rail_y=(-1.9, 2.75)):
    """deck slab, belt recess between the side rails, rear roller and (optionally) a motor hood"""
    rounded(m, deck, (0, 0.3, 0.32), (3.0, 5.6, 0.36), r=0.12)
    m.box('Root', recess, (0, 0.45, 0.6), (2.25, 4.6, 0.04), bevel=0.0)
    y0, y1 = rail_y
    for s in (-1, 1):
        rounded(m, rail, (1.38 * s, (y0 + y1) / 2, 0.66), (0.42, y1 - y0, 0.28), r=0.1)
    cyl(m, 'roller', (-1.12, 2.82, 0.5), (1.12, 2.82, 0.5), 0.17, sides=12)
    if hood:
        rounded(m, hood, (0, -2.45, 0.66), (3.05, 1.2, 0.72), r=0.3, taper=dict(axis='z', end=1, scale=(0.94, 0.72)))


def grips(m, bar, rubber, y=-2.2, z=2.25, half=1.35):
    tube(m, bar, [(-half, y, z), (0, y - 0.12, z + 0.05), (half, y, z)], 0.08)
    for s in (-1, 1):
        tube(m, bar, [(half * s, y, z), (half * 1.03 * s, y + 0.55, z - 0.12), (half * 1.03 * s, y + 1.25, z - 0.22)], 0.08)
        cyl(m, rubber, (half * 1.03 * s, y + 0.6, z - 0.13), (half * 1.03 * s, y + 1.2, z - 0.21), 0.12, sides=10)


# ------------------------------------------------------------------ the five tiers

def scrap_runner(m):
    for k, v in dict(rust='#a35a2f', rust2='#6e3a1f', wood='#c09058', wood2='#8a6236', metal='#9a9ea6', tape='#c3c7cc',
                     red='#d23a2a', crt='#5b5f66', screen='#86ff8f', recess='#24262e', roller='#3b3d44', black='#25262b',
                     bulb='#fff2a8').items():
        C(m, k, v)
    # rusty frame under a pallet of planks
    rounded(m, 'rust2', (0, 0.3, 0.2), (3.0, 5.6, 0.3), r=0.06, segs=1)
    for i, x in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        m.box('Root', 'wood' if i % 2 == 0 else 'wood2', (x, 0.3, 0.42), (0.52, 5.7, 0.12), rot=(0, 0, (i - 2) * 0.6), bevel=0.03)
        for y in (-2.4, 0.3, 2.9):
            m.blob('Root', 'metal', (x, y, 0.49), (0.05, 0.05, 0.03), u=6, v=4)
    m.box('Root', 'recess', (0, 0.45, 0.52), (2.25, 4.6, 0.04), bevel=0.0)
    for s in (-1, 1):
        m.box('Root', 'wood2', (1.38 * s, 0.4, 0.66), (0.4, 4.7, 0.24), rot=(0, 0, 0.8 * s), bevel=0.04)
    cyl(m, 'roller', (-1.12, 2.82, 0.5), (1.12, 2.82, 0.5), 0.17, sides=12)
    # oil-barrel motor lying across the front, with ribs and a spout
    cyl(m, 'rust', (-1.45, -2.45, 0.75), (1.45, -2.45, 0.75), 0.62, sides=16)
    for x in (-0.8, 0.8):
        ring(m, 'rust2', (x, -2.45, 0.75), (1, 0, 0), 0.63, 0.05, segs=16)
    cyl(m, 'metal', (1.45, -2.45, 1.0), (1.6, -2.45, 1.0), 0.1, sides=8)
    # exposed cogs on the left side
    cog(m, 'metal', (-1.68, -1.0, 0.7), (1, 0, 0), 0.45, 0.12, teeth=10)
    cog(m, 'rust2', (-1.68, -0.25, 0.48), (1, 0, 0), 0.26, 0.12, teeth=8)
    # car battery on the right
    rounded(m, 'black', (1.78, -1.0, 0.62), (0.5, 0.75, 0.45), r=0.05, segs=1)
    cyl(m, 'red', (1.68, -1.2, 0.85), (1.68, -1.2, 0.95), 0.06, sides=8)
    cyl(m, 'metal', (1.88, -0.8, 0.85), (1.88, -0.8, 0.95), 0.06, sides=8)
    tube(m, 'red', [(1.68, -1.2, 0.95), (1.4, -1.6, 1.2), (1.2, -2.2, 1.2)], 0.035, sides=6)
    # pipe uprights with duct-tape wraps and bicycle handlebars
    for s in (-1, 1):
        tube(m, 'metal', [(1.3 * s, -2.0, 0.6), (1.35 * s, -2.25, 1.6), (1.2 * s, -2.35, 2.35)], 0.11)
        for z in (1.05, 1.8):
            cyl(m, 'tape', (1.33 * s, -2.17, z - 0.07), (1.34 * s, -2.21, z + 0.07), 0.14, sides=8)
    tube(m, 'metal', [(-1.5, -1.85, 2.55), (-1.1, -2.25, 2.4), (0, -2.35, 2.35), (1.1, -2.25, 2.4), (1.5, -1.85, 2.55)], 0.07)
    for s in (-1, 1):
        cyl(m, 'black', (1.5 * s, -1.85, 2.55), (1.62 * s, -1.6, 2.6), 0.1, sides=8)
    # CRT telly on a crate, bent antennas
    m.box('Root', 'wood2', (0, -2.85, 1.6), (1.6, 0.9, 1.2), bevel=0.04)
    for z in (1.25, 1.6, 1.95):
        m.box('Root', 'wood', (0, -3.31, z), (1.55, 0.04, 0.22), bevel=0.01)
    rounded(m, 'crt', (0, -2.85, 2.65), (1.55, 1.0, 1.05), rot=(0, 0, 3), r=0.18)
    m.box('Root', 'screen', (0, -3.37, 2.67), (1.1, 0.06, 0.72), rot=(0, 0, 3), bevel=0.12)
    m.spike('Root', 'metal', (0.25, -2.8, 3.15), (0.55, 0.2, 1), 1.0, 0.05, snap=False)
    m.spike('Root', 'metal', (-0.2, -2.8, 3.15), (-0.7, 0.1, 1), 0.85, 0.05, snap=False)
    # a work light clamped to the rail
    tube(m, 'black', [(1.4, 1.5, 0.8), (1.5, 1.4, 1.5), (1.2, 1.1, 1.8)], 0.04, sides=6)
    cone(m, 'red', (1.2, 1.1, 1.8), (1.05, 0.95, 1.65), 0.08, 0.2, sides=10)
    m.blob('Root', 'bulb', (1.05, 0.95, 1.63), (0.11, 0.11, 0.11), u=8, v=5)
    # tyre bumper at the back
    ring(m, 'black', (0, 3.2, 0.5), (0, 1, 0), 0.38, 0.17, segs=14)


def street_sprinter(m):
    for k, v in dict(white='#f4f5f7', red='#e8313b', black='#22252c', grey='#b4b9c2', chrome='#e0e5ec',
                     screen='#4fc3ff', led='#7af4ff', recess='#1d2026', roller='#3a3d45', bottle='#3fa9ff').items():
        C(m, k, v)
    base_deck(m, 'white', 'black', hood='white')
    for s in (-1, 1):   # red accent and LED strip along each side
        m.box('Root', 'red', (1.52 * s, 0.3, 0.32), (0.04, 5.5, 0.18), bevel=0.0)
        m.box('Root', 'led', (1.52 * s, 0.3, 0.46), (0.03, 5.3, 0.04), bevel=0.0)
        rounded(m, 'black', (1.25 * s, 2.9, 0.12), (0.4, 0.3, 0.2), r=0.05, segs=1)
        rounded(m, 'black', (1.25 * s, -2.7, 0.12), (0.4, 0.3, 0.2), r=0.05, segs=1)
    m.box('Root', 'red', (0, -3.06, 0.72), (2.4, 0.04, 0.12), bevel=0.0)
    # swooping uprights into a wide curved console
    for s in (-1, 1):
        tube(m, 'white', [(1.3 * s, -2.3, 0.9), (1.42 * s, -2.75, 1.7), (1.35 * s, -2.9, 2.55)], 0.2, sides=14)
    rounded(m, 'white', (0, -2.95, 2.95), (3.0, 0.62, 1.1), rot=(-22, 0, 0), r=0.28, segs=4)
    rounded(m, 'black', (0, -2.72, 3.05), (2.3, 0.08, 0.72), rot=(-22, 0, 0), r=0.06, segs=2)
    m.box('Root', 'screen', (0, -2.68, 3.08), (1.9, 0.04, 0.52), rot=(-22, 0, 0), bevel=0.03)
    m.box('Root', 'led', (0, -2.92, 3.52), (2.6, 0.04, 0.04), rot=(-22, 0, 0), bevel=0.0)
    for s in (-1, 1):   # speaker grills built into the console
        c = Vector((1.15 * s, -2.83, 2.7))
        cyl(m, 'grey', tuple(c), tuple(c + Vector((0, -0.12, 0.05))), 0.18, sides=14)
        ring(m, 'red', tuple(c + Vector((0, -0.12, 0.05))), (0, -1, 0.4), 0.18, 0.025, segs=16)
    grips(m, 'chrome', 'black', y=-2.25, z=2.3)
    # cup holder with a water bottle
    rounded(m, 'black', (1.65, -2.45, 2.15), (0.32, 0.32, 0.18), r=0.05, segs=1)
    cyl(m, 'bottle', (1.65, -2.45, 2.15), (1.65, -2.45, 2.75), 0.12, sides=12)
    cone(m, 'white', (1.65, -2.45, 2.75), (1.65, -2.45, 2.9), 0.12, 0.05, sides=10)


def turbo_trainer(m):
    for k, v in dict(red='#d0202a', red2='#9a141c', chrome='#e6eaf0', black='#1d1f24', flame='#ff8a1a', flame2='#ffd23a',
                     tire='#1f2024', hub='#9aa0a8', gauge='#f4f4f4', needle='#e8313b', screen='#ffe14a', recess='#1d1f24',
                     roller='#2c2e33').items():
        C(m, k, v)
    base_deck(m, 'red', 'chrome')
    # four car wheels with chrome rims at the corners
    for s in (-1, 1):
        for y in (-1.9, 2.3):
            wheel(m, (1.72 * s, y, 0.45), (1, 0, 0), 0.48, 0.32)
        # flame paint licking back along the sides
        for k, (z, l, col) in enumerate(((0.32, 2.2, 'flame'), (0.22, 1.6, 'flame2'), (0.42, 1.4, 'flame2'), (0.3, 1.0, 'flame'))):
            m.spike('Root', col, (1.51 * s, -1.4 + 0.25 * k, z), (0, 1, 0.07 * (k - 1.5)), l, 0.03, 0.22, snap=False)
    # V8 block with chrome valve covers, a supercharger and an air scoop
    rounded(m, 'black', (0, -2.45, 0.85), (1.4, 1.2, 0.8), r=0.1, segs=2)
    for s in (-1, 1):
        rounded(m, 'chrome', (0.45 * s, -2.45, 1.32), (0.42, 1.15, 0.22), rot=(0, 30 * s, 0), r=0.08, segs=2)
        for y in (-2.8, -2.45, -2.1):   # header pipes curling out of the block and back to the exhausts
            tube(m, 'chrome', [(0.72 * s, y, 0.9), (1.05 * s, y + 0.1, 0.75), (1.1 * s, y + 0.5, 0.55)], 0.06, sides=8)
        tube(m, 'chrome', [(1.1 * s, -1.6, 0.52), (1.08 * s, 0.5, 0.55), (1.06 * s, 2.7, 0.6), (1.05 * s, 3.35, 0.62)], 0.11)
        cyl(m, 'black', (1.05 * s, 3.3, 0.62), (1.05 * s, 3.47, 0.62), 0.09, sides=10)
    rounded(m, 'chrome', (0, -2.45, 1.55), (0.75, 0.9, 0.35), r=0.1, segs=2)
    for x in (-0.22, 0.0, 0.22):
        cyl(m, 'black', (x, -2.45, 1.72), (x, -2.45, 1.98), 0.07, sides=8)
    rounded(m, 'red2', (0, -2.6, 2.05), (0.6, 0.55, 0.22), rot=(-12, 0, 0), r=0.08, segs=2,
            taper=dict(axis='y', end=-1, scale=(1.0, 0.4)))
    # dashboard console with gauges, and a steering wheel for a handlebar
    for s in (-1, 1):
        tube(m, 'chrome', [(1.2 * s, -1.85, 0.7), (1.25 * s, -2.2, 1.6), (1.1 * s, -2.55, 2.4)], 0.12)
    rounded(m, 'black', (0, -2.85, 2.75), (2.6, 0.6, 0.85), rot=(-22, 0, 0), r=0.2, segs=3)
    for x in (-0.6, 0.6):
        c = Vector((x, -2.62, 2.85))
        cyl(m, 'gauge', tuple(c), tuple(c + Vector((0, -0.08, 0.03))), 0.24, sides=16)
        ring(m, 'chrome', tuple(c + Vector((0, -0.08, 0.03))), (0, -1, 0.4), 0.24, 0.03, segs=16)
        m.box('Root', 'needle', tuple(c + Vector((0.06, -0.1, 0.08))), (0.2, 0.02, 0.03), rot=(0, 35, 0), bevel=0.0)
    m.box('Root', 'screen', (0, -2.62, 2.75), (0.4, 0.05, 0.2), rot=(-22, 0, 0), bevel=0.02)
    ring(m, 'black', (0, -2.15, 2.3), (0, -1, 0.35), 0.5, 0.07, segs=20)
    for ang in (0.3, 2.84, 4.71):
        m.box('Root', 'chrome', (0.25 * math.cos(ang), -2.15, 2.3 + 0.25 * math.sin(ang)), (0.5, 0.06, 0.06),
              rot=(0, -math.degrees(ang), 0), bevel=0.01)
    # rear spoiler on two struts
    for s in (-1, 1):
        rounded(m, 'black', (0.9 * s, 3.0, 1.0), (0.1, 0.25, 0.75), r=0.03, segs=1)
    rounded(m, 'red', (0, 3.08, 1.42), (2.9, 0.75, 0.12), rot=(-10, 0, 0), r=0.05, segs=2)
    for s in (-1, 1):
        rounded(m, 'black', (1.48 * s, 3.08, 1.5), (0.06, 0.8, 0.35), r=0.02, segs=1)


def rocket_rig(m):
    for k, v in dict(white='#eef0f5', orange='#ff7a1a', dark='#3a3e48', nozzle='#565b66', inner='#ff9a3a',
                     yellow='#ffd02a', black='#202227', screen='#7affd0', button='#ff2a2a', recess='#22252e',
                     roller='#3a3e48', dish='#d9dde4').items():
        C(m, k, v)
    base_deck(m, 'white', 'dark', hood='dark')
    hazard(m, 'yellow', 'black', (-1.5, 3.05, 0.42), (1.5, 3.05, 0.42), 0.12, 0.2, n=10)
    hazard(m, 'yellow', 'black', (-1.5, -3.08, 0.5), (1.5, -3.08, 0.5), 0.12, 0.3, n=10)
    for s in (-1, 1):
        x = 2.05 * s
        # booster: body with panel bands, nose cone, bell nozzle with a hot inner lining, fins
        cyl(m, 'white', (x, -1.2, 1.05), (x, 2.6, 1.05), 0.5, sides=16)
        cone(m, 'orange', (x, -1.2, 1.05), (x, -2.2, 1.05), 0.5, 0.06, sides=16)
        for y in (-0.6, 0.6, 1.8):
            ring(m, 'orange' if y != 0.6 else 'dark', (x, y, 1.05), (0, 1, 0), 0.5, 0.045, segs=16)
        cone(m, 'nozzle', (x, 2.6, 1.05), (x, 3.55, 1.05), 0.3, 0.52, sides=16)
        cone(m, 'inner', (x, 3.0, 1.05), (x, 3.53, 1.05), 0.12, 0.44, sides=16)
        for ang in (0, 2.09, 4.19):
            d = Vector((math.cos(ang) * s, 0, math.sin(ang)))
            if d.x * s < -0.5:
                continue   # no fin into the deck
            m.box('Root', 'orange', tuple(Vector((x, 2.15, 1.05)) + d * 0.72), (0.06 if abs(d.z) > 0.5 else 0.5, 0.85,
                  0.5 if abs(d.z) > 0.5 else 0.06), bevel=0.02, taper=dict(axis='y', end=-1, scale=(1, 0.3)))
        rounded(m, 'dark', (1.65 * s, 0.7, 0.85), (0.35, 0.6, 0.3), r=0.05, segs=1)
        rounded(m, 'dark', (1.65 * s, -0.6, 0.85), (0.35, 0.6, 0.3), r=0.05, segs=1)
    # launch-tower trusses up to the console
    for s in (-1, 1):
        for dx in (-0.12, 0.12):
            tube(m, 'dark', [(1.3 * s + dx, -2.1, 0.95), (1.3 * s + dx, -2.5, 2.6)], 0.06, sides=6)
        for k in range(4):
            z0 = 1.0 + k * 0.4
            m.box('Root', 'orange', (1.3 * s, -2.15 - 0.1 * k, z0 + 0.2), (0.3, 0.05, 0.05), rot=(0, 40 * (1 if k % 2 else -1), 0), bevel=0.0)
    rounded(m, 'dark', (0, -2.9, 2.9), (2.9, 0.62, 1.1), rot=(-22, 0, 0), r=0.15, segs=2)
    m.box('Root', 'screen', (0, -2.66, 3.12), (1.2, 0.05, 0.5), rot=(-22, 0, 0), bevel=0.03)
    for x in (-1.0, 1.0):   # dials
        c = Vector((x, -2.66, 3.05))
        cyl(m, 'dish', tuple(c), tuple(c + Vector((0, -0.06, 0.02))), 0.2, sides=14)
        m.box('Root', 'button', tuple(c + Vector((0.05, -0.08, 0.05))), (0.16, 0.02, 0.03), rot=(0, 50, 0), bevel=0.0)
    # the big red launch button under a hinged cover
    c = Vector((0, -2.55, 2.68))
    cyl(m, 'yellow', tuple(c), tuple(c + Vector((0, 0.0, 0.05))), 0.2, sides=14)
    cyl(m, 'button', tuple(c + Vector((0, 0, 0.05))), tuple(c + Vector((0, 0, 0.14))), 0.13, sides=14)
    tube(m, 'orange', [(-1.4, -2.25, 2.25), (1.4, -2.25, 2.25)], 0.09)
    # radar dish on a mast
    cyl(m, 'dark', (1.3, -3.0, 3.35), (1.3, -3.0, 4.0), 0.05, sides=8)
    m.blob('Root', 'dish', (1.3, -2.95, 4.05), (0.45, 0.45, 0.12), rot=(60, 0, -20), u=14, v=6, smooth=True)
    cyl(m, 'dark', (1.3, -2.95, 4.05), (1.3, -3.2, 4.3), 0.03, sides=6)


def hyperdrive(m):
    for k, v in dict(hull='#1b1d2b', hull2='#2c3046', chrome='#4a5070', cyan='#33f6ff', magenta='#ff3adf',
                     core='#eaffff', screen='#33f6ff', recess='#0f1018', roller='#2c3046', pad='#7ffcff').items():
        C(m, k, v)
    # angular hull floating on four glowing hover pads (no feet)
    rounded(m, 'hull', (0, 0.3, 0.32), (3.1, 6.0, 0.36), r=0.1, segs=2, taper=dict(axis='z', end=-1, scale=(0.85, 0.9)))
    m.box('Root', 'recess', (0, 0.45, 0.52), (2.25, 4.6, 0.04), bevel=0.0)
    for s in (-1, 1):
        rounded(m, 'hull2', (1.38 * s, 0.4, 0.62), (0.42, 4.9, 0.26), r=0.08, segs=2)
        m.box('Root', 'cyan', (1.6 * s, 0.3, 0.42), (0.04, 5.8, 0.05), bevel=0.0)
        m.box('Root', 'magenta', (1.42 * s, 0.4, 0.77), (0.06, 4.6, 0.03), bevel=0.0)
        for y in (-2.2, 2.4):
            cone(m, 'hull2', (1.3 * s, y, 0.15), (1.3 * s, y, -0.05), 0.45, 0.32, sides=16)
            cyl(m, 'pad', (1.3 * s, y, -0.05), (1.3 * s, y, -0.1), 0.3, sides=16)
    cyl(m, 'roller', (-1.12, 2.82, 0.5), (1.12, 2.82, 0.5), 0.15, sides=12)
    # ribbed neon arches the runner sprints through
    for y, col, R in ((-0.9, 'cyan', 2.5), (0.7, 'magenta', 2.4), (2.2, 'cyan', 2.3)):
        ring(m, col, (0, y, 0.55), (0, 1, 0), R, 0.1, segs=18, arc=math.pi, start=0.0, sides=6)
        for i in range(1, 6):
            ang = math.pi * i / 6
            p = Vector((R * math.cos(ang), y, 0.55 + R * math.sin(ang)))
            cyl(m, 'hull2', tuple(p - Vector((0, 0.13, 0))), tuple(p + Vector((0, 0.13, 0))), 0.16, sides=8)
    # reactor core with two orbiting rings, on a pedestal at the back
    cone(m, 'hull2', (0, 3.35, 0.55), (0, 3.35, 0.95), 0.6, 0.35, sides=16)
    m.blob('Root', 'core', (0, 3.35, 1.55), (0.45, 0.45, 0.45), u=14, v=10, smooth=True)
    ring(m, 'cyan', (0, 3.35, 1.55), (0.3, 0.2, 1), 0.72, 0.05, segs=24)
    ring(m, 'magenta', (0, 3.35, 1.55), (-0.5, 0.6, 0.6), 0.85, 0.05, segs=24)
    for k in range(3):   # energy cables from the core forward under the rails
        s = -1 if k == 0 else 1 if k == 1 else 0
        if s:
            tube(m, 'magenta', [(0.4 * s, 3.2, 0.7), (1.0 * s, 2.8, 0.45), (1.5 * s, 1.0, 0.4), (1.5 * s, -2.0, 0.45)], 0.05, sides=6)
    # sleek pillar console with a holo screen and side holo panels
    rounded(m, 'hull', (0, -2.65, 1.35), (0.7, 0.55, 1.9), rot=(-12, 0, 0), r=0.15, segs=2,
            taper=dict(axis='z', end=1, scale=(0.7, 0.8)))
    rounded(m, 'hull2', (0, -2.85, 2.5), (2.4, 0.4, 0.75), rot=(-28, 0, 0), r=0.18, segs=3,
            taper=dict(axis='x', end=1, scale=(0.75, 0.8)))
    m.box('Root', 'screen', (0, -2.95, 3.2), (2.0, 0.03, 0.75), rot=(-15, 0, 0), bevel=0.02)
    m.box('Root', 'magenta', (0, -2.95, 3.6), (2.0, 0.035, 0.04), rot=(-15, 0, 0), bevel=0.0)
    for s in (-1, 1):
        m.box('Root', 'cyan', (1.95 * s, -2.35, 2.6), (0.04, 0.95, 0.65), rot=(0, 0, 25 * s), bevel=0.02)
        m.box('Root', 'magenta', (2.0 * s, -2.35, 2.6), (0.03, 0.75, 0.04), rot=(0, 0, 25 * s), bevel=0.0)
    tube(m, 'chrome', [(-1.35, -2.2, 2.2), (0, -2.35, 2.28), (1.35, -2.2, 2.2)], 0.08)
    for s in (-1, 1):
        tube(m, 'chrome', [(1.35 * s, -2.2, 2.2), (1.4 * s, -1.4, 1.9), (1.38 * s, -0.9, 0.8)], 0.07)


def treadmill(m, tier):
    {1: street_sprinter, 2: turbo_trainer, 3: rocket_rig, 4: scrap_runner, 5: hyperdrive}[tier](m)


m = Monster(WHAT)
m.static = True
if WHAT == 'Bat':
    bat = None
    m.color('wood', '#c98a4b'); m.color('grip', '#d63a3a'); m.color('knob', '#5a3a22'); m.color('band', '#f2efe6')
    m.loft('Root', 'wood', [(0, 0, 0.15), (0, 0, 0.6), (0, 0, 1.3), (0, 0, 2.2), (0, 0, 2.9), (0, 0, 3.25)],
           [(0.12, 0.12), (0.12, 0.12), (0.14, 0.14), (0.27, 0.27), (0.33, 0.33), (0.32, 0.32)],
           sides=8, steps=3, smooth=False, up=(0, -1, 0))
    m.loft('Root', 'knob', [(0, 0, 0.0), (0, 0, 0.16)], [(0.21, 0.21), (0.2, 0.2)], sides=8, steps=1, smooth=False, up=(0, -1, 0))
    m.loft('Root', 'grip', [(0, 0, 0.17), (0, 0, 1.15)], [(0.145, 0.145), (0.15, 0.15)], sides=8, steps=1, smooth=False, up=(0, -1, 0))
    for z in (0.4, 0.7, 0.95):
        m.loft('Root', 'band', [(0, 0, z), (0, 0, z + 0.05)], [(0.16, 0.16), (0.16, 0.16)], sides=8, steps=1, smooth=False, up=(0, -1, 0))
    m.loft('Root', 'band', [(0, 0, 2.55), (0, 0, 2.66)], [(0.315, 0.315), (0.32, 0.32)], sides=8, steps=1, smooth=False, up=(0, -1, 0))
elif WHAT == 'StormSlugger':
    # wheel prize bat: gunmetal barrel with glowing lightning inlays, gold collars, spike studs, a
    # purple-taped grip, an orb in the knob and a crackling crystal on the tip. Longer than the Bat.
    C(m, 'metal', '#3a3f58'); C(m, 'steel', '#9aa3c0'); C(m, 'glow', '#5fe0ff'); C(m, 'glow2', '#e6fbff')
    C(m, 'grip', '#6a3acc'); C(m, 'grip2', '#9a6aff'); C(m, 'gold', '#ffcf3a')
    up = (0, -1, 0)
    # knob + orb
    m.loft('Root', 'steel', [(0, 0, 0.0), (0, 0, 0.2)], [(0.25, 0.25), (0.22, 0.22)], sides=10, steps=1, smooth=False, up=up)
    m.blob('Root', 'glow', (0, 0, -0.04), (0.15, 0.15, 0.12), u=10, v=6)
    # taped grip: alternating bands
    for i in range(10):
        z = 0.2 + i * 0.105
        m.loft('Root', 'grip' if i % 2 == 0 else 'grip2', [(0, 0, z), (0, 0, z + 0.105)], [(0.15, 0.15), (0.152, 0.152)],
               sides=10, steps=1, smooth=False, up=up)
    # neck flaring into the barrel
    m.loft('Root', 'metal', [(0, 0, 1.25), (0, 0, 1.8), (0, 0, 2.4), (0, 0, 3.2), (0, 0, 3.85)],
           [(0.15, 0.15), (0.19, 0.19), (0.31, 0.31), (0.38, 0.38), (0.37, 0.37)], sides=12, steps=3, smooth=True, up=up)
    m.loft('Root', 'steel', [(0, 0, 3.85), (0, 0, 3.97)], [(0.37, 0.37), (0.3, 0.3)], sides=12, steps=1, smooth=False, up=up)
    # gold collars
    for z, r in ((1.25, 0.175), (2.4, 0.33), (3.6, 0.395)):
        m.loft('Root', 'gold', [(0, 0, z - 0.05), (0, 0, z + 0.05)], [(r, r), (r, r)], sides=12, steps=1, smooth=False, up=up)

    def barrel_r(z):
        return 0.15 + (0.31 - 0.15) * max(0, min(1, (z - 1.25) / 1.15)) if z < 2.4 else 0.31 + 0.07 * min(1, (z - 2.4) / 0.8)

    # three lightning bolts zig-zagging up the barrel, inlaid in glow
    for k in range(3):
        a0 = k * TAU / 3
        pts = []
        for j in range(8):
            z = 1.55 + j * 0.27
            a = a0 + (0.22 if j % 2 else -0.22)
            r = barrel_r(z) + 0.012
            pts.append((r * math.cos(a), r * math.sin(a), z))
        m.loft('Root', 'glow', pts, [(0.035, 0.035)] * len(pts), sides=5, steps=1, smooth=False)
    # spike studs in two rings
    for z, n, l in ((2.85, 6, 0.22), (3.35, 6, 0.26)):
        for i in range(n):
            a = i * TAU / n + (TAU / 12 if z > 3 else 0)
            r = barrel_r(z)
            m.spike('Root', 'steel', (r * math.cos(a), r * math.sin(a), z), (math.cos(a), math.sin(a), 0.15), l, 0.07, snap=False)
    # crystal on the tip with a little crown of prongs
    m.spike('Root', 'glow', (0, 0, 3.95), (0, 0, 1), 0.55, 0.17, twist=45, snap=False)
    m.spike('Root', 'glow2', (0, 0, 4.1), (0, 0, 1), 0.3, 0.08, twist=45, snap=False)
    for i in range(4):
        a = i * TAU / 4
        m.spike('Root', 'gold', (0.24 * math.cos(a), 0.24 * math.sin(a), 3.93), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), 0.3, 0.05, snap=False)
elif WHAT == 'TreadmillBelt':
    # marker for where the game's moving belt goes (packed in the same spot as a treadmill)
    m.color('belt', '#2a2c3a')
    m.box('Root', 'belt', BELT['center'], BELT['size'], bevel=0.0)
else:
    treadmill(m, int(WHAT.replace('Treadmill', '')))
m.build(OUT)
