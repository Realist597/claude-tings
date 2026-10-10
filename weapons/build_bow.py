"""The Dark Knight's bow, traced from bow_reference.jpg, and an arrow for it.

The bow is not modelled by hand. Its lower half is traced out of the reference painting (see
bow_trace.py) as a precise outline and mirrored over the grip, so both limbs match; that outline is
triangulated cleanly and given a blade-like depth -- a ridge down the middle of every limb, blade and
feather, tapering to a thin edge -- and auto smoothed, so its faces are smooth but every ridge and
edge stays sharp. The painting is
its colour map (the upper half's UVs mirror onto the lower half's pixels, doubling the detail), with the
purple inlays recoloured to a gradient and an emissive mask so they glow, plus roughness, metalness and
a light normal map. The string is its own mesh.

The arrow is modelled (in the painting it's wrapped in flames): barbed broadhead, banded shaft,
jagged fletching, in stylised purple, baked to the same maps.

    python build_bow.py -- [--stage preview|all] [--out DIR]
    -> export/BowKit.fbx: Weapon_Bow  Weapon_BowString  Weapon_Arrow, plus their
       _Color / _Normal / _Roughness / _Metalness (/ _Emissive).png

The bow stands in the XZ plane, about 5 studs tall, with the grip at the origin and the string vertical
on its +X side; the arrow points up +Z with its nock at the origin.
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bow_trace as bt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as am

STAGE = am.opt('--stage', 'all')
RES = int(am.opt('--res', '1024'))
am.OUT = OUT = os.path.abspath(am.opt('--out', os.path.join(HERE, 'export')))
am.PARTS.clear()
am.PARTS.update({'Arrow': ((3, 0, 0), None)})
ARROW_X = 3.0   # where the arrow stands beside the bow in the previews (moved back to the origin on export)

STRING_STUDS = 4.0                   # how long the string is in Roblox: sets the bow's size
SHARP_ANGLE = 30                     # auto smooth: edges bending more than this stay sharp
HALF_THICK = 0.032                   # the bow's faces sit this far either side of its centre plane (studs)
CHAMFER = 0.016                      # width of the bevel round its edges (studs)
EMISSIVE_STRENGTH = 1.6              # for the previews; set SurfaceAppearance.EmissiveStrength to taste in Studio


# ------------------------------------------------------------------ shapes

def spline(ctrl, n):
    """n points along a Catmull-Rom curve through the control points (x, z)"""
    P = [Vector((x, 0, z)) for x, z in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    segs = len(P) - 3
    for k in range(n):
        t = k / (n - 1) * segs
        i = min(int(t), segs - 1)
        f = t - i
        p0, p1, p2, p3 = P[i:i + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out


def frames(pts):
    """tangent, side (always +Y: the bow is flat in XZ) and in-plane normal at each point"""
    out = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        s = Vector((0, 1, 0))
        n = t.cross(s).normalized()
        out.append((t, s, n))
    return out


def new_bm():
    bm = bmesh.new()
    return bm, bm.loops.layers.uv.new('UVMap'), bm.loops.layers.uv.new('Detail')


def face(bm, uvl, dtl, vs, uvs):
    try:
        f = bm.faces.new(vs)
    except ValueError:
        return
    for loop, uv in zip(f.loops, uvs):
        loop[uvl].uv = uv
        loop[dtl].uv = uv


def tube(part, mat, pts, radii, ring=12, offset=None, bevel=0, name='tube'):
    """a swept solid along pts: radii[i] = (half-width in Y, half-depth in the bow's plane);
    offset(i) shifts the section along the in-plane normal (for inlays riding on a limb's edge)"""
    fr = frames(pts)
    bm, uvl, dtl = new_bm()
    rings, length = [], [0.0]
    for i, p in enumerate(pts):
        if i:
            length.append(length[-1] + (p - pts[i - 1]).length)
        t, s, n = fr[i]
        c = p + n * (offset(i) if offset else 0.0)
        rw, rd = radii[i]
        rings.append([bm.verts.new(c + s * rw * math.cos(a) + n * rd * math.sin(a))
                      for a in (math.tau * k / ring for k in range(ring))])
    per = lambda i: math.pi * (radii[i][0] + radii[i][1])
    for i in range(len(pts) - 1):
        for k in range(ring):
            k2 = (k + 1) % ring
            face(bm, uvl, dtl, (rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]),
                 ((length[i], per(i) * k / ring), (length[i + 1], per(i + 1) * k / ring),
                  (length[i + 1], per(i + 1) * (k + 1) / ring), (length[i], per(i) * (k + 1) / ring)))
    for i, rev in ((0, True), (len(pts) - 1, False)):   # end caps
        vs = rings[i][::-1] if rev else rings[i]
        rw, rd = radii[i]
        face(bm, uvl, dtl, vs, [(0.5 * rw * math.cos(math.tau * k / ring), 0.5 * rd * math.sin(math.tau * k / ring))
                                for k in (range(ring)[::-1] if rev else range(ring))])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return am.finish(part, mat, bm, bevel, name)


def prism(part, mat, outline, origin=(0, 0, 0), ax_a=(1, 0, 0), ax_b=(0, 0, 1), thick=0.03, bevel=0.008, name='blade'):
    """a flat blade: the 2D outline (a, b) laid out on axes ax_a, ax_b from origin, thickness along their normal"""
    O, A, B = Vector(origin), Vector(ax_a), Vector(ax_b)
    Nrm = A.cross(B).normalized()
    bm, uvl, dtl = new_bm()
    pt = lambda a, b, h: O + A * a + B * b + Nrm * h
    lo = [bm.verts.new(pt(a, b, -thick / 2)) for a, b in outline]
    hi = [bm.verts.new(pt(a, b, thick / 2)) for a, b in outline]
    face(bm, uvl, dtl, hi, list(outline))
    face(bm, uvl, dtl, lo[::-1], [(a + 3, b) for a, b in outline[::-1]])
    run = 0.0
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        d = (Vector(outline[j]) - Vector(outline[i])).length
        face(bm, uvl, dtl, (lo[i], lo[j], hi[j], hi[i]), ((run, -thick), (run + d, -thick), (run + d, 0), (run, 0)))
        run += d
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return am.finish(part, mat, bm, bevel, name)


# ------------------------------------------------------------------ the arrow

def arrow():
    X = ARROW_X
    shaft = [Vector((X, 0, z)) for z in (0.0, 0.8, 1.6, 2.4, 2.62)]
    tube('Arrow', 'Glow', shaft, [(0.032, 0.032)] * 5, ring=12, name='shaft')
    for z0, z1 in ((0.04, 0.12), (0.72, 0.78), (2.48, 2.62)):   # steel bands: nock, behind the fletching, ferrule
        band = [Vector((X, 0, z)) for z in (z0, (z0 + z1) / 2, z1)]
        tube('Arrow', 'Steel', band, [(0.04, 0.04), (0.045, 0.045), (0.04, 0.04)], ring=12, bevel=0.004, name='band')
    tube('Arrow', 'Steel', [Vector((X, 0, z)) for z in (-0.06, -0.03, 0.0)], [(0.036, 0.036)] * 3, ring=12, name='nock')
    # barbed broadhead: two crossed blades, each with a pair of barbs
    head = [(0.0, 3.08), (0.15, 2.8), (0.07, 2.84), (0.14, 2.66), (0.035, 2.7), (0.035, 2.58),
            (-0.035, 2.58), (-0.035, 2.7), (-0.14, 2.66), (-0.07, 2.84), (-0.15, 2.8)]
    for ax in ((1, 0, 0), (0, 1, 0)):
        prism('Arrow', 'PurplePolish', head, origin=(X, 0, 0), ax_a=ax, ax_b=(0, 0, 1), thick=0.028, bevel=0.006,
              name='head')
    # three jagged feather vanes
    vane = [(0.03, 0.66), (0.06, 0.6), (0.12, 0.5), (0.1, 0.45), (0.15, 0.36), (0.13, 0.31), (0.17, 0.2),
            (0.13, 0.17), (0.12, 0.13), (0.03, 0.15)]
    for k in range(3):
        a = math.radians(90 + 120 * k)
        prism('Arrow', 'PurplePolish', vane, origin=(X, 0, 0), ax_a=(math.cos(a), math.sin(a), 0), ax_b=(0, 0, 1),
              thick=0.012, bevel=0.003, name='vane')



# ------------------------------------------------------------------ the traced bow

def bow_textures(sym):
    """the maps, from the lower half of the symmetric painting only (the upper half's UVs mirror onto it,
    so the texture's detail is twice what it would be): colour from the painting with its purple
    inlays recoloured to a gradient, an emissive mask for them, a light normal map, roughness and metalness"""
    g = int(round(sym['grip_v']))
    m = sym['mask'][g:] > 0.5
    col = sym['col'][g:]
    H, W = m.shape
    S = max(H, W)
    _, (iy, ix) = ndi.distance_transform_edt(~m, return_indices=True)
    col = col[iy, ix] / 255.0                     # fill outside the bow from its nearest pixel: no grey fringe
    L = col.mean(2)
    sat_ = col.max(2) - col.min(2)
    purple_hard = (sat_ > 0.12) & (col[..., 2] > col[..., 1] + 0.05)
    w = np.clip((sat_ - 0.07) / 0.1, 0, 1) * np.clip((col[..., 2] - col[..., 1] - 0.02) / 0.07, 0, 1)
    w = ndi.gaussian_filter(w, 0.7) * m
    # gradient: deep violet at the grip, vivid purple, bright lavender at the tip
    gpos = np.clip(np.arange(H)[:, None] / (sym['v_bot'] - sym['grip_v']), 0, 1) * np.ones((1, W))
    stops = np.array([[0.22, 0.04, 0.58], [0.52, 0.14, 1.0], [0.82, 0.38, 1.0]])
    ramp = np.where((gpos < 0.5)[..., None], stops[0] + (stops[1] - stops[0]) * (gpos / 0.5)[..., None],
                    stops[1] + (stops[2] - stops[1]) * ((gpos - 0.5) / 0.5)[..., None])
    core = np.clip(ndi.distance_transform_edt(w > 0.5) / 4.0, 0, 1)
    tinted = np.clip(ramp * (0.5 + 0.5 * L)[..., None] + core[..., None] * 0.08, 0, 1)
    col = col * (1 - w[..., None]) + tinted * w[..., None]
    emissive = w * (0.5 + 0.5 * core)
    # a light normal map: just the painting's finest lines, so painted bevels catch a little light
    h = ndi.gaussian_filter(L, 1.0) - ndi.gaussian_filter(L, 4.0)
    gy, gx = np.gradient(h)
    nrm = np.dstack([-gx * 0.5, gy * 0.5, np.ones_like(h)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    rough = np.clip(0.46 - 0.22 * L, 0.18, 0.6)
    rough[purple_hard] = 0.3
    metal = np.where(purple_hard, 0.2, 0.4)
    pad = lambda a, fill: np.pad(a, ((0, S - H), (0, S - W)) + ((0, 0),) * (a.ndim - 2), constant_values=fill)
    maps = {'Color': col, 'Normal': nrm * 0.5 + 0.5, 'Roughness': rough, 'Metalness': metal, 'Emissive': emissive}
    fills = {'Color': 0.0, 'Normal': 0.5, 'Roughness': 0.5, 'Metalness': 0.4, 'Emissive': 0.0}
    out = {}
    for ch, a in maps.items():
        a = np.clip(pad(a, fills[ch]), 0, 1)
        if ch == 'Normal':
            a[H:, :, 2] = 1.0
            a[:, W:, 2] = 1.0
        if a.ndim == 2:
            a = np.dstack([a] * 3)
        path = os.path.join(OUT, f'Weapon_Bow_{ch}.png')
        Image.fromarray((a * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(path)
        out[ch] = path
    return out, g, S


def bow_mesh(sym, g, S):
    """the symmetric silhouette as a hard-surface solid: its precise outline filled with as few triangles
    as possible, perfectly flat front and back faces at one thickness, and a crisp chamfer round every
    edge; auto smoothed, so the faces stay flat and the chamfers catch sharp highlights"""
    polys, soft = bt.outline(sym['mask'])
    V, T, on_edge, segs = bt.triangulate(polys, soft)
    s = STRING_STUDS / (sym['v_bot'] - sym['v_top'])
    gu, gv = sym['grip_u'], sym['grip_v']
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    front, back, uv = [], [], []
    for x, y in V:
        X, Z = (x - gu) * s, (gv - y) * s
        front.append(bm.verts.new((X, -HALF_THICK, Z)))
        back.append(bm.verts.new((X, HALF_THICK, Z)))
        ym = y if y >= g else 2 * gv - y           # the upper half reads the lower half's pixels, mirrored
        uv.append((x / S, 1 - (ym - g) / S))
    def face(vs, ids):
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for loop, i in zip(f.loops, ids):
            loop[uvl].uv = uv[i]
    for a, b, c in T:
        face((front[a], front[b], front[c]), (a, b, c))
        face((back[c], back[b], back[a]), (c, b, a))
    for a, b in segs:
        face((front[a], front[b], back[b], back[a]), (a, b, b, a))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Weapon_Bow')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('Weapon_Bow', me)
    bpy.context.scene.collection.objects.link(ob)
    # the chamfer round the outline (only where the faces meet the rim at a hard angle)
    md = ob.modifiers.new('chamfer', 'BEVEL')
    md.width = CHAMFER
    md.segments = 1
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(60)
    md.use_clamp_overlap = True
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = me2
    am.smooth(ob.data, SHARP_ANGLE)   # flat faces stay flat, chamfers stay crisp
    to_plane = lambda xs, ys: [((x - gu) * s, (gv - y) * s) for x, y in zip(xs, ys)]
    return ob, to_plane


def texture_material(name, paths):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    t = {}
    for ch, p in paths.items():
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(p)
        if ch != 'Color':
            n.image.colorspace_settings.name = 'Non-Color'
        t[ch] = n
    nt.links.new(t['Color'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(t['Roughness'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(t['Metalness'].outputs[0], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(t['Normal'].outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    if 'Emissive' in t:   # glow: the colour map, wherever the emissive mask says (as Roblox does it)
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        nt.links.new(t['Color'].outputs[0], mul.inputs[6])
        nt.links.new(t['Emissive'].outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = EMISSIVE_STRENGTH
    return m


def bow_string(sym, to_plane):
    """a thin cord between the string's ends, in the painted string's colour"""
    u = sym['u0']
    (X0, Z0), (X1, Z1) = to_plane([u, u], [sym['v_top'], sym['v_bot']])
    pts = [Vector((X0 + (X1 - X0) * k / 10, 0, Z0 + (Z1 - Z0) * k / 10)) for k in range(11)]
    ob = tube('BowString', 'Glow', pts, [(0.014, 0.014)] * 11, ring=8, name='Weapon_BowString')
    am.PIECES.remove(('BowString', ob))
    ob.name = 'Weapon_BowString'
    colour = np.array([0.62, 0.5, 0.86])
    flat = {'Color': np.dstack([np.full((64, 64), c) for c in colour]), 'Normal': np.dstack([np.full((64, 64), v) for v in (0.5, 0.5, 1.0)]),
            'Roughness': np.full((64, 64, 3), 0.35), 'Metalness': np.full((64, 64, 3), 0.3),
            'Emissive': np.full((64, 64, 3), 0.8)}
    paths = {}
    for ch, a in flat.items():
        p = os.path.join(OUT, f'Weapon_BowString_{ch}.png')
        Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(p)
        paths[ch] = p
    return ob, paths


# ------------------------------------------------------------------ build, preview, export

def build_bow():
    img, lum, sat, bg = bt.load_reference()
    sym = bt.symmetric(bt.upright(img, bt.bow_mask(img, lum, sat, bg)))
    paths, g, S = bow_textures(sym)
    bow, to_plane = bow_mesh(sym, g, S)
    bow.data.materials.append(texture_material('Weapon_Bow', paths))
    string, spaths = bow_string(sym, to_plane)
    string.data.materials.clear()
    string.data.materials.append(texture_material('Weapon_BowString', spaths))
    return bow, string


def build_arrow():
    am.HIGH[0] = False
    arrow()
    low = am.join_parts('Weapon_')
    am.PIECES.clear()
    am.HIGH[0] = True
    arrow()
    high = am.join_parts('High_')
    am.HIGH[0] = False
    return low, high


def preview(path, samples=48):
    sc, cam, cam_d = am.studio()
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = 1000, 1100
    cam_d.lens = 50
    for i, (loc, tgt) in enumerate((((1.0, -12.0, 0.0), (1.0, 0, 0.0)), ((5.5, -8.5, 2.0), (0.6, 0, 0.0)))):
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path.replace('.png', f'_{i}.png') if i else path
        bpy.ops.render.render(write_still=True)
    print('PREVIEW', path, flush=True)


def export(objs):
    for o in bpy.data.objects:
        o.select_set(False)
    for ob in objs:
        ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'BowKit.fbx'), use_selection=True, object_types={'MESH'},
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_tspace=True,
                             path_mode='STRIP')
    print('EXPORTED', os.path.join(OUT, 'BowKit.fbx'), flush=True)


def main():
    am.reset()
    os.makedirs(OUT, exist_ok=True)
    am.materials()
    am.mk_material('Glow', 'purple', '#9a63e8', '#8550d6', '#e2ccff', (0.22, 0.32), 0.6, groove_col='#2a1048',
                   engraved=False)
    bow, string = build_bow()
    low, high = build_arrow()
    arrow_ob = low['Arrow']
    for ob in (bow, string, arrow_ob, high['Arrow']):
        print(ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), flush=True)
    if STAGE == 'preview':
        arrow_ob.hide_render = True
        preview(os.path.join(OUT, 'preview.png'), samples=32)
        return
    maps = am.bake(low, high, RES)
    am.baked_materials(low, maps)
    preview(os.path.join(OUT, 'preview.png'))
    arrow_ob.data.transform(Matrix.Translation((-ARROW_X, 0, 0)))   # back to the origin
    export([bow, string, arrow_ob])


if __name__ == '__main__':   # (importable, e.g. by the quiver script)
    main()
