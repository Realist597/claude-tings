# The Brute (R6)

An original hulking barbarian, built on your own muscle body (`source/muscle_body.obj` and its three normal maps).

- **Skin:** dark charcoal and matte, painted from the muscles in your normal maps (creases darker, ridges catching the
  light). It's battle-worn: grime worked into the creases, dust, bruises, cuts and scrapes, dried blood spatter, a few
  old scars, and veins standing out across it. The pores, scars, cuts and veins are added into your normal maps too.
- **Head:** a plain R6 head, scaled to the body, in the same skin. A normal face decal sits on it.
- **Gear:** iron worn black, scratched and pitting, rusting in its grooves and in runs, with silver trim tarnished black
  in its grooves and rubbed bright on its edges. Leather is scuffed and cracked, and the cloth is stained.
  - **Wrists and shins:** iron cuffs between rolled silver rims, studded all round, shaped to each limb's own blocky
    form.
  - **Elbows:** a riveted iron guard strapped over each elbow, with a long edged spike swept back and out of a domed
    collar.
  - **Waist:** a double leather belt with silver studs and a turned silver boss.
  - **Loincloth:** front and back flaps of oxblood cloth, pleated, torn ragged at the hem and rigged.
  - **Hips:** leather strips hanging over the outside of each thigh, tipped in silver.

## What's in `export/`

| File | What it is |
|---|---|
| `Brute.fbx` | Everything as one model. **Body:** `Brute_Torso`, `Brute_LeftArm`, `Brute_RightArm`, `Brute_LeftLeg`, `Brute_RightLeg` (your mesh, with its own UVs) and `Brute_Head`. **Gear:** `Brute_Gear_Torso` (the belts), `Brute_Gear_LeftArm`, `Brute_Gear_RightArm`, `Brute_Gear_LeftLeg`, `Brute_Gear_RightLeg`. **Loincloth:** `Brute_Gear_LoinFront` and `Brute_Gear_LoinBack`, with their bones |
| `Brute_Gear_<Part>_Color.png`, `_Normal.png`, `_Roughness.png`, `_Metalness.png` | Each gear mesh's maps (normal maps are OpenGL, as Roblox expects) |
| `textures/normal_torso_*.png`, `normal_a_*.png`, `normal_b_*.png`, `head_*.png` | The body's and head's skin, in sets of three: `_skin` (colour), `_detail` (normal), `_rough` (roughness) |
| `Brute_Head.fbx` | The head on its own |
| `steps/` | Renders of the build, step by step. `step_11_final.png` uses the baked maps, so it shows what Roblox will show |

### Which skin maps go where

| MeshPart | ColorMap | NormalMap | RoughnessMap |
|---|---|---|---|
| `Brute_Torso` | `normal_torso_skin.png` | `normal_torso_detail.png` | `normal_torso_rough.png` |
| `Brute_LeftArm`, `Brute_RightArm` | `normal_a_skin.png` | `normal_a_detail.png` | `normal_a_rough.png` |
| `Brute_LeftLeg`, `Brute_RightLeg` | `normal_b_skin.png` | `normal_b_detail.png` | `normal_b_rough.png` |
| `Brute_Head` | `head_skin.png` | `head_detail.png` | `head_rough.png` |

The skin isn't metal, so leave MetalnessMap empty. These maps fit your own body mesh's UVs as well. If your game
already uses that body, you can put them straight onto it.

Triangles:

| Part | Triangles |
|---|---|
| Body | 5.5k |
| Head | 1.7k |
| Each arm's gear | 9.1k |
| Each leg's gear | 7.1k |
| The belts | 6k |
| Each loincloth flap | 4.3k to 4.6k |

Every mesh is under Roblox's 20,000-triangle limit. The gear's maps are 1024 × 1024.

## Putting it in your game

1. **Import:** in Studio, go to Avatar → Import 3D (or File → Import 3D), pick `Brute.fbx` and import it as one model.
2. **Textures:** give each MeshPart a **SurfaceAppearance**, if the importer didn't make one:
   - **Gear:** each `Brute_Gear_*` part takes its own four maps.
   - **Body and head:** use the skin maps from the table above.
3. **Store it:** rename the model to `Brute` and move it into **ServerStorage**.
4. **Script:** put `Brute.server.lua` in **ServerScriptService** as a Script.

Players then spawn as the Brute:

- The Brute's body and head are welded over the character's own parts, which are hidden, and any face decal moves
  onto the Brute's head.
- Each piece of gear is welded to its body part: the belts and the loincloth to the torso, the cuffs and elbow guards
  to the arms and legs. So it all moves with R6 animations.

Options at the top of the script:

| Option | What it does |
|---|---|
| `WEAR_BODY = false` | Puts only the gear on the character's own body |
| `HIDE_ACCESSORIES` | Removes hats and hair the character spawns with |
| `FLIP = true` | Turns it round, if it comes in facing backwards |
| `EQUIP_ON_SPAWN = false` | Stops everyone spawning as the Brute. Call `_G.EquipBrute(character)` from another server script yourself |

The gear was fitted to the Brute's body. On a character with smaller or bigger parts, the script scales every piece by
how tall that body part is next to the Brute's.

## The loincloth's bones

Each flap is rigged for you to animate, for example with Smart Bones:

| Mesh | Root bone | Chains |
|---|---|---|
| `Brute_Gear_LoinFront` | `LoinFrontRoot` (under the belt) | three chains across the flap, `LoinFront_<chain>_<0..2>`, top to bottom |
| `Brute_Gear_LoinBack` | `LoinBackRoot` | three chains, `LoinBack_<chain>_<0..2>` |

Each root should stay still. Every vertex has at most four bone influences, and the weights blend between neighbouring
bones, so the cloth bends smoothly rather than kinking.

## Rebuilding

```
python build_brute.py -- --stage body    # the body and its skin maps
python build_brute.py -- --stage head    # the plain head, exported as Brute_Head.fbx
python build_brute.py -- --stage gear    # a quick look at the gear with its live materials
python build_brute.py -- --stage all     # bake the gear, rig the loincloth, export Brute.fbx
```

- **Skin tone:** set by `SKIN`.
- **Elbow:** the elbow's height is `ELBOW_Z`, and its spike is set in `elbow_spike()`.
- **Wear:** set in `worn_material()`.
- **Skin's battle wear:** set in `skin_maps()`.
