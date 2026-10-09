---
name: lucid-loop
description: "Lucid Loop: build a game, app or 3D scene inside a locked art style (low-poly, clay, abstract, voxel, paper, ink) so detail is diverted into form, quantity, motion and life instead of realism. Use when the user says \"lucid loop\", names a stylized look, or wants an ambitious scene without photorealism."
license: MIT
---

# Lucid Loop

A dream you steer. Adapted from [achimala/dream-loop](https://github.com/achimala/dream-loop): the same target, build and judge loop, aimed at a locked art style instead of a photograph. See [Provenance](PROVENANCE.md).

Realism spends an agent's effort on what it authors worst: painted textures, photo materials, scanned detail. A style **lock** takes that off the table, and that raises the ceiling. Every surface becomes something Blender and code make perfectly, so effort is **diverted** into what reads as complexity: crafted form, quantity, motion, behavior and composition. Simple parts, rich scene.

Put working files in `.lucid-loop/` and gitignore it.

## Prerequisites

- Vision input, and image generation or a target image from the user.
- Subagents, strongly preferred, for the judge.
- Blender, through a Blender MCP or its Python scripting, for models. Without it, build models in code and tell the user once.
- A way to screenshot the running product at chosen times.

## 1. Lock the style

Write `.lucid-loop/style.md`. Start from the closest entry in [references/styles.md](references/styles.md); if the user named no style, pick the one that best suits the request and say which. Fill every field:

- **Palette:** 3-8 exact hex colors. All color comes from the palette; light may tint it.
- **Shapes:** the allowed geometry and its budget.
- **Surfaces:** the shading rule, using palette colors as flat or vertex colors. Image textures, normal maps, downloaded models and image-to-3D models sit outside every lock.
- **Light:** one recipe for light, shadow and fog.
- **Banned:** what would break this particular look.
- **Detail goes to:** the 2-4 channels this style spends richness on.

Done when every field holds values a judge can check from a screenshot. The lock is law for you, the image generator and the judge. It changes only when the user asks.

## 2. Dream the target

Generate a target screenshot. Ask for a real in-engine screenshot of the product, not concept art, and quote the lock in the prompt: palette hexes, shape rules and banned list. If the product already exists, screenshot it and pass that in as the base so the target refines it.

Check the result against the lock yourself and regenerate until it passes. A target the lock can't reach is a target you can't reach. Save it as `.lucid-loop/target.png`.

A user-supplied target is used as is. With no image tool and no supplied target, stop and ask the user for a target or an image API key; a prose description does not stand in for the target.

## 3. Build

Model in Blender and export `.glb` for the engine (in three.js, load with GLTFLoader). Code is for pieces too simple to be worth modeling. Blender is where a simple style gets its depth: crafted silhouettes, bevels, modifiers, rigs and baked animation, all inside the lock.

- Assign palette colors as materials.
- Use the modifier that suits the style: Decimate with flat shading for low-poly, Bevel and Subdivision for clay, Remesh in Blocks mode for voxel.
- After import, check every model's orientation, scale and pivot in the engine. Exports often arrive rotated or tiny.
- Keep each `.blend` beside its export (for example `assets/src/*.blend` and `assets/*.glb`) so later rounds edit models instead of rebuilding them.

The target fixes the look and framing. On the lock's detail channels it is a **floor**, not a ceiling: more objects, motion, reactions and crafted form than the target shows scores higher, as long as the lock holds.

## 4. Capture

Take a **contact sheet**: 3 frames about 1 second apart from the target's camera, side by side, saved as `.lucid-loop/round-NN.png`. Drive the clock (a fixed timestep or a frame-step hook) so frames repeat exactly between rounds.

Before judging, look at the sheet yourself: the product runs, models are upright and in place, nothing is missing. Fix those bugs first.

## 5. Judge

Every round, start a fresh-context subagent. Give it `style.md`, `target.png`, the current contact sheet, and the previous round's sheet and verdict if any. With no subagents, judge it yourself and tell the user.

> You are judging a product built in a locked art style. Read style.md first; it is law. Compare the contact sheet (3 frames, about 1 second apart) with the target and score:
>
> - **Lock (0-3):** list every rule break, with where it is and how to fix it. Any break caps the total at 6.
> - **Composition (0-2):** camera, framing, layout and scale of the major elements against the target.
> - **Richness (0-3):** how much is happening on the lock's "detail goes to" channels across the frames. Count objects, kinds of motion, reactions and crafted detail in the forms. Matching the target earns 2; clearly beating it earns 3. Name the three cheapest ways to add more.
> - **Cohesion (0-2):** does everything look made by one hand under one light? Name the odd ones out.
>
> Give the total out of 10 on the first line. If a previous verdict is provided, mark each of its directives LANDED, PARTIAL or NOT DONE and carry forward anything not landed. Every item must name what is wrong and how to fix it. A simple style earns its score through a full, living scene. If the product regressed, score it lower. Be blunt.

Fix every item, then return to step 4.

## 6. Decide

- **8 or more for two rounds, frame rate acceptable:** re-dream. Generate a richer target from the latest screenshot under the same lock, and return to step 3. After 2 re-dreams, stop and show the user the latest sheet beside its target.
- **8 or more, frame rate too low:** optimize, then re-judge to confirm nothing regressed.
- **Stall approaching:** the best score hasn't risen a full point in 2 rounds, or the judge named the same gap twice. Make one big-picture change: recompose the scene, remodel the key assets, rework the light or move the camera.
- **Stalled:** the big change didn't help. Stop and ask the user to weigh in.
- **Otherwise:** keep looping.

If the user gives a time budget, record the start time once the target is saved and check it between rounds. The lock holds under time pressure; spend the remaining time on richness.
