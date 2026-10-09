# Provenance

Lucid Loop adapts Dream Loop's build-and-judge workflow from chasing realism to working inside a locked art style. It is a separate skill, not a claim that the upstream project endorses this adaptation.

## Source and retained mechanisms

- [achimala/dream-loop](https://github.com/achimala/dream-loop/tree/9bddb901f7d071cfefdd21e264267c757177a9df), revision `9bddb901f7d071cfefdd21e264267c757177a9df`: a generated target to chase, prompted as an in-engine screenshot rather than concept art; refining an existing product's screenshot instead of replacing it; a fresh-context judge every round with a 0-10 rubric; exit at 8; stall rules that force a big-picture change; time budgets; and re-dreaming a better target from the current state. The original MIT notice is preserved in [LICENSE](LICENSE).

## Deliberate changes

- A style lock (palette, shapes, surfaces, light, banned list, and where detail goes) is written before the target and binds the builder, the image generator and the judge.
- The target is generated inside the lock and rejected if it breaks it.
- The asset ladder is reduced to Blender, with code for trivial pieces. Downloads, image-to-3D models, and generated textures and normal maps are dropped.
- The rubric is Lock, Composition, Richness and Cohesion instead of Composition, Lighting, Materials and Details. Any lock break caps the score at 6.
- On the lock's detail channels the target is a floor, not a ceiling: exceeding it scores higher.
- The judge sees a 3-frame contact sheet, so motion and life count.
- Each scene names a hook (a situation, a point of view, or something that reacts) that the judge scores under Composition, and every hand-back includes up to 3 play notes. Dream Loop has neither.
- The Plus/Pro workflow split and model-tier checks are removed. Directive tracking (LANDED / PARTIAL / NOT DONE) is borrowed from Motion Loop.

These are design choices, not measured performance improvements.

## Validation limit

Only the skill's discovery and file layout have been checked. It has not yet been run on a real build. Treat it as a draft until a bounded trial (for example, a small low-poly harbor at dusk with boats, birds, lights and smoke) shows the lock, judge and re-dream steps produce useful results.
