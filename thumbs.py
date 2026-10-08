"""Roblox game icon + thumbnail renders in the chunky "simulator" style: real game monsters and
eggs, a blocky avatar, thick white outlines, a bright sky with speed lines, and big outlined text.
    blender -b --factory-startup --python thumbs.py -- <export_dir> <out_dir> <icon|steal> [--live]
export_dir holds the monster/egg .blend files (monsters/export/myth). Writes <out_dir>/<scene>.png:
icon 512x512, steal 1920x1080."""
import bpy, sys, os, math
from mathutils import Vector, Euler

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LIVE = '--live' in args
args = [a for a in args if a != '--live']
EXPORT, OUT, WHICH = args[0], args[1], args[2]
os.makedirs(OUT, exist_ok=True)
FONT_BLACK = 'C:/Windows/Fonts/ariblk.ttf'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


# ------------------------------------------------------------------ materials

def mat(name, rgb, emit=0.0, rough=0.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = emit
    return m


def flat(name, rgb, alpha=1.0):
    """unlit colour (sky, text, lines): emission only"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*rgb, 1)
    if alpha < 1:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
        elif hasattr(m, 'blend_method'):
            m.blend_method = 'BLEND'
    else:
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


OUTLINE = flat('Outline', (1, 1, 1))
OUTLINE.use_backface_culling = True


def outline(obj, thickness):
    """inverted-hull white outline: solidify outward, flipped normals, back faces only"""
    obj.data.materials.append(OUTLINE)
    mod = obj.modifiers.new('Outline', 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = len(obj.data.materials) - 1
    for p in obj.data.polygons:
        if p.material_index == len(obj.data.materials) - 1:
            p.material_index = 0


# ------------------------------------------------------------------ game models

def load(name, action=None, frame=12):
    with bpy.data.libraries.load(os.path.join(EXPORT, name + '.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in (name, name + '_Rig') or n.startswith(name + '_Glow_')]   # + glow meshes
        dst.actions = [n for n in src.actions if action and n == name + '_' + action]
    objs = {o.name: o for o in dst.objects if o}
    for o in objs.values():
        col.objects.link(o)
    arm = objs.get(name + '_Rig')
    if arm and dst.actions:
        act = dst.actions[0]
        arm.animation_data_create()
        arm.animation_data.action = act
        if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
            arm.animation_data.action_slot = act.slots[0]
        scene['pose_frame'] = frame
    root = arm or objs[name]
    root.rotation_mode = 'XYZ'
    return root, objs[name]


def place(root, loc, yaw_deg, scale):
    root.location = Vector(loc)
    root.rotation_euler = Euler((0, 0, math.radians(yaw_deg)))
    root.scale = (scale, scale, scale)


# ------------------------------------------------------------------ blocky avatar

def box(name, size, loc, color, parent=None, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.location = Vector(loc)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 3
    o.data.materials.append(color)
    if parent:
        o.parent = parent
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def pivot(name, loc, parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.location = Vector(loc)
    e.rotation_euler = Euler(tuple(math.radians(r) for r in rot))
    if parent:
        e.parent = parent
    return e


SKIN, SHIRT, JACKET, PANTS, HAIR, SHOE = (mat('skin', srgb('#f5f1ea')), mat('shirt', srgb('#2f6fe0')), mat('jacket', srgb('#1d1f27')),
                                          mat('pants', srgb('#2f6b3a')), mat('hair', srgb('#b5541f')), mat('shoe', srgb('#e9e9ee')))
EYE, MOUTH, TEETH = flat('eye', srgb('#15161c')), flat('mouth', srgb('#3a1418')), flat('teeth', (1, 1, 1))


def avatar(pose):
    """a blocky avatar (about 5.6 tall, feet at 0, facing -Y). pose: dict of joint -> (x, y, z) degrees,
    plus 'body' for the whole figure and 'drop' to lower the hips (kneeling)."""
    body = pivot('Avatar', (0, 0, 0), rot=pose.get('body', (0, 0, 0)))
    hips = pivot('Hips', (0, 0, 2.0 - pose.get('drop', 0)), body, pose.get('hips', (0, 0, 0)))
    torso = box('Torso', (2.0, 1.0, 2.0), (0, 0, 1.0), SHIRT, hips)
    box('JacketL', (0.62, 1.06, 2.02), (0.72, 0, 1.0), JACKET, hips, 0.05)
    box('JacketR', (0.62, 1.06, 2.02), (-0.72, 0, 1.0), JACKET, hips, 0.05)
    neck = pivot('Neck', (0, 0, 2.0), hips, pose.get('head', (0, 0, 0)))
    head = box('Head', (1.25, 1.2, 1.2), (0, 0, 0.65), SKIN, neck, 0.18)
    # face: eyes and a big cheeky grin on the front (-Y)
    for s in (-1, 1):
        box('Eye', (0.16, 0.05, 0.28), (0.24 * s, -0.61, 0.8), EYE, neck, 0.04)
        box('Brow', (0.3, 0.05, 0.07), (0.26 * s, -0.61, 1.02), EYE, neck, 0.02).rotation_euler = (0, math.radians(-12 * s), 0)
    box('Mouth', (0.72, 0.05, 0.26), (0, -0.61, 0.38), MOUTH, neck, 0.08)
    box('Teeth', (0.62, 0.06, 0.1), (0, -0.62, 0.45), TEETH, neck, 0.02)
    # chunky swept hair
    box('HairTop', (1.4, 1.36, 0.45), (0, 0.04, 1.32), HAIR, neck, 0.12)
    box('HairBack', (1.36, 0.4, 1.0), (0, 0.48, 0.95), HAIR, neck, 0.1)
    for k, x in enumerate((-0.45, 0.0, 0.45)):
        b = box('Fringe', (0.5, 0.4, 0.42), (x, -0.42, 1.18), HAIR, neck, 0.1)
        b.rotation_euler = (math.radians(-25), 0, math.radians((k - 1) * 12))
    parts = [torso, head]
    for side, s in (('L', 1), ('R', -1)):
        sh = pivot('Shoulder' + side, (1.5 * s, 0, 1.85), hips, pose.get('arm' + side, (0, 0, 0)))
        box('Arm' + side, (0.95, 0.95, 2.0), (0, 0, -0.85), JACKET, sh)
        box('Hand' + side, (0.9, 0.9, 0.5), (0, 0, -1.85), SKIN, sh)
        hp = pivot('Hip' + side, (0.5 * s, 0, 0), hips, pose.get('leg' + side, (0, 0, 0)))
        box('Leg' + side, (0.97, 0.97, 1.75), (0, 0, -0.88), PANTS, hp)
        box('Shoe' + side, (1.0, 1.15, 0.38), (0, -0.08, -1.82), SHOE, hp)
    for o in [x for x in bpy.data.objects if x.type == 'MESH' and x.parent and x.parent.name.split('.')[0] in
              ('Hips', 'Neck', 'ShoulderL', 'ShoulderR', 'HipL', 'HipR')]:
        if o.name.split('.')[0] in ('Torso', 'Head', 'ArmL', 'ArmR', 'LegL', 'LegR', 'HairTop', 'HairBack', 'ShoeL', 'ShoeR', 'HandL', 'HandR', 'JacketL', 'JacketR', 'Fringe'):
            outline(o, 0.09)
    return body


# ------------------------------------------------------------------ background, text, effects

def sky(top, bottom, size, depth):
    """a big gradient card behind everything"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, depth, size * 0.3))
    p = bpy.context.active_object
    p.scale = (size * 2.2, size, 1)
    p.rotation_euler = (math.radians(90), 0, 0)
    m = bpy.data.materials.new('sky')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(tc.outputs['UV'], sep.inputs[0])
    nt.links.new(sep.outputs['Y'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    p.data.materials.append(m)
    return p


def ground(color, size, z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    g = bpy.context.active_object
    g.data.materials.append(mat('ground', color, rough=0.9))
    return g


def speed_lines(center, depth, n, inner, outer, seed=3):
    import random
    rng = random.Random(seed)
    m = flat('speed', (1, 1, 1), 0.55)
    for i in range(n):
        a = i / n * math.tau + rng.uniform(-0.08, 0.08)
        r0 = inner * rng.uniform(1.0, 1.3)
        r1 = outer * rng.uniform(0.85, 1.1)
        w = rng.uniform(0.08, 0.22)
        verts = [(math.cos(a) * r0, 0, math.sin(a) * r0),
                 (math.cos(a + w / r1 * 3) * r1, 0, math.sin(a + w / r1 * 3) * r1),
                 (math.cos(a - w / r1 * 3) * r1, 0, math.sin(a - w / r1 * 3) * r1)]
        me = bpy.data.meshes.new('line')
        me.from_pydata(verts, [], [(0, 1, 2)])
        o = bpy.data.objects.new('SpeedLine', me)
        o.location = (center[0], depth, center[1])
        o.data.materials.append(m)
        col.objects.link(o)


def text(body, loc, size, fill, outline_rgb, rot=(90, 0, 0), stroke=0.09, extrude=0.06):
    def make(rgb, offset, z):
        cu = bpy.data.curves.new('txt', 'FONT')
        cu.body = body
        cu.font = bpy.data.fonts.load(FONT_BLACK, check_existing=True)
        cu.size = size
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.offset = offset
        cu.extrude = extrude
        o = bpy.data.objects.new('Text', cu)
        o.location = Vector(loc) + Vector((0, z, 0))
        o.rotation_euler = Euler(tuple(math.radians(r) for r in rot))
        o.data.materials.append(flat('t', rgb))
        col.objects.link(o)
        return o
    make(outline_rgb, stroke * size, 0.05)
    return make(fill, 0, 0)


def bang(loc, size, rot=0):
    """a red '!' with a white outline"""
    return text('!', loc, size, srgb('#e8262b'), (1, 1, 1), rot=(90, rot, 0), stroke=0.1)


def arrow(start, ctrl, end, color, width=0.35):
    """curved red arrow with a white rim (in the X/Z plane at the given Y)"""
    cu = bpy.data.curves.new('arrow', 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(1)
    a, b = sp.bezier_points
    a.co, b.co = Vector(start), Vector(end)
    a.handle_right = Vector(ctrl)
    a.handle_left = Vector(start) * 2 - Vector(ctrl)
    b.handle_left = Vector(ctrl)
    b.handle_right = Vector(end) * 2 - Vector(ctrl)
    cu.bevel_depth = width
    cu.bevel_resolution = 4
    o = bpy.data.objects.new('Arrow', cu)
    o.data.materials.append(flat('arrow', color))
    col.objects.link(o)
    rim = o.copy()
    rim.data = cu.copy()
    rim.data.bevel_depth = width * 1.35
    rim.data.materials[0] = flat('arrowRim', (1, 1, 1))
    rim.location.y += 0.3
    col.objects.link(rim)
    # head: a fat triangle at the end, pointing along the curve's end tangent
    t = (Vector(end) - Vector(ctrl)).normalized()
    n = Vector((-t.z, 0, t.x))
    tip = Vector(end) + t * width * 3.2
    for rgb, grow, dy in ((color, 1.0, 0.0), ((1, 1, 1), 1.35, 0.3)):
        verts = [tuple(tip + t * (grow - 1) * width * 2), tuple(Vector(end) + n * width * 2.6 * grow - t * width * (grow - 1)),
                 tuple(Vector(end) - n * width * 2.6 * grow - t * width * (grow - 1))]
        me = bpy.data.meshes.new('head')
        me.from_pydata([(v[0], v[1] + dy, v[2]) for v in verts], [], [(0, 1, 2)])
        h = bpy.data.objects.new('ArrowHead', me)
        h.data.materials.append(flat('ah', rgb))
        col.objects.link(h)


def lights(key_dir, strength=4.0):
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = strength
    sun.data.angle = math.radians(8)
    sun.rotation_euler = Vector(key_dir).to_track_quat('-Z', 'Y').to_euler()
    col.objects.link(sun)
    fill = bpy.data.objects.new('Fill', bpy.data.lights.new('Fill', 'SUN'))
    fill.data.energy = strength * 0.35
    fill.rotation_euler = Vector((0.6, 1, -0.3)).to_track_quat('-Z', 'Y').to_euler()
    col.objects.link(fill)
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.82, 0.95, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    scene.world = world


def camera(loc, target, lens, w, h):
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.lens = lens
    cam.data.clip_end = 2000
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    col.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = w, h


def monster_outline(mesh, thickness):
    outline(mesh, thickness)


# ------------------------------------------------------------------ scenes

def scene_icon():
    lights((0.4, 0.9, -0.7), 4.5)
    sky(srgb('#2f8fff'), srgb('#bfe9ff'), 60, 30)
    ground(srgb('#f2c46a'), 200)
    speed_lines((2, 7), 28, 34, 9, 60, seed=7)
    # Cerberus roaring behind, big
    root, mesh = load('Cerberus', 'Roar', 24)
    place(root, (3.4, 7, 0), -28, 2.3)
    monster_outline(mesh, 0.05)
    # the avatar on one knee, hoisting a giant Cerberus egg overhead
    av = avatar({
        'drop': 0.8, 'hips': (6, 0, 0), 'head': (-14, 0, 10),
        'armL': (-168, 0, -10), 'armR': (-168, 0, 10),
        'legL': (-85, 0, 0), 'legR': (25, 0, 0),
    })
    av.location = (-3.0, -3.5, 0)
    av.rotation_euler = Euler((0, 0, math.radians(14)))
    eroot, emesh = load('CerberusEgg')
    place(eroot, (-3.1, -3.9, 6.6), -10, 1.3)
    outline(emesh, 0.06)
    camera((0.2, -18.5, 5.0), (0.2, 2, 5.6), 40, 512, 512)


def scene_steal():
    lights((0.5, 0.8, -0.6), 4.5)
    sky(srgb('#1f78ff'), srgb('#9fdcff'), 80, 45)
    g = ground(srgb('#5fc23a'), 400)
    speed_lines((0, 9), 40, 46, 12, 90, seed=11)
    # the Hydra lunging in from the left
    root, mesh = load('Hydra', 'Attack', 14)
    place(root, (-9.5, 7, 0), 300, 1.9)
    monster_outline(mesh, 0.05)
    # the avatar sprinting right with a stolen egg in its arms, grinning at the camera
    av = avatar({
        'body': (0, 0, 0), 'hips': (12, 0, 0), 'head': (-10, 0, 25),
        'armL': (-72, 0, 18), 'armR': (-72, 0, -18),
        'legL': (-55, 0, 0), 'legR': (45, 0, 0),
    })
    av.location = (6.0, 0, 0.3)
    av.rotation_euler = Euler((0, 0, math.radians(-38)))
    eroot, emesh = load('InfernalWyvernEgg')
    place(eroot, (5.55, -1.55, 2.1), -30, 0.95)
    outline(emesh, 0.06)
    # !! by the hydra, the arrow + YOU!, the title
    bang((-3.1, -2, 10.4), 3.4, -14)
    bang((-1.4, -2, 10.9), 3.4, 10)
    text('YOU!', (12.6, -3, 9.6), 2.2, (1, 1, 1), srgb('#15161c'))
    arrow((11.4, -3.2, 11.4), (9.6, -3.2, 13.2), (8.6, -3.2, 10.3), srgb('#e8262b'))
    text('STEAL A MONSTER', (-4.5, -3, 15.2), 2.4, srgb('#ffd23a'), srgb('#15161c'), stroke=0.11)
    camera((0, -30, 7.5), (0, 3, 7.2), 38, 1920, 1080)


def build():
    {'icon': scene_icon, 'steal': scene_steal}[WHICH]()


# render settings: bright, punchy, soft shadows
if not LIVE:
    build()
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.render.film_transparent = False
scene.frame_set(int(scene.get('pose_frame', 1)))
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(OUT, WHICH + '.png')
if not LIVE:
    bpy.ops.render.render(write_still=True)
    print('THUMB OK', WHICH)
else:
    # live window: build once the window exists, then look through the camera, rendered
    def show():
        build()
        scene.frame_set(int(scene.get('pose_frame', 1)))
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D':
                    for sp in area.spaces:
                        if sp.type == 'VIEW_3D':
                            sp.region_3d.view_perspective = 'CAMERA'
                            sp.shading.type = 'RENDERED'
                            sp.overlay.show_overlays = False
                    with bpy.context.temp_override(window=win, area=area):
                        try:
                            bpy.ops.view3d.view_center_camera()
                        except Exception:
                            pass
        return None
    bpy.app.timers.register(show, first_interval=1.5)
