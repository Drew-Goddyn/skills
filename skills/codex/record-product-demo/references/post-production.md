# Post-production

Read this when the brief needs cuts, titles, sound, retiming, or a revision to an existing edit. Scale the work to the request: a simple trim does not need a soundtrack or a multi-stage production framework.

## Preserve source and edit decisions

Keep original footage and audio separate from edited outputs. Record the cut list in a machine-readable form: source file and in/out times, destination times, camera/source identity where needed, and any crop, title, freeze, or speed change. Keep inputs and render commands sufficient to rebuild the delivered edit.

Preserve the causal sequence needed for the viewer's understanding. Keep performance demonstrations faithful to their measured timing. For a cinematic brief, cuts, slow motion, and speed ramps can serve the presentation when they remain traceable to real footage and do not misrepresent the game or application. Record such transformations with the edit.

Once the picture is settled, retain it independently of the soundtrack. A music revision should reuse it, copying the video stream when compatible. Verify unchanged picture with decoded-frame comparisons when that is the intended boundary. Re-capture only when the requested revision or a source defect requires it.

## Add sound when it serves the brief

Keep recorded game/application sound, music, and the final mix separately when available. Preserve supplied tracks and their identities; record the excerpts and transformations actually used. Retain quiet intervals, manage peaks, and make room for meaningful product sounds. Meter readings support technical checks; the perceived balance still needs listening.

For generated music, provide the mood, instrumentation, broad energy arc, important transitions, and ending. Treat requested timestamps as arrangement targets, then inspect the returned track. Request stems or a usable tail when they help the edit; a stereo mix can be sufficient. Keep genre, tempo, titles, and the particular dramatic arc in the task brief.

If the music is longer than the picture, select passages around musical structure and the visual beats. Record cuts, crossfades, gain changes, and any time or pitch processing. An end title needs an intentional musical ending or decay.

## Render and review the changed work

Use a clean audio timeline for the final mix. Run `python3 scripts/check_video.py reel.mp4 --audio-policy require` when the brief requires sound, adding its media limits. The default `forbid` policy rejects audio tracks; `--audio-policy allow` (also `--allow-audio`) permits a silent reel. Every present audio track is decoded under all policies.

The JSON report separates `picture` and per-track `audio` presentation intervals. Start, end, and duration differences exceeding one video frame fail with an audio/picture timing diagnostic. Decoded timestamps retain stream offsets and codec skip/discard handling; a shorter signalled final audio-frame duration trims codec padding. The legacy top-level `duration_seconds` and `--max-duration` still use container duration. Missing timing or decode errors fail rather than establish alignment.

Set `--min-duration SECONDS` when the brief has a minimum. It checks the decoded picture's presentation span, excluding its start offset; a longer soundtrack cannot satisfy a picture minimum. Equality passes with no tolerance added. Seconds must be finite and nonnegative; decimals and fractions such as `59/30` are accepted. Omitting the option imposes no minimum. For a silent 15–30 second brief, use `--min-duration 15 --max-duration 30 --audio-policy forbid`.

The report preserves the probe's `pixel_format` and `color_range` values, with separate `known`, `unknown`, or `missing` statuses. Missing values are `null`; an explicit unknown value stays visible. `tv` means limited range and `pc` means full range. Missing or unknown range does not establish limited range.

The default `--h264-range-policy report` flags H.264 signalled as full range (`color_range=pc` or a `yuvj` pixel format) in `compatibility_findings` as a warning; it does not fail solely for that metadata. For a delivery target whose compatibility requirements exclude full-range H.264, select `--h264-range-policy reject-full-range` to make that finding a violation. Neither policy establishes that colors look wrong or certifies a playback target: review the encode on the intended target and keep the finding in delivery evidence. Unknown range is still unknown, and other codecs are outside this specific policy. FFmpeg documents the range and full-scale pixel-format meanings in its [pixel format definitions](https://ffmpeg.org/doxygen/trunk/pixfmt_8h.html); rejection is a caller-selected delivery policy, not a universal H.264 restriction.

Technical success does not establish meaningful audible content, listening quality, or perceptual synchronization. A decodable track of digital silence can pass `require`. Check loudness and peaks, then watch and listen to the delivered encode at normal playback speed using the review coverage established in the main workflow.

For reproducibility checks, compare decoded picture and audio separately from container hashes. Container metadata can differ while media stays identical. Preserve differing renders and locate the changed stage before claiming a repeatable result. Use [media repair](media.md) for a demonstrated conversion or playback problem.

Review clarity and rhythm against the brief. A trailer's review should cover anticipation, readable action, appeal, and the finish; a product walkthrough should make the action and its result easy to follow. Keep remaining review gaps in the delivery evidence.

For an edit-only delivery, use `production.mode: edit_only` and `capture: null` in [evidence.json](evidence.md). Reference source take records as `source_capture`; keep the original driver clock separate from encoded source/output timelines. Save the edit settings and any known cut map without claiming a new take or inventing unknown alignment.
