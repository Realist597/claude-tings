# Dark Knight bow and arrow

The bow is traced from `bow_reference.jpg`, not modelled by hand, so it matches the painting exactly:
- **Shape:** its silhouette is cut out of the painting and given depth, thickest along the middle of each limb and
  blade and tapering to the edges.
- **Colour map:** the painting itself, so you get the same stylised metal and highlights. The purple inlays are
  recoloured with a gradient, from deep violet at the grip to bright lavender at the tips, and glow through an
  emissive mask.
- **Other maps:** normal, roughness and metalness are derived from the painting, so it still catches light like metal.
- **String:** a separate mesh, so you can animate the draw.

The arrow is modelled, because in the painting it's wrapped in flames. It has a barbed broadhead, a banded shaft and
jagged fletching, in stylised purple, with no effects; add those in Studio.

## What's in `export/`

| File | What it is |
|---|---|
| `BowKit.fbx` | `Weapon_Bow`, `Weapon_BowString` and `Weapon_Arrow` |
| `Weapon_<Part>_Color.png` | Base colour (sRGB) |
| `Weapon_<Part>_Normal.png` | Tangent-space normal map, OpenGL (+Y) |
| `Weapon_<Part>_Roughness.png`, `Weapon_<Part>_Metalness.png` | Roughness and metalness |
| `Weapon_Bow_Emissive.png`, `Weapon_BowString_Emissive.png` | Emissive masks: white where it glows (the purple inlays, brightest along their centres, and the string) |
| `preview.png`, `preview_1.png` | Renders with these maps |

**Sizes:**
- **Bow:** 5 studs tall, under 17,000 triangles, with the grip at its origin and the string on its +X side.
- **Arrow:** 3.1 studs long, pointing up +Z, with its nock at the origin.

## In Studio

1. Import `BowKit.fbx` with the 3D Importer.
2. Give each part a **SurfaceAppearance** with its four maps, if the importer didn't add one.
   For the glow, set the bow's and string's **emissive mask** to their `_Emissive.png`, then turn up
   **EmissiveStrength** until the purple glows the way you like (try 1–3). An optional purple **EmissiveTint**
   pushes it further. The glow takes its colour from the colour map, so it follows the gradient.
3. For a Tool, weld `Weapon_BowString` to `Weapon_Bow`. Use the bow as the Handle, or weld it to a Handle part
   at the grip.

## Rebuilding

```
python build_bow.py -- --stage preview   # quick look
python build_bow.py -- --stage all       # textures, arrow bake, previews, FBX
```

It needs `numpy`, `scipy` and `Pillow`, plus Blender 4.2+ or the pip `bpy` module. It reuses the materials and baking
from `../armor/build_armor.py`.
