"""Open a built monster in the Blender UI: textured viewport, framed, Idle playing."""
import bpy


def setup():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'MATERIAL'
                space.overlay.show_bones = True
                region = next(r for r in area.regions if r.type == 'WINDOW')
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.view3d.view_all(center=False)
    scene = bpy.context.scene
    act = None
    for arm in (o for o in scene.objects if o.type == 'ARMATURE'):
        base = arm.name.split('.')[0].removesuffix('_Rig')
        act = bpy.data.actions.get(base + '_Walk') or act
        if act and arm.animation_data:
            arm.animation_data.action = act
            if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
                arm.animation_data.action_slot = act.slots[0]
    scene.frame_start = 0
    scene.frame_end = int(act.frame_range[1]) - 1 if act else 71
    if not bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()
    return None


bpy.app.timers.register(setup, first_interval=1.0)
