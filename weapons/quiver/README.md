# Quiver (R6)

A quiver for the new bow, slung on the back of the plain R6 rig with five of the bow's own arrows in it. It matches
the bow's look: stylised black metal with light steel edges, black leather, and glowing deep-purple inlays.

- **Bandolier:** a black leather strap that runs over the right shoulder, across the chest and under the left arm.
  - It lies flat on the torso all the way round.
  - It has a black buckle, studs, and a purple gem on the chest.
- **Quiver body:** black leather, riding along the strap's back stretch with its mouth behind the right shoulder,
  where the right hand can reach. It's fitted with:
  - a black metal collar with six points and a glowing ring
  - a faceted black point at the base, ringed in purple
  - a black spine down the outside, with a glowing line and a purple gem
  - two black bands with glowing inlays
  - blade fins sweeping back from the mouth, like the bow's limbs
  - two leather ties holding it to the strap
- **Arrows:** five arrows from `../new_bow/export/NewBow.fbx`, nocks up and fanned a little. They're scaled to 6 times
  that file's size, so they're about 2.8 studs long. To match them, scale the bow by the same amount.

## What's in `export/`

| File | What it is |
|---|---|
| `QuiverKit.fbx` | `Quiver` (the quiver and bandolier, about 14k triangles), `Quiver_Arrows` (the five arrows), and `Ref_Torso`, the R6 torso it was fitted to |
| `Quiver_Color.png`, `_Normal.png` (OpenGL), `_Roughness.png`, `_Metalness.png` | The quiver's maps |
| `Quiver_Emissive.png` | Emissive mask: white on the purple parts, so they glow |
| `Quiver_Arrows_*.png` | The arrows' maps (the bow's `NewBow_Arrow_*` maps, copied here) |
| `preview.png`, `preview_closeup.png` | Renders using the baked maps |

## In Studio

1. Import `QuiverKit.fbx` as one model.
2. Give `Quiver` and `Quiver_Arrows` a **SurfaceAppearance** each, with their maps. For the glow, set the emissive
   mask to the `_Emissive.png` and raise **EmissiveStrength** (try 1–2).
3. Name the model `QuiverKit` and put it in **ServerStorage**.
4. Put `Quiver.server.lua` in **ServerScriptService**.

Players then spawn wearing it, welded to the torso.

## Rebuilding

```
python build_quiver.py -- --stage preview   # quick look with live materials
python build_quiver.py -- --stage all       # bake, preview, export
```

The strap's path is set by `P1` (over the shoulder) and `E_S` (its slope). The quiver's size is set by `L_Q`, `qw()`
and `qd()`, and the arrows' scale by `S`.
