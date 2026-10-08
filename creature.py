"""Shared bits for the standalone creatures (each with its own skeleton and gait, unlike the
quadruped.py family): command-line/stage setup, the stage-scaled monster, and leg IK that also
copes with a tilted body.

    m, st, out = setup('Penguin', palette, overrides)   # stage from argv (Child|Teen|Adult)
    ik(m, pose, (upper, lower, foot), (ankle_y, ankle_z), shift=(dy, dz), pitch=deg, pivot=(y, z))

Conventions as in kit.py: Z up, faces -Y, ground at Z = 0, adult-design units times stage size S.
Pose rotations are degrees about the rest axes; a positive X rotation tips the front (-Y) DOWN.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import envelope, smooth01
from quadruped import Scaled, STAGE_DEFAULTS, lighten, add, TAU

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ARGS = [a for a in ARGS if a != '--live']


def setup(base, palette, overrides=None):
    out = ARGS[0] if ARGS else os.path.join(os.path.dirname(__file__), 'export')
    stage = ARGS[1] if len(ARGS) > 1 else 'Adult'
    st = dict(STAGE_DEFAULTS[stage])
    st.update((overrides or {}).get(stage, {}))
    st['stage'] = stage
    m = Scaled(base if stage == 'Adult' else f'{base}_{stage}', st['S'])
    for key, val in palette.items():
        hexv, dots, edges = (val, True, False) if isinstance(val, str) else (tuple(val) + (False,))[:3]
        m.color(key, lighten(hexv, st['tint']) if dots else hexv, dots=dots, edges=edges)
    return m, st, out


def rot_yz(y, z, deg):
    """rotate the point (y, z) by `deg` about the X axis (same sense as a pose X rotation)"""
    a = math.radians(deg)
    return y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)


def ik(m, pose, chain, target, shift=(0.0, 0.0), pitch=0.0, pivot=(0.0, 0.0), tilt=0.0):
    """Two-bone leg IK (kit.ik_leg) when the leg's parent is also pitched by `pitch` degrees about
    `pivot` (y, z) on top of being moved by `shift`. Positions are in stage-scaled units."""
    upper = chain[0]
    hip = next(h for n, h, t, _ in m.bones if n == upper)
    ry, rz = rot_yz(hip.y - pivot[0], hip.z - pivot[1], pitch)
    dy = pivot[0] + ry - hip.y + shift[0]
    dz = pivot[1] + rz - hip.z + shift[1]
    m.ik_leg(pose, *chain, target, (dy, dz), tilt)
    (rx, a, b), off = pose[upper]
    pose[upper] = ((rx - pitch, a, b), off)


def refs(gaits, S):
    """ground speed of each looping gait: stride (adult units) per cycle -> studs-per-unit / second"""
    return {k: g['stride'] * S / (g['frames'] / 30) for k, g in gaits.items()}
