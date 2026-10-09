# Blender for Lucid Loop

Read before the first model. Work through the Blender MCP if one is connected, otherwise through Blender's Python (`blender --background --python script.py`). One Blender unit is one meter, which is also one three.js unit.

## Palette materials

Make one material per palette color and reuse them on every model, so the whole scene shares exactly the lock's colors. Use a Principled BSDF with Metallic 0 and Roughness 0.7-1.0 for a matte look; it exports as a standard glTF material and loads in three.js as `MeshStandardMaterial`.

Hex codes are sRGB, but Blender's Python color values are linear. Setting a hex directly makes every color too bright, so convert first:

```python
import bpy

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def palette_material(name, hex_code, roughness=0.9):
    h = hex_code.lstrip("#")
    rgb = [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = roughness
    return mat
```

On the three.js side, keep the renderer's output color space at sRGB (the default) so the palette round-trips.

## Style recipes

- **Low-poly:** model from simple shapes, add a Decimate modifier (Collapse) until faces read clearly, then `shade_flat()`. Color by face: assign different palette materials to face groups.
- **Clay:** Bevel modifier with several segments, then Subdivision Surface (level 2), then `shade_smooth()`. Exaggerate proportions; clay reads through chunky silhouettes.
- **Voxel:** model the rough form, then a Remesh modifier in Blocks mode, at one octree depth for the whole scene so the grid stays consistent.
- **Paper cutout:** draw shapes as curves, extrude a few millimeters, and space layers apart in depth.
- **Abstract and ink:** primitives are often enough in code; use Blender when a form needs care.

## Animation

Rig with an armature, or parent rigid parts to bones. Give each action a clear name (`idle`, `bob`, `wave`); each exported action becomes a clip in three.js, played with `AnimationMixer`. Baked animation is where a simple model gains life cheaply.

## Export

Before exporting, look at the model in a viewport screenshot. Then:

1. Set the origin where the model should pivot, usually the base center for anything that stands on the ground.
2. Apply rotation and scale (`bpy.ops.object.transform_apply(rotation=True, scale=True)`), so the engine receives the model as it looks.
3. Export glTF binary with modifiers applied and the default +Y Up setting:

```python
bpy.ops.export_scene.gltf(filepath="assets/boat.glb", export_format="GLB",
                          use_selection=True, export_apply=True)
```

Keep each `.blend` beside its export (for example `assets/src/boat.blend` and `assets/boat.glb`) so later rounds edit the model instead of rebuilding it.

After loading in the engine, check orientation, scale and pivot against the target. Most "broken model" bugs are one of those three.
