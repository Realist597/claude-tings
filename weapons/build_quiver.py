"""A quiver for the Dark Knight's bow, slung on the back and strapped round the armoured R6 body.

The strap is fitted to the armour itself: it runs from over the right shoulder, across the chest to the
left hip and back round, and its path is found by measuring the armour's outer surface all the way
round that loop (from ../armor/export/ArmorKit.fbx), so it lies on the breastplate, emblem, collar and
hip flaps instead of floating off them or cutting through. The quiver rides on the back over the cape,
mouth behind the right shoulder, with five arrows in it.

Same look as the bow: dark leather and steel with glowing purple inlays (an emissive mask), and the
same high-poly-to-game-mesh bake as the armour. One mesh, welded to the torso:
    export/QuiverKit.fbx: Armor_Quiver (+ Ref_Torso, the R6 torso it was fitted to)
    export/Armor_Quiver_Color/_Normal/_Roughness/_Metalness/_Emissive.png

    python build_quiver.py -- [--stage preview|all] [--res 1024]
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
sys.path.insert(0, HERE)
import build_armor as am
import build_bow as bw

STAGE = am.opt('--stage', 'all')
RES = int(am.opt('--res', '1024'))
am.OUT = OUT = os.path.abspath(am.opt('--out', os.path.join(HERE, 'export')))
ARMOUR = os.path.join(HERE, '..', 'armor', 'export')
am.PARTS.clear()
am.PARTS.update({'Quiver': ((0, 0, 3), None)})

# the strap's loop: over the right shoulder (the character's right is -X; it faces -Y), between the collar
# and the pauldron, down across the chest to the left hip, under the left hand
SHOULDER = Vector((-0.95, 0.0, 4.12))
HIP = Vector((1.02, 0.0, 1.84))
STRAP_W = 0.14
# the quiver: mouth behind the right shoulder, foot toward the left hip
Q_TOP = Vector((-0.6, 0.0, 4.4))
Q_BOT = Vector((0.42, 0.0, 1.98))
Q_R = (0.27, 0.21)   # half-width across the back, half-depth away from it


# ------------------------------------------------------------------ the armoured body to fit to

def load_armour():
    """the finished armour (meshes and baked textures), to fit against and to show it on"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ARMOUR, 'ArmorKit.fbx'))
    obs = [o for o in bpy.data.objects if o not in before]
    body = bpy.data.materials.new('Body')
    body.use_nodes = True
    body.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = am.lin('#a3a2a5')
    for o in obs:
        if o.type != 'MESH':
            continue
        o.data.materials.clear()
        if o.name.startswith('Armor_'):
            paths = {ch: os.path.join(ARMOUR, f'{o.name}_{ch}.png') for ch in ('Color', 'Normal', 'Roughness', 'Metalness')}
            o.data.materials.append(bw.texture_material(o.name, paths))
        else:
            o.data.materials.append(body)
    return obs


def surface(origin, direction, ignore=()):
    """the first armour (or body) surface along a ray, or None"""
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    o = Vector(origin)
    for _ in range(6):
        hit, loc, nrm, idx, ob, mat = sc.ray_cast(dg, o, Vector(direction))
        if not hit:
            return None
        if ob.name.startswith(('Armor_', 'Ref_')) and ob.name not in ignore:
            return loc
        o = loc + Vector(direction) * 1e-3
    return None


def strap_path(n=192):
    """the loop round the body in the plane through the shoulder and hip points that contains the
    front-back axis: for each direction round it, where the armour's outer surface is, then bridged
    over dips (a strap doesn't follow every crease) and smoothed, standing just proud of it"""
    C = (SHOULDER + HIP) / 2
    U = (HIP - SHOULDER).normalized()
    Y = Vector((0, 1, 0))
    r = np.zeros(n)
    dirs = []
    for k in range(n):
        ph = math.tau * k / n
        d = U * math.cos(ph) + Y * math.sin(ph)
        dirs.append(d)
        hit = surface(C + d * 6, -d)
        r[k] = (hit - C).length if hit else 0.0
    r = np.maximum.reduce([np.roll(r, s) for s in range(-5, 6)])   # bridge the creases
    r = np.convolve(np.concatenate([r[-6:], r, r[:6]]), np.ones(7) / 7, mode='same')[6:-6]
    pts = [C + d * (rk + 0.03) for d, rk in zip(dirs, r)]
    normal = U.cross(Y).normalized()   # across the strap's width
    return pts, C, normal


# ------------------------------------------------------------------ the quiver

def back_offset():
    """how far back the quiver must sit to clear the cape and armour beneath it"""
    worst = 0.0
    ax = (Q_BOT - Q_TOP)
    side = ax.cross(Vector((0, 1, 0))).normalized()
    for k in range(13):
        p = Q_TOP + ax * (k / 12)
        for s in (-1, -0.5, 0, 0.5, 1):
            q = p + side * s * Q_R[0]
            hit = surface(q + Vector((0, 6, 0)), (0, -1, 0))
            if hit:
                worst = max(worst, hit.y)
    return worst + Q_R[1] + 0.03


def quiver(pts, C, nrm, yq):
    P = 'Quiver'
    # the strap: leather, with a stitched purple line down its middle
    m = len(pts)
    fn = lambda u, v: tuple(pts[int(u * m) % m].lerp(pts[(int(u * m) + 1) % m], u * m - int(u * m))
                            + nrm * (v - 0.5) * STRAP_W)
    am.slab(P, 'Leather', fn, m, 2, 0.03, lambda p: tuple(C + (Vector(p) - C).project(nrm)), closed_u=True, bevel=0.006,
            name='strap')
    am.slab(P, 'Glow', lambda u, v: tuple(Vector(fn(u, 0.5 + (v - 0.5) * 0.18)) + (Vector(fn(u, 0.5)) - C).normalized() * 0.026),
            m, 1, 0.008, lambda p: tuple(C + (Vector(p) - C).project(nrm)), closed_u=True, bevel=0.002, name='strap_line')
    # a steel buckle with a glowing gem where the strap crosses the chest
    front = min(pts, key=lambda p: p.y + abs(p.z - 3.0) * 0.6)
    out = (front - C)
    out.x = 0
    out = out.normalized() if out.length > 1e-6 else Vector((0, -1, 0))
    w = nrm
    h = w.cross(out).normalized()
    plate = [(-0.11, -0.13), (0.11, -0.13), (0.14, 0.0), (0.11, 0.13), (-0.11, 0.13), (-0.14, 0.0)]
    bw.prism(P, 'Steel', plate, origin=tuple(front + out * 0.05), ax_a=tuple(w), ax_b=tuple(h), thick=0.04, bevel=0.01,
             name='buckle')
    am.rivet(P, 'Glow', tuple(front + out * 0.075), tuple(out), 0.06, flat=0.7)
    # the quiver itself, set back over the cape
    top, bot = Q_TOP + Vector((0, yq, 0)), Q_BOT + Vector((0, yq, 0))
    ax = bot - top
    n = 26
    axis = [top + ax * (k / (n - 1)) for k in range(n)]
    taper = lambda s: 1.0 - 0.22 * s ** 2
    radii = [(Q_R[0] * taper(k / (n - 1)), Q_R[1] * taper(k / (n - 1))) for k in range(n)]
    bw.tube(P, 'Leather', axis, radii, ring=20, bevel=0.004, name='body')
    # a flared steel rim at the mouth, steel bands down it, a pointed cap at the foot
    rim = [top + ax * (s / 40) for s in (-1.4, 0, 1.2)]
    bw.tube(P, 'Steel', rim, [(Q_R[0] * 1.14, Q_R[1] * 1.16), (Q_R[0] * 1.1, Q_R[1] * 1.12), (Q_R[0] * 1.04, Q_R[1] * 1.06)],
            ring=20, bevel=0.005, name='rim')
    for s in (0.3, 0.62, 0.9):
        t = taper(s)
        band = [top + ax * (s + d) for d in (-0.018, 0.0, 0.018)]
        bw.tube(P, 'Steel', band, [(Q_R[0] * t + 0.022, Q_R[1] * t + 0.022), (Q_R[0] * t + 0.03, Q_R[1] * t + 0.03),
                                   (Q_R[0] * t + 0.022, Q_R[1] * t + 0.022)], ring=20, bevel=0.003, name='band')
        glow = [top + ax * (s + d) for d in (-0.005, 0.0, 0.005)]
        bw.tube(P, 'Glow', glow, [(Q_R[0] * t + 0.033, Q_R[1] * t + 0.033)] * 3, ring=20, name='band_glow')
    cap = [bot + ax.normalized() * d for d in (-0.06, 0.0, 0.12, 0.24)]
    bw.tube(P, 'Steel', cap, [(Q_R[0] * 0.8, Q_R[1] * 0.8), (Q_R[0] * 0.82, Q_R[1] * 0.82), (Q_R[0] * 0.45, Q_R[1] * 0.45),
                              (0.01, 0.01)], ring=20, bevel=0.004, name='cap')
    # glowing inlay lines running down its outer face, between the bands
    side = ax.cross(Vector((0, 1, 0))).normalized()
    for off in (-0.45, 0.45):
        line = []
        for k in range(14):
            s = 0.04 + 0.86 * k / 13
            t = taper(s)
            ang = off   # radians round the quiver from straight out the back
            line.append(top + ax * s + side * math.sin(ang) * Q_R[0] * t + Vector((0, math.cos(ang) * Q_R[1] * t + 0.006, 0)))
        bw.tube(P, 'Glow', line, [(0.012, 0.009)] * len(line), ring=8, name='inlay')
    # wing blades curling off the rim, as on the bow
    for sgn in (-1, 1):
        base = top + ax * 0.06 + side * sgn * Q_R[0] * 0.75 + Vector((0, Q_R[1] * 0.75, 0))
        blade = [(0.0, 0.0), (sgn * 0.08, 0.18), (sgn * 0.1, 0.42), (sgn * 0.02, 0.62), (sgn * 0.05, 0.36), (sgn * -0.02, 0.14)]
        bw.prism(P, 'Steel', blade, origin=tuple(base), ax_a=tuple(side), ax_b=tuple(-ax.normalized()), thick=0.03,
                 name='rim_blade')
    # five arrows in it, nocks up, fletching showing above the rim
    up = -ax.normalized()
    for k, (a, b) in enumerate(((-0.12, 0.05), (0.0, -0.04), (0.12, 0.06), (-0.06, -0.09), (0.07, -0.1))):
        base = top + side * a * 1.5 + Vector((0, b * 1.2, 0))
        tip = base + up * (0.55 + 0.06 * (k % 3))
        shaft = [base + (tip - base) * (q / 4) for q in range(5)]
        bw.tube(P, 'Glow', shaft, [(0.022, 0.022)] * 5, ring=8, name='arrow')
        bw.tube(P, 'Steel', [tip - up * 0.05, tip, tip + up * 0.03], [(0.028, 0.028)] * 3, ring=8, name='nock')
        vane = [(0.02, 0.0), (0.06, 0.05), (0.1, 0.12), (0.08, 0.16), (0.11, 0.24), (0.06, 0.3), (0.02, 0.32)]
        for v in range(3):
            ang = math.radians(90 + 120 * v + 25 * k)
            dirv = side * math.cos(ang) + Vector((0, math.sin(ang), 0))
            bw.prism(P, 'PurplePolish', vane, origin=tuple(tip - up * 0.38), ax_a=tuple(dirv), ax_b=tuple(up), thick=0.01,
                     bevel=0.003, name='vane')


def pieces(pts, C, nrm, yq):
    quiver(pts, C, nrm, yq)


# ------------------------------------------------------------------ build, bake, preview, export

def bake_emissive(low, high):
    """one more map: white where the Glow material is, black elsewhere, for SurfaceAppearance's emissive mask"""
    sc = bpy.context.scene
    tnode = low.data.materials[0].node_tree.nodes.active
    img = bpy.data.images.new(f'{low.name}_Emissive', RES, RES, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    tnode.image = img
    restore = []
    for m in high.data.materials:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        old = out.inputs['Surface'].links[0].from_socket
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (1, 1, 1, 1) if m.name == 'Glow' else (0, 0, 0, 1)
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        restore.append((nt, old, out))
    for o in bpy.data.objects:
        o.select_set(False)
    high.hide_render = False
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    sc.cycles.samples = 4
    bpy.ops.object.bake(type='EMIT', margin=12, use_selected_to_active=True)
    for nt, old, out in restore:
        nt.links.new(old, out.inputs['Surface'])
    high.hide_render = True
    img.filepath_raw = os.path.join(OUT, f'{low.name}_Emissive.png')
    img.file_format = 'PNG'
    img.save()
    return img


def preview(path, samples=48):
    sc, cam, cam_d = am.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 760, 900
    cam_d.lens = 80
    for i, az in enumerate((150, -20, 205)):
        a = math.radians(az - 90)
        cam.location = (15 * math.cos(a), 15 * math.sin(a), 4.6)
        cam.rotation_euler = (Vector((0, 0, 2.7)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path.replace('.png', f'_{i}.png')
        bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def main():
    am.reset()
    os.makedirs(OUT, exist_ok=True)
    armour = load_armour()
    am.materials()
    am.mk_material('Glow', 'purple', '#9a63e8', '#8550d6', '#e2ccff', (0.22, 0.32), 0.6, groove_col='#2a1048',
                   engraved=False)
    pts, C, nrm = strap_path()
    yq = back_offset()
    print('quiver set back to y =', round(yq, 3), flush=True)
    am.HIGH[0] = False
    pieces(pts, C, nrm, yq)
    low = am.join_parts('Armor_')
    am.PIECES.clear()
    am.HIGH[0] = True
    pieces(pts, C, nrm, yq)
    high = am.join_parts('High_')
    am.HIGH[0] = False
    q, hq = low['Quiver'], high['Quiver']
    print(q.name, 'tris', sum(len(p.vertices) - 2 for p in q.data.polygons), flush=True)
    if STAGE == 'preview':
        q.hide_render = True
        for m in hq.data.materials:   # show the glow live
            if m.name == 'Glow':
                b = m.node_tree.nodes.get('Principled BSDF') or next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                m.node_tree.links.new(m.node_tree.nodes['OUT_COL'].outputs[0], b.inputs['Emission Color'])
                b.inputs['Emission Strength'].default_value = 1.6
        preview(os.path.join(OUT, 'quiver_preview.png'), samples=32)
        return
    maps = am.bake(low, high, RES)
    emit = bake_emissive(q, hq)
    am.baked_materials(low, maps)
    m = q.data.materials[0]
    t = m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = emit
    b = m.node_tree.nodes['Principled BSDF']
    mul = m.node_tree.nodes.new('ShaderNodeMix')
    mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    col = next(n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.endswith('_Color'))
    m.node_tree.links.new(col.outputs[0], mul.inputs[6])
    m.node_tree.links.new(t.outputs[0], mul.inputs[7])
    m.node_tree.links.new(mul.outputs[2], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 1.6
    preview(os.path.join(OUT, 'quiver_preview.png'))
    ref = bpy.data.objects.get('Ref_Torso')
    for o in bpy.data.objects:
        o.select_set(False)
    q.select_set(True)
    ref.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'QuiverKit.fbx'), use_selection=True, object_types={'MESH'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
    print('EXPORTED', os.path.join(OUT, 'QuiverKit.fbx'), flush=True)


main()
