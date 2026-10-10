"""Textures for new_bow_and_arrow.fbx: stylised black metal with glowing purple accents (more black than purple).

The meshes are kept exactly as modelled. Each gets a fresh non-overlapping UV unwrap (the originals overlap,
which a baked texture can't use), then its maps are baked from stylised materials:
    black metal  a smooth dark gradient, painted-style light edges with a faint purple tint, darker crevices
    purple       a gradient from deep violet at the grip to bright lavender at the tips, glowing
Which pieces are purple is chosen per loose part (see PURPLE below).

    python texture_new_bow.py -- [--res 1024] [--stage preview|all]
    -> export/NewBow.fbx (Bow, Arrow) and export/NewBow_<Bow|Arrow>_<Color|Normal|Roughness|Metalness|Emissive>.png
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'new_bow_and_arrow.fbx')
OUT = os.path.join(HERE, 'export')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
RES = int(opt('--res', '1024'))
STAGE = opt('--stage', 'all')


def lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


def is_purple(name, size, lo, hi):
    """which loose parts glow purple, by what they are (sizes in world units, bow ~0.67 tall)"""
    dx, dy, dz = (h - l for l, h in zip(lo, hi))
    if name == 'Bow':
        if dx < 0.004 and dz > 0.5:                    # the string
            return True
        if size in (82, 20, 18):                       # the disc faces, their rims and centre pins
            return True
        if size == 6:                                  # the thin strips set into the limbs
            return True
        return False
    if name == 'Arrow':
        return size in (78, 4)                         # the arrowhead's two halves and the fletching
    return False


# ------------------------------------------------------------------ materials

def material(name, kind, zmax, axis='Z'):
    """a stylised material whose colour / roughness / metalness / emission are exposed for baking"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(bsdf.outputs[0], out.inputs['Surface'])
    tc = N.new('ShaderNodeTexCoord')
    geo = N.new('ShaderNodeNewGeometry')

    def op(o, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath')
        n.operation = o
        n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def rng(x, a, b, c=0.0, d=1.0):
        n = N.new('ShaderNodeMapRange')
        n.clamp = True
        L.new(x, n.inputs['Value'])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = c, d
        return n.outputs[0]

    def mix(f, a, b, blend='MIX'):
        n = N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        if isinstance(f, (int, float)):
            n.inputs['Factor'].default_value = f
        else:
            L.new(f, n.inputs['Factor'])
        for sock, c in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(c, tuple):
                sock.default_value = c
            else:
                L.new(c, sock)
        return n.outputs[2]

    # edges: where a wide bevel normal turns from the true one (painted-on edge light)
    bev = N.new('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.004
    bev.samples = 16
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(bev.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Normal'], dot.inputs[1])
    edge = rng(dot.outputs['Value'], 0.995, 0.9)
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.01
    ao.samples = 16
    cav = rng(ao.outputs['AO'], 0.2, 1.0)
    # position along the piece: 0 at its middle (the grip), 1 at its ends
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Position'], sep.inputs[0])
    along = rng(op('ABSOLUTE', sep.outputs[axis]), 0.0, zmax)
    # a soft hand-painted variation, broad strokes only
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 18.0
    nz.inputs['Detail'].default_value = 2.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    soft = rng(nz.outputs['Fac'], 0.35, 0.65)
    if kind == 'black':
        base = mix(along, lin('#121117'), lin('#1f1d27'))
        base = mix(op('MULTIPLY', soft, 0.35), base, lin('#2a2734'))
        edge_col = mix(0.35, lin('#8f8aa3'), lin('#7a55c8'))            # light steel with a faint purple sheen
        col = mix(op('MULTIPLY', edge, 0.85), base, edge_col)
        col = mix(op('SUBTRACT', 1.0, cav), col, lin('#07060a'))        # darker crevices
        rough = op('SUBTRACT', rng(soft, 0, 1, 0.3, 0.38), op('MULTIPLY', edge, 0.1))
        metal, emit = 0.85, 0.0
    else:
        base = mix(rng(along, 0.0, 0.55), lin('#33087a'), lin('#7322f0'))
        base = mix(rng(along, 0.55, 1.0), base, lin('#a85cff'))
        col = mix(op('MULTIPLY', edge, 0.5), base, lin('#cfa6ff'))
        col = mix(op('MULTIPLY', op('SUBTRACT', 1.0, cav), 0.6), col, lin('#1a0636'))
        rough = rng(soft, 0, 1, 0.22, 0.3)
        metal, emit = 0.3, 0.8
    nrm = N.new('ShaderNodeBevel')   # rounds the hard edges in the normal map so they catch a clean highlight
    nrm.inputs['Radius'].default_value = 0.0015
    nrm.samples = 16
    tags = {}
    for tag, sock in (('COL', col), ('ROUGH', rough)):
        r = N.new('NodeReroute')
        r.name = 'OUT_' + tag
        L.new(sock, r.inputs[0])
        tags[tag] = r
    for tag, v in (('METAL', metal), ('EMIT', emit)):
        n = N.new('ShaderNodeValue')
        n.name = 'OUT_' + tag
        n.outputs[0].default_value = v
        tags[tag] = n
    L.new(tags['COL'].outputs[0], bsdf.inputs['Base Color'])
    L.new(tags['ROUGH'].outputs[0], bsdf.inputs['Roughness'])
    L.new(tags['METAL'].outputs[0], bsdf.inputs['Metallic'])
    L.new(nrm.outputs['Normal'], bsdf.inputs['Normal'])
    if emit:
        L.new(tags['COL'].outputs[0], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


# ------------------------------------------------------------------ prepare the meshes

def loose_parts(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            w = stack.pop()
            comp.append(w.index)
            for e in w.link_edges:
                u = e.other_vert(w)
                if u.index not in seen:
                    seen.add(u.index)
                    stack.append(u)
        parts.append(set(comp))
    bm.free()
    return parts


def prepare(ob, name, zmax, axis='Z'):
    me = ob.data
    black, purple = material(f'{name}_Black', 'black', zmax, axis), material(f'{name}_Purple', 'purple', zmax, axis)
    me.materials.clear()
    me.materials.append(black)
    me.materials.append(purple)
    vert_part = {}
    for k, part in enumerate(loose_parts(me)):
        cs = [ob.matrix_world @ me.vertices[i].co for i in part]
        lo = [min(c[a] for c in cs) for a in range(3)]
        hi = [max(c[a] for c in cs) for a in range(3)]
        flag = is_purple(name, len(part), lo, hi)
        for i in part:
            vert_part[i] = flag
    for p in me.polygons:
        p.material_index = 1 if vert_part[p.vertices[0]] else 0
        p.use_smooth = True
    # auto smooth: smooth surfaces, hard edges stay sharp
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(40):
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    # a fresh unwrap with no overlaps, as the only UV map (Roblox reads the first one)
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    me.uv_layers.new(name='UVMap')
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, area_weight=0.0, scale_to_bounds=False)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, scale=True, shape_method='CONCAVE', margin_method='FRACTION', margin=0.006)
        bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------------------------------------------ bake, preview, export

def bake(ob, name):
    sc = bpy.context.scene
    sc.render.bake.use_selected_to_active = False
    sc.render.bake.margin = 12
    maps = {}
    for o in bpy.data.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for ch, nonc in (('Color', False), ('Normal', True), ('Roughness', True), ('Metalness', True), ('Emissive', True)):
        img = bpy.data.images.new(f'NewBow_{name}_{ch}', RES, RES, alpha=False)
        img.colorspace_settings.name = 'Non-Color' if nonc else 'sRGB'
        restore = []
        for m in ob.data.materials:
            nt = m.node_tree
            t = nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage')
            t.name = 'BAKE_TARGET'
            t.image = img
            nt.nodes.active = t
            if ch != 'Normal':
                out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
                old = out.inputs['Surface'].links[0].from_socket
                em = nt.nodes.get('BAKE_EMIT') or nt.nodes.new('ShaderNodeEmission')
                em.name = 'BAKE_EMIT'
                src = nt.nodes['OUT_' + {'Color': 'COL', 'Roughness': 'ROUGH', 'Metalness': 'METAL', 'Emissive': 'EMIT'}[ch]]
                nt.links.new(src.outputs[0], em.inputs['Color'])
                nt.links.new(em.outputs[0], out.inputs['Surface'])
                restore.append((nt, old, out))
        if ch == 'Normal':
            sc.cycles.samples = 32
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=12)
        else:
            sc.cycles.samples = 32 if ch == 'Color' else 4
            bpy.ops.object.bake(type='EMIT', margin=12)
        for nt, old, out in restore:
            nt.links.new(old, out.inputs['Surface'])
        img.filepath_raw = os.path.join(OUT, f'NewBow_{name}_{ch}.png')
        img.file_format = 'PNG'
        img.save()
        maps[ch] = img
        print('BAKED', img.name, flush=True)
    # swap onto one material driven by the maps (what Roblox will show)
    m = bpy.data.materials.new(f'NewBow_{name}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = {}
    for ch, img in maps.items():
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        t[ch] = n
    nt.links.new(t['Color'].outputs[0], b.inputs['Base Color'])
    nt.links.new(t['Roughness'].outputs[0], b.inputs['Roughness'])
    nt.links.new(t['Metalness'].outputs[0], b.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(t['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], b.inputs['Normal'])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(t['Color'].outputs[0], mul.inputs[6])
    nt.links.new(t['Emissive'].outputs[0], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 1.0
    for p in ob.data.polygons:
        p.material_index = 0
    ob.data.materials.clear()
    ob.data.materials.append(m)


def preview(path, objs, samples=48):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = lin('#3a3a40')
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    lo = Vector((min((o.matrix_world @ Vector(c))[a] for o in objs for c in o.bound_box) for a in range(3)))
    hi = Vector((max((o.matrix_world @ Vector(c))[a] for o in objs for c in o.bound_box) for a in range(3)))
    ctr, size = (lo + hi) / 2, (hi - lo).length
    for nm_, loc, e in (('key', (-1.2, -2.0, 1.6), 300), ('rim', (1.4, 1.6, 1.0), 260), ('fill', (2.0, -1.4, -0.4), 90)):
        ld = bpy.data.lights.new(nm_, 'AREA')
        ld.energy, ld.size = e * size ** 2, size
        lob = bpy.data.objects.new(nm_, ld)
        sc.collection.objects.link(lob)
        lob.location = ctr + Vector(loc) * size
        lob.rotation_euler = (ctr - lob.location).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('cam')
    cd.lens = 70
    cam = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for i, d in enumerate(((0.0, -1.0, 0.05), (0.75, -0.65, 0.2))):
        cam.location = ctr + Vector(d).normalized() * size * 1.9
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path.replace('.png', f'_{i}.png')
        bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    for o in [o for o in bpy.data.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    bow, arrow = bpy.data.objects['bow'], bpy.data.objects['arrow']
    zmax = max(abs((bow.matrix_world @ v.co).z) for v in bow.data.vertices)
    prepare(bow, 'Bow', zmax)
    xmax = max(abs((arrow.matrix_world @ v.co).x) for v in arrow.data.vertices)
    prepare(arrow, 'Arrow', xmax, 'X')
    if STAGE == 'preview':
        preview(os.path.join(OUT, 'preview.png'), [bow, arrow], samples=32)
        return
    bake(bow, 'Bow')
    bake(arrow, 'Arrow')
    preview(os.path.join(OUT, 'preview.png'), [bow, arrow])
    for o in bpy.data.objects:
        o.select_set(o in (bow, arrow))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'NewBow.fbx'), use_selection=True, object_types={'MESH'},
                             mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
    print('EXPORTED', os.path.join(OUT, 'NewBow.fbx'), flush=True)


main()
