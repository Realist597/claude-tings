"""High-res transparent "hero" renders of monsters and eggs for thumbnails / marketing.
    blender -b --factory-startup --python hero.py -- <export_dir> <out_dir> <Name> [<Name> ...]
Monsters are posed at Idle (eggs as-is), lit with a key + rim light in Eevee, 2048px, transparent
background, cropped to the subject. Output: <out_dir>/hero_<Name>.png"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
export_dir, out_dir, names = args[0], args[1], args[2:]
os.makedirs(out_dir, exist_ok=True)

for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    with bpy.data.libraries.load(os.path.join(export_dir, name + '.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (name, name + '_Rig')]
        dst.actions = [n for n in src.actions if n == name + '_Idle']
    objs = {o.name: o for o in dst.objects if o}
    mesh = objs[name]
    for o in objs.values():
        scene.collection.objects.link(o)
    arm = objs.get(name + '_Rig')
    if arm and dst.actions:
        act = dst.actions[0]
        arm.animation_data_create()
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
    size = (hi - lo).length

    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.view_settings.view_transform = 'Standard'
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 2048

    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.85, 0.95, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    scene.world = world
    for key, energy, d in (('Key', 4.0, (0.5, 0.8, -0.7)), ('Rim', 3.0, (-0.6, -0.9, -0.2)), ('Fill', 1.2, (-0.8, 0.6, -0.4))):
        l = bpy.data.objects.new(key, bpy.data.lights.new(key, 'SUN'))
        l.data.energy = energy
        l.data.angle = math.radians(6)
        l.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(l)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 50
    d = Vector((-0.5, -1.0, 0.22)).normalized()
    cam.location = center + d * size * 2.4
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_end = 1000
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    path = os.path.join(out_dir, f'hero_{name}.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

    # crop to the subject with a small margin
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    ys, xs = np.nonzero(px[..., 3] > 0.02)
    if len(xs):
        m = 24
        x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, w - 1)
        y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, h - 1)
        out = px[y0:y1 + 1, x0:x1 + 1]
        crop = bpy.data.images.new(f"crop_{name}", out.shape[1], out.shape[0], alpha=True)
        crop.pixels.foreach_set(out.ravel())
        crop.filepath_raw = path
        crop.file_format = 'PNG'
        crop.save()
    print('HERO', name)
