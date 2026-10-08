# A chunky 3D gear icon for the Settings button, in the style of the other menu icons: thick toothed
# gear with bevels, glossy steel-blue, a black outline (inverted hull), rendered on transparent.
#   blender -b --factory-startup --python icon_gear.py -- <out.png>
import bpy, bmesh, math, sys
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "gear.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, color, metal=0.0, rough=0.35, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    return m

steel = mat("Steel", (0.18, 0.42, 0.95), metal=0.15, rough=0.32)
hub = mat("Hub", (1.0, 0.72, 0.12), metal=0.4, rough=0.3)
ink = mat("Ink", (0.01, 0.01, 0.02), rough=1)
ink.use_backface_culling = True

# ---- the gear: a cylinder with box teeth unioned on and a hole cut through, bevelled
TEETH, R_IN, R_HOLE, DEPTH = 8, 0.78, 0.36, 0.42
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=R_IN, depth=DEPTH)
gear = bpy.context.active_object
gear.name = "Gear"
for i in range(TEETH):
    a = i / TEETH * math.tau
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * (R_IN + 0.12), math.sin(a) * (R_IN + 0.12), 0))
    t = bpy.context.active_object
    t.scale = (0.42, 0.34, DEPTH)
    t.rotation_euler = (0, 0, a)
    m = gear.modifiers.new("t%d" % i, "BOOLEAN")
    m.operation = "UNION"
    m.object = t
    bpy.context.view_layer.objects.active = gear
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(t)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=R_HOLE, depth=DEPTH * 3)
h = bpy.context.active_object
m = gear.modifiers.new("hole", "BOOLEAN")
m.operation = "DIFFERENCE"
m.object = h
bpy.context.view_layer.objects.active = gear
bpy.ops.object.modifier_apply(modifier=m.name)
bpy.data.objects.remove(h)
bev = gear.modifiers.new("bev", "BEVEL")
bev.width = 0.06
bev.segments = 3
bev.limit_method = "ANGLE"
bpy.ops.object.modifier_apply(modifier="bev")
bpy.ops.object.shade_smooth()
gear.data.materials.clear()
gear.data.materials.append(steel)

# a gold hub ring in the hole
bpy.ops.mesh.primitive_torus_add(major_radius=R_HOLE + 0.02, minor_radius=0.09, major_segments=40, minor_segments=12)
ring = bpy.context.active_object
ring.location.z = DEPTH / 2
ring.data.materials.append(hub)
bpy.ops.object.shade_smooth()

# black outline: inverted hull on both
for ob in (gear, ring):
    ob.data.materials.append(ink)
    s = ob.modifiers.new("outline", "SOLIDIFY")
    s.thickness = 0.05
    s.offset = 1
    s.use_flip_normals = True
    s.material_offset = len(ob.data.materials) - 1

# tilt toward the camera like the other icons (the ring rides along)
ring.parent = gear
gear.rotation_euler = (math.radians(58), 0, math.radians(12))

# ---- camera, light, render
bpy.ops.object.camera_add(location=(0, -6, 0.3))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(88), 0, 0)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.75
scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=(3, -4, 6))
sun = bpy.context.active_object
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(40), math.radians(20), math.radians(30))
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.85, 0.9, 1, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out)
