# Media repair

Preserve the source recording and diagnose the failing stage before converting it. Keep a usable recorder output directly when it suits delivery. Inspect the final video with `scripts/check_video.py`; supply `--expected-fps` only for the agreed recording rate.

## Capture completeness and timing

When motion is coarse or an action is missing, inspect source timestamps or distinct captured states during that action. Separate intended stillness from gaps during movement. An input log and a valid 30 fps encode can coexist with lost typing or gameplay. Re-encoding cannot recover omitted action; retain the failure and compare a suitable capture method on the same sequence.

If source image dimensions change, inspect the dimension inventory and preserve aspect ratio on a stable output canvas. Replay the retained source through any encoding repair and check duration, holds, and resumed motion. A passing resolution or frame-rate field alone does not establish those properties.

If a pixel-based stillness check fails, inspect the implicated frames and timestamps. Compression noise can split a perceptually still interval. Preserve the failing result; validate any revised detector against both real holds and missing intended motion before changing its gate.

## Conversion and playback

When conversion is needed, choose the container and codec for the requested player and remove stale inherited metadata. Probe `color_range` first. For full-range input, convert pixels from `pc` to `tv` before selecting `yuv420p`. Changing the range label alone does not convert pixels. Preserve intended duration and playback speed. Re-run the media check and watch the delivered encode.

If local embedding fails while HTTP playback works, compare a fresh copy of a known-good WebM and a clean encode of the new file in the same player. This separates file access problems from container or color signaling. An opened tab is not evidence that playback worked.

For browser-recorder problems, run the same relevant preflight with an alternate executable through `DEMO_BROWSER`. A task-local installation avoids changing unrelated browser workflows. Record the version and measured result. Choose window capture when it addresses the demonstrated need within the authorized scope.

For audio packet errors, discontinuous timestamps, or synchronization problems, retain the original audio and inspect its clock through the edit. A continuous PCM intermediate can isolate timing from the delivery codec. Verify synchronization and decode both streams after repair; a codec change or empty video-only error log is insufficient.
