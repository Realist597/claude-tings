"""Bundle several built monsters into one FBX so Studio needs a single Import 3D.
blender -b --factory-startup --python pack.py -- <export_dir> <Pack.fbx> <Name> [<Name> ...]
Each <Name>.blend in export_dir contributes its mesh + rig, in rest pose, laid out in a grid.
A name starting with '+' shares the previous model's spot (e.g. a treadmill and its belt marker)."""
import bpy, sys, os

args = sys.argv[sys.argv.index('--') + 1:]
export_dir, out, names = args[0], args[1], args[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

objs = []
slot = -1
for name in names:
    if name.startswith('+'):
        name = name[1:]
    else:
        slot += 1
    i = slot
    with bpy.data.libraries.load(os.path.join(export_dir, name + '.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (name, name + '_Rig') or n.startswith(name + '_Glow_')]   # + glow meshes
    loaded = {o.name.split('.')[0]: o for o in dst.objects if o}   # repeated markers load as Name.001
    mesh = loaded[name]
    arm = loaded.get(name + '_Rig')   # static props (eggs) are mesh-only
    for o in loaded.values():   # mesh, rig and any glow meshes
        scene.collection.objects.link(o)
    if arm:
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
    (arm or mesh).location = ((i % 6) * 30.0, (i // 6) * 40.0, 0)
    objs += list(loaded.values())   # mesh, rig and any glow meshes

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, object_types={'ARMATURE', 'MESH'},
    add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True,
    mesh_smooth_type='OFF', use_armature_deform_only=False, axis_forward='-Z', axis_up='Y')
print("PACK OK", len(names), "models ->", out)
