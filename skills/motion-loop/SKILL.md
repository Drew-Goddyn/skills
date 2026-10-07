---
name: motion-loop
description: Animate an existing character, object or UI element from a short action description so its motion matches a reference clip or timing sheet. Use when the user says "motion loop" or asks for a specific animation (an attack, a jump, a UI transition, a mechanism) to look good, not just move.
license: MIT
---

# motion-loop

A build-and-judge loop for motion, adapted from [achimala/dream-loop](https://github.com/achimala/dream-loop), which does the same for stills. See [Provenance](PROVENANCE.md).

The goal is a solid, readable animation: clear poses, believable timing, proper easing and no glitches. It is not perfection. Most agent-made animation fails at the basics: linear tweens, no anticipation, floaty timing, sliding feet, pops. This loop exists to fix those reliably and then stop. It aims for 7/10, not 10/10.

The judge never watches video. Motion is turned into numbers (tracks, timings, speed curves) and still images (key-pose grids, spacing charts, strobes) that a vision model and a script can judge reliably.

## Input and output

**Input**
- A one-line action description covering subject, action, rough duration, view and feel. Example: "The knight does a heavy two-handed overhead slam, about 2 s, side view, slow wind-up, brutal impact."
- The subject: a model, rig, object or UI element (see Step 1).
- Optionally, a reference clip.

**Output**
- The animation as data in the target's own format (Blender action, glTF clip, engine animation asset, or motion code) that plays in real time.
- A final preview render (mp4) and the key-pose grid.
- The final metrics and verdict.

Put working files in `.motion-loop/` and gitignore it unless the user says otherwise.

## Prerequisites

- Vision input, and subagents (strongly preferred, for the judge).
- A scriptable way to pose, render and read back transforms frame by frame: Blender via Python, or the target engine driven by script.
- Python with numpy, matplotlib and opencv. A pose estimator (e.g. MediaPipe) for human references, and optionally a point tracker for objects.
- Image generation (for the fallback reference). Video generation is optional.

If you can't render deterministically or read back per-frame transforms, flag it early and stop.

## Scope: one shot at a time

A shot is a fixed camera, one subject, one action, 1-4 seconds. Split longer sequences into shots and loop each one. Work at 30 fps unless the target requires otherwise. All frame counts below assume 30 fps.

## Step 1: Subject check

Before animating, confirm the subject can physically make the moves the action needs. Write findings to `.motion-loop/subject-check.md`. Fix what's cheap. Otherwise stop and tell the user exactly what's missing.

**Humanoid character, minimum viable rig**
- A skeleton (armature) with at least: root, hips, 2-3 spine bones, neck, head, and on each side: upper arm, forearm, hand, thigh, shin, foot. That's about 18 bones. Fingers, toes and face are optional.
- The mesh attached to the bones in one of two ways:
  - **Rigid parts:** each piece is parented to exactly one bone. This is the easiest and most robust option, and it suits armor, robots, toys and low-poly models.
  - **Skinned:** a weight-painted mesh. Test it by posing extremes (arms overhead, deep crouch, torso twist). If the mesh tears, collapses at the joints, or twists like a candy wrapper, flag it.
- Rest pose is a T- or A-pose, feet on the ground at the origin, real-world scale (meters), and a known forward axis.
- Consistent left/right bone names.
- Pivots at real joints: the elbow bends at the elbow.
- Anything else the action needs, such as a weapon parented to the hand bone at the grip.

If there's no rig and Blender is available, build a rigid-parts rig: the minimum armature, with the model split into pieces each parented to one bone. Automatic skin weights are worth one try, but verify them with extreme poses and fall back to rigid parts if they fail. If external tools are allowed, an auto-rigging service is also an option.

**Object or mechanism**
- Each moving part is a separate object (or bone) with its pivot where it physically rotates: a lid on its hinge line, a wheel at its axle.
- The parent hierarchy matches physical attachment (lid is a child of the chest).
- If the action deforms the object (squash, jiggle, bend), there must be something to drive it: enough geometry plus bones, a lattice, or shape keys.

**UI**
- Every moving element is individually addressable, its transform origin sits where it should pivot, and the start and end states are known.

**Secondary motion** (cape, hair, tail, chain) needs its own 3-5 bone chain or a simulation. Without one, it's out of scope; note that in the subject check.

## Step 2: Reference

Build the target the loop will chase. Use the first option available:

1. **A reference clip from the user.** This is the best option.
2. **The user films themselves acting it out on a phone.** Suggest this for human actions when no clip exists. Animators work this way.
3. **Generated video,** if you have a video-generation tool. Generate 3-4 candidates. In the prompt, ask for a plain background, a locked-off camera matching the requested view, a single subject fully in frame, real-time speed and no cuts. Reject candidates that drift into slow motion or floaty physics, which video models tend to do. Generated motion is fine for poses and rough timing but unreliable for weight, so rely on the timing sheet for weight.
4. **No video available:** generate a key-pose sheet with image generation (4-7 key poses, same view, same character, plain background) and write the timing sheet yourself.

Trim the reference to just the action and resample it to 30 fps.

**Extract from the reference**
- **Key poses:** frames where the main mover hits an extreme (speed near zero, or a change of direction). Save them to `.motion-loop/reference/poses/`.
- **Tracks (when you have a clip):** 2D positions per frame. Use a pose estimator for humans. For objects, use a point tracker on 2-6 points on the moving parts if one is available; otherwise mark key poses only.
- **Normalize:** express positions relative to subject height and the ground or root, and time in frames.

**Timing sheet:** always write `.motion-loop/timing-sheet.md`, even when you have a clip (in which case derive it from the tracks). It's a table with one row per key pose: name, frame, hold length, easing in and out, and notes (anticipation depth, overshoot, which parts lag).

Starting points when writing a timing sheet without a clip (30 fps, human scale). Adjust for size and feel: heavier means a longer wind-up, a faster strike and a longer settle.
- **Anticipation:** 6-12 frames for heavy actions, 3-6 for light ones, moving opposite to the main action.
- **Main action:** the fastest part, often 3-8 frames.
- **Impact or contact hold:** 2-6 frames.
- **Overshoot then settle:** 8-30 frames.
- **Loose parts** lag the part driving them by 2-5 frames.
- **Easing:** ease into and out of every held pose. Use linear only for mechanical, constant-speed motion.
- **Arcs:** limbs and swung objects travel in arcs, not straight lines.

If you generated the reference or wrote the timing sheet yourself, show the user the key-pose sheet and timing sheet and confirm them before building. Keep that check brief.

## Step 3: Build in passes

Animators work pose to pose, and so does this loop.

1. **Blocking.** Set only the key poses from the timing sheet, with stepped interpolation (each pose holds until the next one, no in-betweens). Judge this pass for Tier 1 before doing anything else. Fixing a pose now is cheap; fixing it after spacing is expensive.
2. **Spline.** Switch to smooth interpolation. Set easing, anticipation and overshoot to match the timing sheet. Add in-between poses wherever an arc has gone straight.
3. **Secondary and polish.** Follow-through, overlapping action, contacts, settle, and defect fixes.

Pick whichever method suits the subject: keyframes on bones for characters; keyframes or code (easing functions, springs) for UI and mechanisms; procedural or physics for jiggle and cloth. Mixing methods is fine.

## Step 4: Capture

Every round, use the same camera, resolution and fps as the reference.

- **Render deterministically:** a fixed timestep with every frame rendered offline. Never screen-record, because it drops frames. In Blender, render headless via Python. In a browser, take control of the clock (a fixed or fake clock, or a manual frame-step hook) and capture each frame.
- **Export engine data per frame:** the world position of key joints or parts, plus contact points, projected into the camera's 2D view. This data is exact, so use it as the build's tracks. If the reference tracks came from a pose estimator, also run that estimator on the build render and compare estimator output to estimator output, which is usually the fairer pairing.

## Step 5: Measure

Write `metrics.py` once and reuse it every round. It writes `.motion-loop/rounds/NN/metrics.json` plus the images below. First choose the main mover: the part carrying the action, such as the weapon tip, the hips, or the edge of a lid.

**Numbers**
- **Duration error:** build length vs reference length, as a percentage.
- **Key-pose timing:** detect extremes in the build the same way as in the reference, then report each key pose's frame in both and the error in frames.
- **Speed-profile match:** stretch both to the same duration, then report the correlation between the main mover's speed curves.
- **Anticipation:** whether the main mover moves opposite to the main action beforehand, how far (as a percentage of the main travel), and for how many frames.
- **Overshoot and settle:** the largest overshoot past the final position as a percentage, and the number of frames until it stays within 2% of final.
- **Follow-through lag:** frames between the driver's speed peak and the follower's (hips to hand, body to cape).
- **Arc:** the largest deviation from a straight line between consecutive key poses, normalized. Near zero on a swing means a straight-line tween.
- **Defects (always reported):**
  - **Pops:** a frame where speed exceeds 4× the local median and drops back the next frame.
  - **Jitter:** high-frequency wobble (second-difference energy) above a threshold during holds.
  - **Foot slide:** a planted foot moving more than 1% of body height per frame.
  - **Penetration:** parts passing through the ground or the body (use engine data where possible).
  - **Loop seam (cycles only):** mismatch between the first and last frame.

**Images.** These and the numbers are all the judge sees.
- `poses.png`: a grid with one column per key pose, reference on top and build below, matched by name.
- `spacing.png`: the main mover's path with one dot per frame, reference and build side by side. Bunched dots mean slow, spread-out dots mean fast, so easing is visible at a glance.
- `strobe.png`: an onion-skin of the whole subject every 2-3 frames, with older frames faded, for both reference and build.
- `speed.png`: both speed curves overlaid on normalized time, with key poses marked.
- `contact.png` (when relevant): foot or contact height over time.

## Step 6: Self-check, then judge

Before every judge call, review the images and metrics yourself. Don't submit a pass that has flagged defects, missing key poses, or unfinished work. Write a short, honest note to `rounds/NN/self-check.md`.

The judge is a fresh subagent with a clean context every round. Give it the action description, the timing sheet, `metrics.json`, and every image. From round 2 on, also give it the previous round's verdict. If you have no subagents, judge it yourself and tell the user you're doing so.

Judge prompt:

> You are an animation director reviewing a real-time animation against its reference. You will not see video.
> You get still images (key poses side by side, spacing charts, strobes, speed curves) and measured metrics.
> Trust the metrics for timing and defects, and use the images for poses, silhouettes, arcs and spacing.
> Score 0-10 on this ladder. It is gated: a pass cannot score above a tier's cap until every requirement of the
> tiers below it is met.
>
> - **Tier 1, poses (0-3):** every key pose is present and in order; each silhouette reads clearly; each pose
>   matches the reference in direction and broad shape (major limbs within about 15% of body height of where they
>   should be). No broken deformation at any key pose. Judge layout, not polish. Cap 3.
> - **Tier 2, timing (3-5):** total duration within 15% of the reference; every key pose within 3 frames of the
>   reference or timing sheet; holds present where specified. Cap 5.
> - **Tier 3, spacing (5-7):** eases into and out of held poses; anticipation and overshoot present wherever the
>   reference has them, at roughly the right depth (within about 50%); limbs and swung objects travel in arcs;
>   the speed curve follows the reference's shape. Cap 7.
> - **Tier 4, secondary and contact (7-9):** loose parts lag and settle; feet stay planted; impacts read; weight
>   feels right. Cap 9.
> - **Tier 5 (9-10):** matches the reference in feel.
>
> Defects (pops, jitter, foot slide, penetration, mesh tearing, loop seam) block at every tier: any defect caps the
> score at 5.
>
> This is animation, not motion capture. A bigger anticipation or overshoot than the reference is fine if the
> timing structure holds and it reads better. Penalize missing structure, not stylization.
>
> If a previous verdict is provided, you are one reviewer in a sequence. Go through its directives one by one and
> mark each LANDED, PARTIAL or NOT DONE. Carry forward anything not landed. Don't reverse a prior directive unless
> the result is clearly worse, and if you do, say why.
>
> Output format:
> 1. The score on the first line, then "Tier N" (the highest tier whose gate is fully passed) on the second.
> 1b. If given a previous verdict, the LANDED / PARTIAL / NOT DONE list.
> 2. "Defects:" each one with its frame range and a fix.
> 3. "Blocking:" what fails the next tier's gate. Name the part and the key pose, and give magnitudes in frames
>    and percentages. For example: "Slam: anticipation lasts 4 frames and pulls back 5%; the reference is 9 frames
>    at 15%. Extend the wind-up to frames 6-15 and draw the sword further back over the shoulder."
> 4. At most 3 further directives, ordered by points recoverable.
>
> Never give vague feedback such as "feels floaty" without naming the cause, for example: "Landing settles in
> 3 frames; the reference takes 14. The hips stop dead at contact." Don't round up: if a gate isn't fully passed,
> the cap holds.

## Exit criteria

- **Score of 7 or more with no defects:** done. Show the user the preview render and key-pose grid, and ask whether they want a polish pass (Tier 4).
- **Round cap:** 6 judge rounds by default (the user can change this). At the cap, stop and deliver the best round so far.
- **Stall approaching:** the best score hasn't improved by a full point in 2 rounds, or the judge has named the same gap 3 times. Stop tweaking and make one structural change:
  - re-block from scratch off the key poses;
  - switch method (keyframes ↔ code, springs or physics);
  - change the reference (a cleaner clip, user-filmed footage, or a rewritten timing sheet);
  - fix the subject (pivots, rig, rigid parts instead of bad skinning).
- **Stalled:** after one structural change, 2 more rounds without improvement. Stop and report the score, what's blocking, the likely cause (often the rig or the reference), and options.
- **Otherwise:** each round, fix all defects and most of the blocking items, not just the top one. Revert only if the score dropped by a full point; smaller dips are judge noise. If one specific change clearly caused a regression, undo just that change.

Expect a 7 to mean clean poses, sound timing, real easing, no glitches and the basics of weight. The last stretch of feel still needs a human eye, so that's where this loop hands back.

## Chaining with a visual build loop

If the subject doesn't exist yet, build it first with a visual build loop (such as Dream Graph or dream-loop), then run the subject check. Don't build and animate in the same loop: when a frame looks bad, the judge can't tell whether the motion or the model is at fault.
