"""Watch the Brute's head being sculpted, layer by layer, in Blender's own window.

    blender --python brute/watch_head.py

It starts from the plain R6 head, then every couple of seconds adds the next step of the sculpt (the brow, the
sockets, the nose, the muzzle, the snarl, the mouth and teeth, the eyes, then the creases and scars), in the viewport
with clay shading, while the view slowly turns. The glowing eyes go in with the eye step. Each step takes a few
seconds to work out, and the window pauses while it does.
"""
import bpy, math, os, sys
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import head as HD                               # noqa: E402

SCALE, CENTRE = 1.0, (0.0, 0.0, 0.0)
INTERVAL = 2.0


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    G = HD.grid(180, 136)
    ob = HD.build(G, SCALE, CENTRE, 'BruteHead', upto=1)
    eyes = HD.eyes(SCALE, CENTRE)
    glow = bpy.data.materials.new('Glow')
    glow.diffuse_color = (1.0, 0.05, 0.02, 1)
    eyes.data.materials.append(glow)
    eyes.hide_set(True)
    eye_step = 1 + next(i for i, (name, _) in enumerate(HD.FORMS) if name.startswith('the eyes'))
    state = {'k': 1, 'turn': 0.0}

    def views():
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D':
                    yield area

    def setup():
        for area in views():
            sp = area.spaces.active
            sp.shading.type = 'SOLID'
            sp.shading.light = 'MATCAP'
            sp.shading.color_type = 'MATERIAL'
            sp.overlay.show_floor = False
            sp.overlay.show_axis_x = sp.overlay.show_axis_y = False
            r3 = sp.region_3d
            r3.view_perspective = 'PERSP'
            r3.view_location = (0, 0, 0)
            r3.view_distance = 2.6
        return None

    def tick():
        k = state['k'] + 1
        HD.update(ob, G, SCALE, CENTRE, upto=k)
        eyes.hide_set(k < eye_step)
        print('step', k, HD.step_name(k), flush=True)
        state['k'] = k
        return INTERVAL if k < HD.STEPS else None

    def spin():
        state['turn'] += 0.01
        for area in views():
            area.spaces.active.region_3d.view_rotation = Euler((math.radians(84), 0,
                                                                 math.sin(state['turn']) * 0.7)).to_quaternion()
        return 0.03 if state['k'] < HD.STEPS else None

    bpy.app.timers.register(setup, first_interval=0.3)
    bpy.app.timers.register(tick, first_interval=1.5)
    bpy.app.timers.register(spin, first_interval=0.5)


main()
