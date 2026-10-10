# New bow and arrow: textures and draw rig

Your `new_bow_and_arrow.fbx`, textured in stylised black metal with glowing purple accents, mostly black. The meshes
are exactly as you modelled them.

## What's in `export/`

| File | What it is |
|---|---|
| `NewBow.fbx` | Your `bow` (skinned to the `BowRig` armature) and `arrow` meshes, each with a fresh, non-overlapping UV map, plus the baked **Draw** animation |
| `NewBow_rig.blend` | The same rig in Blender with the **live IK**, so you can pose or animate it yourself |
| `NewBow_<Bow\|Arrow>_Color.png` | Base colour (sRGB) |
| `NewBow_<Bow\|Arrow>_Normal.png` | Normal map, OpenGL (+Y); it rounds the hard edges slightly so they catch light |
| `NewBow_<Bow\|Arrow>_Roughness.png`, `_Metalness.png` | Roughness and metalness |
| `NewBow_<Bow\|Arrow>_Emissive.png` | Emissive mask: white on the purple parts, so they glow |
| `preview_0.png`, `preview_1.png` | Renders with these maps |
| `draw_compare.png` | Rest pose next to full draw |

Your original UVs overlapped, with mirrored halves and stacked faces sharing texture space, which a baked texture
can't use. Import `NewBow.fbx`, not the original, so the meshes carry the new UVs.

## The look

- **Black metal:** a smooth dark gradient, with painted-style light edges carrying a faint purple sheen and darker
  crevices. There are no noisy scratches, so it reads stylised.
- **Purple (glowing):** a dark gradient from near-black violet at the grip to a deep royal purple at the tips. It covers the faces of the
  two discs and their centre pins, the thin strips set into the limbs, the string, and the arrow's head and fletching.

## The rig

| Bone | Does |
|---|---|
| `Root` | The grip. Move or rotate this to move the whole bow |
| `Pull` | The string's nocking point. **Drag it back along +X (its local Y) to draw**; full draw is 0.2 units |
| `Limb_Upper_1..3`, `Limb_Lower_1..3` | The limbs, three bones each, driven by IK |
| `Tip_Upper`, `Tip_Lower` | IK targets for the limbs (non-deforming) |

The string is weighted between `Pull` and the limb tips, so it stays straight on both sides and forms a clean V.
In the `.blend`, each limb has an IK chain (3 bones) aimed at its tip target. A Transform constraint moves the
targets back and inward as `Pull` goes back, so pulling one bone draws the string **and** bends the limbs.

**Draw animation** (60 frames at 30 fps): pull back (frames 1–26), hold at full draw (to 42), then release with a
small string twang that settles by frame 60.

Roblox doesn't import IK or constraints, so the FBX carries this animation **baked** onto the bones. In Studio you
can:
- play the baked animation (import the rig with the Animation Editor and publish it), or
- animate it yourself by moving `Pull` back and keying the limb bones, or by posing in the `.blend` and re-exporting.
  To bend the limbs from `Pull` live in Studio, add an `IKControl` per limb.

## In Studio

1. Import `NewBow.fbx` (it comes in as a rigged model with bones).
2. Give each MeshPart a **SurfaceAppearance** with its `Color`, `Normal`, `Roughness` and `Metalness` maps.
3. For the glow, set its **emissive mask** to the `_Emissive.png` and raise **EmissiveStrength**. Try 1–2.

## Rebuilding

```
python texture_new_bow.py -- --stage preview   # quick look with live materials
python texture_new_bow.py -- --stage all       # unwrap, bake, preview, rig, animate, export
python texture_new_bow.py -- --stage rigtest   # renders rest and drawn poses of the rig
```

Which pieces are purple is decided in `is_purple()`, and the colours are in `material()`, the rig is in `rig()`, and the animation is in `draw_action()` (`DRAW` sets the draw length).
