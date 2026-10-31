# Amethyst pendant (R6)

A silver necklace drawn from `reference.png`: a pear-cut amethyst, point up, held by six claws in a silver bezel. Round
that is a cage of thorns, with a big thorn at the bottom, a barbed one at each side and smaller ones higher up, and
scrolls between the bezel and the cage. It hangs from a leafed bail and a little ring on a cable chain.

It's fitted to the standard R6 body (`../armor/r6_rig_body.fbx`). The head is wider than the torso is deep, so a loop
round the "neck" can't simply lie flat. The chain lies across the top of the torso either side of the head, drapes
just over the back's top edge and comes over the front edge and down the chest. The pendant hangs mid-chest,
standing just off it.

The texturing is stylised:
- **Silver:** bright where it stands proud, darkened in its recesses, and lit from above and in front so it reads at
  a glance.
- **Stone:** faceted, each facet its own shade of violet, with a few catching the light.

Both meshes are game meshes with a detailed version's shape baked into their normal maps: round wire, rounded thorns,
granulation beads along the cage.

## What's in `export/`

| File | What it is |
|---|---|
| `Pendant.fbx` | `Pendant_Chain`, `Pendant_Charm`, and `Ref_Torso` (the R6 torso they were fitted to, used by the script to place them) |
| `Pendant_Chain_Color.png`, `_Normal.png`, `_Roughness.png`, `_Metalness.png` | The chain's maps, 512 × 512. Every link shares the same patch of them |
| `Pendant_Charm_Color.png`, `_Normal.png`, `_Roughness.png`, `_Metalness.png` | The pendant's maps, 1024 × 1024 |
| `Pendant_Charm_Emissive.png` | The stone glowing, everything else black: an emissive map for the pendant |
| `preview.png` | The game meshes with their baked maps on the R6 body, beside the reference |

Normal maps are OpenGL, as Roblox expects.

| Mesh | Triangles |
|---|---|
| `Pendant_Chain` | 5k |
| `Pendant_Charm` | 3.1k |

## Putting it in your game

1. **Import:** in Studio, go to Avatar → Import 3D (or File → Import 3D), pick `Pendant.fbx` and import it as one
   model.
2. **Textures:** give `Pendant_Chain` and `Pendant_Charm` each a **SurfaceAppearance** with their four maps, if the
   importer didn't make one.
3. **Store it:** rename the model to `Pendant` and move it into **ServerStorage**.
4. **Script:** put `Pendant.server.lua` in **ServerScriptService** as a Script.

Players then spawn wearing it. Both pieces are welded to the torso, so they move with it. On a torso that isn't the
standard size, the script scales them to fit. Set `EQUIP_ON_SPAWN = false` to hand it out yourself with
`_G.EquipPendant(character)`. Set `FLIP = true` if it comes in on the character's back.

## Rebuilding

```
python build_pendant.py -- --stage preview   # the detailed versions with their paint, rendered (quick)
python build_pendant.py -- --stage all       # build, bake, export Pendant.fbx and render preview.png
```

- **Chain's path:** `chain_path()`.
- **Link size:** `LINK_H`, `LINK_R`, `WIRE`.
- **Pendant's size:** `CHARM_SCALE`.
- **Stone's shape:** `GEM_TOP`, `GEM_H`, `GEM_HW`.
- **Colours:** `SILVER`, `OXIDE`, `HIGHLIGHT` and `GEM_*`.
