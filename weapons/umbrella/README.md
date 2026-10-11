# Bladed umbrella (Gachiakuta), rigged

The umbrella from Gachiakuta, modelled from the anime stills, rigged to open and close.

- **Canopy:** eight off-white cloth panels, with two bands of maroon lettering across each one and faint seams fanning
  out from the hub.
- **Fins:** one on every rib.
  - Each is a thin black fin standing straight up off its rib.
  - Its top edge runs in one straight line to a point well past the canopy's edge.
  - Just past the edge it drops below the cloth, then a long diagonal sweeps back up to the point.
  - All its edges are bevelled to a knife edge, with a yellow band along each side.
- **Top:** a forged leaf-shaped spike with a yellow slot set through it, bound with red cord at its foot.
- **Shaft and handle:** a dark grey shaft, a runner and eight stretchers underneath, and a crook handle wrapped in cream
  tape, with a capped end.

The fins and the spike are built with diamond and bevelled cross-sections and hard edges, so every facet catches the
light on its own. Everything else is a lean, clean quad grid:

- Rows go only where the shape bends: in the handle's crook, and at the fins' corners.
- No piece has hidden inner walls.
- The canopy is 3 × 6 quads per panel, starting under the hub so nothing pinches at the centre.

That's about 2,200 triangles for the frame and 290 for the canopy.

## What's in `export/`

| File | What it is |
|---|---|
| `Umbrella.fbx` | Two meshes skinned to one armature, `UmbrellaRig`, plus the `OpenClose` animation. `Umbrella` is the frame (shaft, handle, spike, cord, ribs, stretchers, runner and fins). `Umbrella_Canopy` is the cloth |
| `Umbrella_Color.png`, `_Normal.png` (OpenGL), `_Roughness.png`, `_Metalness.png` | The frame's maps |
| `Umbrella_Canopy_Color.png`, `_Normal.png`, `_Roughness.png`, `_Metalness.png` | The cloth's maps. All eight panels share one panel's texture space, so the lettering stays sharp |
| `Umbrella_rig.blend` | The same rig and animation in Blender, to pose or animate further |
| `preview.png`, `preview_fin.png` | Open from above, open from below, shut, and a close-up of a fin |

## The rig

| Bone | Does |
|---|---|
| `Root` | The handle and shaft, the hub, the spike and the cord. Move it to move the umbrella |
| `Runner` | The sleeve on the shaft. It slides down as the umbrella closes |
| `Rib_1` … `Rib_8` | Each hinges at the hub and carries its rib and fin. Rotating one about its own X axis swings it shut |

- The cloth between two ribs is weighted to both of them, so it folds in between them as they close.
- Each stretcher runs from the runner to its rib. In the animation the runner is placed so the stretchers keep their
  length.

**`OpenClose` animation:** 60 frames at 30 fps. The umbrella is open at frame 1, shut by frame 20, held shut to frame
40, and open again by frame 60, all eased.

To make your own poses or animations, rotate all eight `Rib_*` bones together and slide `Runner` down to close it.
Nothing else is needed, and there are no constraints, so it works the same in Roblox's Animation Editor.

## In Studio

1. Import `Umbrella.fbx` with the 3D Importer. It comes in as a rigged model with bones.
2. Give `Umbrella` and `Umbrella_Canopy` a **SurfaceAppearance** each, with their own four maps.
3. Select `Umbrella_Canopy` and turn on **DoubleSided**. The cloth is a single sheet, so it needs this for its
   underside to show.
4. Play the imported animation, or animate the bones yourself.

## Rebuilding

```
python build_umbrella.py -- --stage preview   # quick look with live materials
python build_umbrella.py -- --stage all       # bake, rig, animate, export
```

- **Fin outline:** set by `fin_top()`, `fin_bottom()` and the `FIN_*` constants.
- **Spike:** set by `spike_w()`.
- **Size:** set by `R` (the canopy) and `Z_HUB` (the length).
- **Lettering:** set in `canopy_textures()`.
