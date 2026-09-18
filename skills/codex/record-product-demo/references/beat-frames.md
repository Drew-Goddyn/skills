# Frames from the delivered encode

Use `evidence.json` to extract review material from the actual reel. This needs
Python, Pillow >= 10.1 (its bundled scalable font), and `ffmpeg` and `ffprobe`
on PATH. There is no browser, model call, tool installer, or system-font lookup.

```sh
python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json
python3 <skill>/scripts/beat_frames.py <delivery>/evidence.json <delivery>/frames-review
```

The output directory must be new. The default is both beat frames and whole-reel
samples every two seconds. Use `--mode beats` or `--mode intervals` to restrict
the output, or `--interval 0.5` for denser interval sampling. Keep the index,
contact sheets and original-resolution PNGs together. Include them in the review
package with the reel and evidence; keep assessment separate.

## Selection and clocks

For each beat with a `video_time`, request the midpoint of its `[start, end]`
range; a point requests that exact time. Select the decoded frame whose
presentation interval contains the request: `[frame PTS, next frame PTS)`.
The final interval ends at its decoded timestamp plus its decoded duration.
This handles variable frame spacing without guessing from nominal frame rate.
All range endpoints must lie within the picture span. The picture end itself
is exclusive for a point request. Targets outside that span are **missing**,
never clamped to the first or last frame. No timestamp tolerance is added;
decimal inputs are used as written.

Video seconds start at the first decoded presentation timestamp. The index also
keeps that origin, integer PTS and time base so raw timestamps can be recovered.
These are encoded-video clocks, not driver clocks. For edits, supply final-output
`video_time` ranges in the evidence; the tool does not transform source times
using the edit map or take events. Existing source/output maps and takes remain
unchanged. A `null` video time stays **unresolved**, even when a driver timestamp
exists. The index retains the supplied precision, alignment and timing basis;
an exact extracted-frame timestamp does not upgrade approximate beat timing.

Interval requests are `0, spacing, 2*spacing, ...` strictly before the picture
end. There is no forced last-frame sample. Coverage lists every requested time,
the last sample and picture end, and the number of decoded frames not extracted.
Brief appearances between samples can be missed. Sampling is review material,
not a completed watch or privacy clearance.

## Output and failures

`frames.index.json` version 1 records:

- Source evidence/reel hashes, decoded picture span, timestamp origin, and
  selection rules.
- Each beat ID/label or interval ID, requested range and midpoint, status and
  reason, and a frame reference or `null`. Extracted-frame metadata includes
  relative PNG path, native dimensions, hash, decode index, integer PTS/time
  base, raw timestamp and normalized video seconds.
- Timestamped sheets with labels and references to their cells. Missing and
  unresolved entries remain visible as placeholders. Full-resolution frames
  remain separate; sheets only resize thumbnails and add captions.
- Sampling coverage, errors and explicit review limitations. `complete` means
  every requested sample was extracted, not that the reel was fully inspected.

Frames are decoded and selected without input seeking. The extractor verifies
each emitted FFmpeg timestamp against the probed timestamp before assigning any
frame paths. It records an error if decoding fails, frames/timestamps go missing,
timestamps are ambiguous, or the final frame duration is unknown. It does not
invent a frame rate or endpoint. Probe JSON and diagnostic stderr are retained.

Exit 0 means all requested samples were extracted; exit 1 means some beats are
missing or unresolved; exit 2 means invalid input or an extraction error. An
error index is retained when the output directory could be created. Existing
output paths are refused without overwriting them. Missing media tools explain
the PATH prerequisite; unavailable Pillow reports the missing dependency.

The extractor validates the fields it consumes plus reel identity. It does not
replace the full evidence validator, which also checks take/report references
and may reject out-of-range records. Extraction can still produce a diagnostic
index for such targets. It never rewrites evidence, takes, edit maps, checker
warnings or reviewer attribution. Whether the selected image shows a decisive
action, whether someone watched, and whether the reel is private remain separate
review judgments. Driver/video alignment and calibration are outside this tool.

Run `python3 <skill>/scripts/test_beat_frames.py -v` for browser-free synthetic
tests. The fixtures contain numbered frames with known RGB pixels; tests check
the extracted content as well as timing, missing results and sheet placement.
