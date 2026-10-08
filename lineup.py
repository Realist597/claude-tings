"""Render built monsters side by side at their real relative sizes.
blender -b --factory-startup --python lineup.py -- <export_dir> <out.png> <Name> [<Name> ...]
Each name is a <Name>.blend in export_dir; they're placed left to right, posed at Idle."""
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
export_dir, out, names = args[0], args[1], args[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# "|" in the name list starts a new row (rows stack upward)
x = 0.0
row_z = 0.0
row_h = 0.0
meshes = []
for name in names:
    if name == '|':
        x = 0.0
        row_z += row_h + 2.0
        row_h = 0.0
        continue
    path = os.path.join(export_dir, name + '.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (name, name + '_Rig') or n.startswith(name + '_Glow_')]   # + glow meshes
        dst.actions = [n for n in src.actions if n.startswith(name + '_')]
    objs = {o.name.split('.')[0]: o for o in dst.objects if o}
    mesh = objs[name]
    arm = objs.get(name + '_Rig', mesh)   # static props (eggs) have no rig: move the mesh itself
    for o in objs.values():   # mesh, rig and any glow meshes
        scene.collection.objects.link(o)
    idle = next((a for a in bpy.data.actions if a.name == name + '_Idle'), None)
    if idle and arm.type == 'ARMATURE' and arm.animation_data:
        arm.animation_data.action = idle
        if hasattr(arm.animation_data, 'action_slot') and len(idle.slots):
            arm.animation_data.action_slot = idle.slots[0]
    bpy.context.view_layer.update()
    lo = min((mesh.matrix_world @ Vector(c)).x for c in mesh.bound_box)
    hi = max((mesh.matrix_world @ Vector(c)).x for c in mesh.bound_box)
    width = hi - lo
    arm.location.x = x - lo + 1.0
    arm.location.z = row_z
    row_h = max(row_h, max((mesh.matrix_world @ Vector(c)).z for c in mesh.bound_box))
    x += width + 2.5
    meshes.append(mesh)

scene.frame_set(10)
bpy.context.view_layer.update()
pts = [m.matrix_world @ Vector(c) for m in meshes for c in m.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2

scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_shadows = True
rows = names.count('|') + 1
scene.render.resolution_x, scene.render.resolution_y = 1500, 750 if rows == 1 else 1500
world = bpy.data.worlds.new("W")
world.color = (0.62, 0.8, 0.95)
scene.world = world
scene.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = 'ORTHO'
d = Vector((-0.3, -1.0, 0.28)).normalized()
cam.location = center + d * (hi - lo).length * 3
cam.data.ortho_scale = max(hi.x - lo.x, (hi.z - lo.z) * 1.1) * 1.18
center.z -= (hi.z - lo.z) * 0.08
cam.data.clip_end = 500
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
scene.frame_start, scene.frame_end = 0, 71
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(out)[0] + '.blend')
print("LINEUP OK")
