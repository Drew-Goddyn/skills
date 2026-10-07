# Provenance

Motion Loop adapts Dream Loop's build-and-judge workflow from still frames to animation. It is a separate skill, not a claim that the upstream project endorses this adaptation.

## Source and retained mechanisms

- [achimala/dream-loop](https://github.com/achimala/dream-loop/tree/9bddb901f7d071cfefdd21e264267c757177a9df), revision `9bddb901f7d071cfefdd21e264267c757177a9df`: a generated target to chase, a fresh-context judge every round, a gated score ladder with tier caps, directive tracking (LANDED / PARTIAL / NOT DONE), self-review before judging, and stall rules that force a structural change. The original MIT notice is preserved in [LICENSE](LICENSE).

## Deliberate changes

- The unit of work is a short shot (one subject, one action, 1-4 seconds), not a screenshot.
- The judge never sees video. Motion is converted into measured tracks and metrics plus still images (key-pose grid, spacing chart, strobe, speed curves).
- The target is a reference clip or a written timing sheet, with a key-pose sheet from image generation as the fallback when no video is available.
- A subject check comes first, defining the minimum rig, pivots and hierarchy needed before animating.
- Work follows the animator's pose-to-pose order: blocking, then spline, then secondary motion and polish.
- The ladder is poses, timing, spacing, secondary motion, then feel. Measurable defects (pops, jitter, foot slide, penetration, loop seams) cap the score at 5.
- It exits at 7 instead of 8, with a default cap of 6 judge rounds. The aim is a solid result, not a near-perfect match.

These are design choices, not measured performance improvements.

## Validation limit

Only the skill's discovery and file layout have been checked. It has not yet been run on a real animation task. Treat it as a draft until a bounded trial (for example, a chest lid that bursts open and settles, which needs no rig) shows the measure-and-judge steps produce useful directives.
