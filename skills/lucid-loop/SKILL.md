---
name: lucid-loop
description: "Lucid Loop: build a game, app or 3D scene inside a locked art style (low-poly, clay, abstract, voxel, paper cutout, ink) so detail goes into form, quantity, motion and life instead of realism. Use only when the user asks for Lucid Loop by name."
license: MIT
---

# Lucid Loop

A dream you steer. Adapted from [achimala/dream-loop](https://github.com/achimala/dream-loop): the same target, build and judge loop, aimed at a locked art style instead of a photograph. See [Provenance](PROVENANCE.md).

Realism spends an agent's effort on what it authors worst: painted textures, photo materials, scanned detail. Even a strong run lands at "almost real", which reads as wrong. A style **lock** takes realism off the table, and that raises the ceiling. Every surface becomes something Blender and code make perfectly, so effort is **diverted** into what reads as complexity: crafted form, quantity, motion, behavior and composition. Simple parts, rich scene.

Put working files in `.lucid-loop/` and gitignore it.

## Prerequisites

- Vision input, and image generation or a target image from the user.
- Subagents, strongly preferred, so the judge has fresh eyes.
- Blender, through a Blender MCP or bridge (such as Higgsfield's) or its Python scripting, for models. Without it, build models in code and tell the user once.
- A way to screenshot the running product at chosen times.

## 1. Lock the style

Write `.lucid-loop/style.md`. Start from the closest entry in [references/styles.md](references/styles.md). If the user named no style, pick the one whose "detail goes to" channels best match what they want to feel alive, and say which. Fill every field:

- **Palette:** 3-8 exact hex colors. All color comes from the palette; light may tint it.
- **Shapes:** the allowed geometry and its budget.
- **Surfaces:** the shading rule, using palette colors as flat or vertex colors. Image textures, normal maps, downloaded models and image-to-3D models sit outside every lock, because they bring back the realism the lock exists to remove.
- **Light:** one recipe for light, shadow and fog.
- **Banned:** what would break this particular look.
- **Detail goes to:** the 2-4 channels this style spends richness on.

Done when every field holds values a judge can check from a screenshot. The lock is law for you, the image generator and the judge. It changes only when the user asks: a lock that bends under pressure drifts back toward realism.

## 2. Dream the target

Generate a target screenshot. Ask for a real in-engine screenshot of the product, not concept art, and quote the lock in the prompt: palette hexes, shape rules and banned list. If the product already exists, screenshot it and pass that in as the base so the target refines it.

Check the result against the lock yourself and regenerate until it passes. A target the lock can't reach is a target you can't reach. Save it as `.lucid-loop/target.png`.

A user-supplied target is used as is. With no image tool and no supplied target, stop and ask the user for a target or an image API key; a prose description is too loose to judge against.

## 3. Build

Model in Blender and export `.glb` for the engine. Before the first model, read [references/blender.md](references/blender.md) for the style recipes and the export settings that keep colors, shading and orientation intact. Use code for pieces too simple to be worth modeling. Blender is where a simple style gets its depth: crafted silhouettes, bevels, modifiers, rigs and baked animation, all inside the lock.

The target fixes the look and framing. On the lock's detail channels it is a **floor**, not a ceiling: more objects, motion, reactions and crafted form than the target shows scores higher, as long as the lock holds.

## 4. Capture

Take a **contact sheet**: 3 frames about 1 second apart from the target's camera, joined side by side into `.lucid-loop/round-NN.png` (Pillow or ffmpeg). Three frames let the judge see motion and life, which a single still hides. Drive the clock with a fixed timestep or a frame-step hook so every round captures the same moments and scores compare like with like.

Before judging, look at the sheet yourself: the product runs, models are upright and in place, nothing is missing. Fix those bugs first so judge rounds go to the look.

## 5. Judge

Every round, start a fresh-context subagent, so it judges what it sees rather than what you intended. Give it [references/judge.md](references/judge.md) as its instructions, plus `style.md`, `target.png`, the current contact sheet, and the previous round's sheet and verdict if any. With no subagents, judge from that file yourself and tell the user.

Fix every item in the verdict, then return to step 4.

## 6. Decide

- **8 or more for two rounds, at the frame rate target** (the user's, or 60 fps on desktop by default): re-dream. Generate a richer target from the latest screenshot under the same lock, and return to step 3. After 2 re-dreams, stop and show the user the latest sheet beside its target, so the direction stays theirs.
- **8 or more, below the frame rate target:** optimize, then re-judge to confirm nothing regressed.
- **Stall approaching:** the best score hasn't risen a full point in 2 rounds, or the judge named the same gap twice. Small tweaks have stopped working, so make one big-picture change: recompose the scene, remodel the key assets, rework the light or move the camera.
- **Stalled:** the big change didn't help. Stop and ask the user to weigh in.
- **Otherwise:** keep looping.

If the user gives a time budget, record the start time once the target is saved and check it between rounds. The lock holds under time pressure; spend the remaining time on richness.
