"""Render a side-view film strip of one animation from a built .blend.
blender -b Monster.blend --python strip.py -- <Action suffix> <frames> <out.png>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
suffix, count, out = args[0], int(args[1]), args[2]
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
body = next(o for o in scene.objects if o.type == 'MESH')
act = next(a for a in bpy.data.actions if a.name.endswith('_' + suffix))
ad = arm.animation_data
ad.action = act
if hasattr(ad, 'action_slot') and len(act.slots):
    ad.action_slot = act.slots[0]
scene.render.resolution_x, scene.render.resolution_y = 520, 360

# ground line so planted feet are easy to judge
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
mat = bpy.data.materials.new("ground")
mat.diffuse_color = (0.35, 0.55, 0.3, 1)
ground.data.materials.append(mat)

cam = scene.camera
cam.location = Vector((16, 0.6, 1.9))
cam.rotation_euler = (Vector((0, 0.6, 1.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 55

frames = int(act.frame_range[1])
tiles = []
for i in range(count):
    scene.frame_set(int(i * frames / count))
    p = os.path.join(os.path.dirname(out), f"_strip{i}.png")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    tiles.append(np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4))
    os.remove(p)
cols = 4
rows = [np.concatenate(tiles[r * cols:(r + 1) * cols], axis=1) for r in range(len(tiles) // cols)]
sheet = np.concatenate(rows[::-1], axis=0)
h, w = sheet.shape[:2]
img = bpy.data.images.new("strip", w, h, alpha=False)
img.pixels.foreach_set(sheet.ravel())
img.filepath_raw = out
img.file_format = 'PNG'
img.save()
print("STRIP OK")
