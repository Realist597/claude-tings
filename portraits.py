"""Render transparent-background portraits for UI icons / Index cards.
blender -b --factory-startup --python portraits.py -- <export_dir> <out_dir> <Name> [<Name> ...]
Rigged monsters are posed at Idle; static props (eggs) render as-is. Output: <out_dir>/p_<Name>.png"""
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
export_dir, out_dir, names = args[0], args[1], args[2:]
os.makedirs(out_dir, exist_ok=True)

for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    with bpy.data.libraries.load(os.path.join(export_dir, name + '.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (name, name + '_Rig') or n.startswith(name + '_Glow_')]   # + glow meshes
        dst.actions = [n for n in src.actions if n == name + '_Idle']
    objs = {o.name: o for o in dst.objects if o}
    mesh = objs[name]
    for o in objs.values():
        scene.collection.objects.link(o)
    arm = objs.get(name + '_Rig')
    if arm and arm.animation_data and dst.actions:
        act = dst.actions[0]
        arm.animation_data.action = act
        if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
            arm.animation_data.action_slot = act.slots[0]
    scene.frame_set(12)
    bpy.context.view_layer.update()

    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps)
    pts = [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2

    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'TEXTURE'
    sh.show_shadows = False
    sh.show_cavity = True
    sh.cavity_type = 'WORLD'
    scene.display.shading.show_object_outline = True
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    d = Vector((-0.55, -1.0, 0.35)).normalized()
    cam.location = center + d * (hi - lo).length * 3
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = max((hi - lo).length * 0.86, 0.1)
    cam.data.clip_end = 1000
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = os.path.join(out_dir, f'p_{name}.png')
    bpy.ops.render.render(write_still=True)

    # crop to the opaque area (square, small margin) so icons fill their frames
    import numpy as np
    img = bpy.data.images.load(scene.render.filepath)
    w, h = img.size
    px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    ys, xs = np.nonzero(px[..., 3] > 0.02)
    if len(xs):
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        half = int(max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.54) + 2
        x0, y0 = int(cx - half), int(cy - half)
        side = 2 * half
        out = np.zeros((side, side, 4), np.float32)
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, w), min(y0 + side, h)
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = px[sy0:sy1, sx0:sx1]
        crop = bpy.data.images.new(f"crop_{name}", side, side, alpha=True)
        crop.pixels.foreach_set(out.ravel())
        crop.filepath_raw = scene.render.filepath
        crop.file_format = 'PNG'
        crop.save()
    print('PORTRAIT', name)
