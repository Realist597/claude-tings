# New bow and arrow: textures

Your `new_bow_and_arrow.fbx`, textured in stylised black metal with glowing purple accents, mostly black. The meshes
are exactly as you modelled them.

## What's in `export/`

| File | What it is |
|---|---|
| `NewBow.fbx` | Your `bow` and `arrow` meshes, each with a fresh, non-overlapping UV map |
| `NewBow_<Bow\|Arrow>_Color.png` | Base colour (sRGB) |
| `NewBow_<Bow\|Arrow>_Normal.png` | Normal map, OpenGL (+Y); it rounds the hard edges slightly so they catch light |
| `NewBow_<Bow\|Arrow>_Roughness.png`, `_Metalness.png` | Roughness and metalness |
| `NewBow_<Bow\|Arrow>_Emissive.png` | Emissive mask: white on the purple parts, so they glow |
| `preview_0.png`, `preview_1.png` | Renders with these maps |

Your original UVs overlapped, with mirrored halves and stacked faces sharing texture space, which a baked texture
can't use. Import `NewBow.fbx`, not the original, so the meshes carry the new UVs.

## The look

- **Black metal:** a smooth dark gradient, with painted-style light edges carrying a faint purple sheen and darker
  crevices. There are no noisy scratches, so it reads stylised.
- **Purple (glowing):** a gradient from deep violet at the grip to bright purple at the tips. It covers the faces of the
  two discs and their centre pins, the thin strips set into the limbs, the string, and the arrow's head and fletching.

## In Studio

1. Import `NewBow.fbx`.
2. Give each MeshPart a **SurfaceAppearance** with its `Color`, `Normal`, `Roughness` and `Metalness` maps.
3. For the glow, set its **emissive mask** to the `_Emissive.png` and raise **EmissiveStrength**. Try 1–2.

## Rebuilding

```
python texture_new_bow.py -- --stage preview   # quick look with live materials
python texture_new_bow.py -- --stage all       # unwrap, bake, preview, export
```

Which pieces are purple is decided in `is_purple()`, and the colours are in `material()`.
