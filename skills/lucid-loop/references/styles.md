# Starting locks

Copy the closest lock into `.lucid-loop/style.md`, then tighten it for the request. The palettes are working defaults; swap them for the user's colors when given ("clay, but only blues"). Every lock shares one surface rule: color comes from the palette as flat or vertex colors. How to model each style in Blender is in [blender.md](blender.md).

## Low-poly

- **Palette:** `#2B3A55` `#3E6259` `#7FA36B` `#D9C27E` `#E8885A` `#B5523B` `#F2EBDD`
- **Shapes:** faceted forms, at most 300 triangles per prop and 2,000 per hero object.
- **Surfaces:** flat shading, one color per face.
- **Light:** one warm directional sun, cool ambient, crisp shadows, distance fog in the darkest palette color.
- **Banned:** smooth shading, gradients across a face, bloom, outlines.
- **Detail goes to:** quantity of objects, silhouettes, wind and sway, time-of-day light.

## Clay

- **Palette:** `#F4E3C3` `#E9A36B` `#D85C4A` `#6FA8A1` `#3F5E7A` `#2E2A33`
- **Shapes:** soft rounded forms with no hard edges.
- **Surfaces:** matte, slightly rough, no specular highlights.
- **Light:** one large soft key light, soft contact shadows, gentle ambient occlusion.
- **Banned:** sharp corners, metallic or glossy materials, thin details that clay couldn't hold.
- **Detail goes to:** squash and stretch, chunky characters, wobble and settle, reactions to touch.

## Abstract geometric

- **Palette:** `#111318` `#F2F0EA` `#E4572E` `#29BF12` `#FFC914`
- **Shapes:** circles, squares, triangles and lines only. Things are signified by shape, color and motion, never drawn literally.
- **Surfaces:** flat fills.
- **Light:** none, or one flat ambient; shadows only as hard offset shapes.
- **Banned:** representational objects, textures, gradients.
- **Detail goes to:** rhythm, patterns, emergent behavior, motion synced to events or sound.

## Paper cutout (2.5D)

- **Palette:** `#F6EFE0` `#E3C9A8` `#9DB4A5` `#5E7F8C` `#C9665A` `#3B3040`
- **Shapes:** flat layered planes with slightly irregular edges, stacked in depth.
- **Surfaces:** flat color per layer.
- **Light:** one directional light casting hard drop shadows between layers.
- **Banned:** rounded 3D volumes, perspective-heavy cameras, gradients.
- **Detail goes to:** parallax depth, layering, things sliding, folding and popping up.

## Voxel

- **Palette:** `#1E2A3A` `#4C6E57` `#86B05A` `#C7B26A` `#A8653F` `#D8DEE6`
- **Shapes:** cubes on one fixed grid size.
- **Surfaces:** one color per cube.
- **Light:** directional sun plus ambient occlusion in the corners.
- **Banned:** off-grid shapes, smooth surfaces, mixed grid sizes.
- **Detail goes to:** build density, destruction, growth and change over time.

## Ink and one accent

- **Palette:** `#0E0E10` `#F4F1EA` plus one accent, `#D7263D` by default
- **Shapes:** any, but read as strong silhouettes.
- **Surfaces:** black or white, with the accent on one subject or idea only.
- **Light:** hard two-tone lighting, no midtones.
- **Banned:** grays, gradients, a second accent.
- **Detail goes to:** contrast, composition, where the accent lands and moves.
