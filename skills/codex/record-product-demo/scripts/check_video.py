#!/usr/bin/env python3
"""Check demo media decoding, timing, audio policy, and delivery compatibility."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


def tool(name: str) -> str:
    found = shutil.which(name) or str(Path("/opt/homebrew/bin") / name)
    if not Path(found).is_file():
        raise RuntimeError(f"Required command not found: {name}")
    return found


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def size(value: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x", 1))
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected WIDTHxHEIGHT") from error
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Dimensions must be positive")
    return width, height


def minimum_duration(value: str) -> Fraction:
    try:
        duration = Fraction(value)
        if duration < 0 or not math.isfinite(float(duration)):
            raise ValueError
        return duration
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise argparse.ArgumentTypeError("Minimum duration must be finite, nonnegative seconds") from error


def color_metadata(stream: dict) -> dict:
    """Keep raw probe values; an absent range does not establish limited range."""
    pixel_format = stream.get("pix_fmt")
    color_range = stream.get("color_range")
    return {
        "pixel_format": pixel_format,
        "pixel_format_status": ("missing" if pixel_format is None else
                                "unknown" if pixel_format in {"", "unknown", "unspecified", "none", "N/A"} else "known"),
        "color_range": color_range,
        "color_range_status": ("missing" if color_range is None else
                               "known" if color_range in {"tv", "pc"} else "unknown"),
    }


def decode_stream(video: Path, stream: dict) -> tuple[list[dict], dict]:
    """Require decoded frames as well as a clean full decode of this stream."""
    index = stream["index"]
    probe = run([
        tool("ffprobe"), "-v", "error", "-err_detect", "explode",
        "-select_streams", str(index), "-show_frames", "-show_entries",
        "frame=pts,best_effort_timestamp,duration,pkt_duration,nb_samples",
        "-of", "json", str(video),
    ])
    frames = json.loads(probe.stdout or "{}").get("frames", [])
    decode = run([
        tool("ffmpeg"), "-v", "error", "-xerror", "-err_detect", "explode",
        "-i", str(video), "-map", f"0:{index}", "-f", "null", "-",
    ])
    errors = []
    for label, result in (("frame probe", probe), ("decode", decode)):
        if result.returncode or result.stderr.strip():
            errors.append(f"{label}: {result.stderr.strip() or result.returncode}")
    if not frames:
        errors.append("no decoded frames")
    if stream["codec_type"] == "audio" and not sum(int(f.get("nb_samples", 0)) for f in frames):
        errors.append("no decoded audio samples")
    return frames, {"status": "fail" if errors else "pass", "errors": errors}


def presentation_timing(stream: dict, frames: list[dict]) -> tuple[Fraction, Fraction, dict]:
    """Use decoded presentation timestamps, with signalled audio tail trimming.

    FFmpeg applies codec skip/discard samples while decoding. AAC can still
    produce a full final block whose frame duration signals a shorter playable
    tail. Use that duration, not a codec-sized grace period or container length.
    """
    if not frames:
        raise ValueError("no decoded frames for timing")
    time_base = Fraction(stream["time_base"])
    audio = stream["codec_type"] == "audio"
    sample_rate = int(stream.get("sample_rate", 0))
    stamped = []
    for frame in frames:
        pts = frame.get("pts", frame.get("best_effort_timestamp"))
        if pts is None:
            raise ValueError("decoded frame has no presentation timestamp")
        duration = int(frame.get("duration", frame.get("pkt_duration", 0))) * time_base
        if audio:
            samples = int(frame.get("nb_samples", 0))
            if samples <= 0 or sample_rate <= 0:
                raise ValueError("decoded audio frame has no positive sample count/rate")
            span = Fraction(samples, sample_rate)
        else:
            span = duration
            if span <= 0:
                fps = Fraction(stream.get("avg_frame_rate", "0"))
                if fps <= 0:
                    raise ValueError("decoded picture frame has no duration or positive frame rate")
                span = 1 / fps
        stamped.append((int(pts) * time_base, span, duration))
    start = min(pts for pts, _, _ in stamped)
    decoded_end = max(pts + span for pts, span, _ in stamped)
    last_index = max(range(len(stamped)), key=lambda i: stamped[i][0])
    pts, span, duration = stamped[last_index]
    tail_trim = Fraction(0)
    if audio and 0 < duration < span:
        tail_trim = span - duration
        stamped[last_index] = (pts, duration, duration)
    end = max(pts + span for pts, span, _ in stamped)
    if end <= start:
        raise ValueError("decoded presentation interval is empty")
    report = {
        "start_seconds": float(start),
        "end_seconds": float(end),
        "duration_seconds": float(end - start),
        "decoded_frame_count": len(frames),
    }
    if audio:
        report.update(
            sample_rate=sample_rate,
            decoded_sample_count=sum(int(f["nb_samples"]) for f in frames),
            decoded_end_seconds=float(decoded_end),
            signalled_tail_trim_seconds=float(tail_trim),
        )
    return start, end, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a demo video and print JSON facts.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--expected-fps", type=float)
    parser.add_argument("--expected-size", type=size, metavar="WIDTHxHEIGHT")
    parser.add_argument("--min-duration", type=minimum_duration, metavar="SECONDS",
                        help="Minimum decoded picture presentation span; equality passes (default: no minimum)")
    parser.add_argument("--max-duration", type=float)
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--h264-range-policy", choices=("report", "reject-full-range"), default="report",
                        help="Report (default) or reject signalled full-range H.264 for delivery compatibility, not visual diagnosis")
    audio_policy = parser.add_mutually_exclusive_group()
    audio_policy.add_argument("--audio-policy", choices=("forbid", "allow", "require"),
                              help="Forbid (default), allow, or require decodable audio")
    audio_policy.add_argument("--allow-audio", dest="audio_policy", action="store_const", const="allow",
                              help="Compatibility alias for --audio-policy allow")
    parser.set_defaults(audio_policy="forbid")
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        parser.error(f"Video is not a file: {video}")

    probe = run([
        tool("ffprobe"), "-v", "error", "-show_streams",
        "-show_format", "-of", "json", str(video),
    ])
    if probe.returncode:
        raise RuntimeError(probe.stderr.strip() or "ffprobe failed")

    payload = json.loads(probe.stdout)
    streams = payload.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    primary = videos[0] if videos else {}
    file_bytes = video.stat().st_size
    fps = rate(primary.get("avg_frame_rate"))
    duration = float(payload.get("format", {}).get("duration", 0) or 0)
    frame_count = 0
    width = int(primary.get("width", 0) or 0)
    height = int(primary.get("height", 0) or 0)
    color = color_metadata(primary)

    violations: list[str] = []
    compatibility_findings = []
    full_range_basis = []
    if color["color_range"] == "pc":
        full_range_basis.append("color_range=pc")
    if (color["pixel_format"] or "").startswith("yuvj"):
        full_range_basis.append(f"pixel_format={color['pixel_format']}")
    if primary.get("codec_name") == "h264" and full_range_basis:
        message = "full-range H.264 flagged by delivery compatibility policy; not an observed color defect"
        compatibility_findings.append({"code": "full_range_h264", "basis": full_range_basis,
                                       "severity": "error" if args.h264_range_policy == "reject-full-range" else "warning",
                                       "message": message})
        if args.h264_range_policy == "reject-full-range":
            violations.append(message + "; selected policy: reject-full-range")
    if len(videos) != 1:
        violations.append(f"expected one video stream, found {len(videos)}")
    if audios and args.audio_policy == "forbid":
        violations.append(f"unexpected audio streams: {len(audios)}")
    if not audios and args.audio_policy == "require":
        violations.append("required audio is missing")

    picture = None
    audio_reports = []
    windows = {}
    for stream in ([primary] if videos else []) + audios:
        frames, decoded = decode_stream(video, stream)
        label = "picture" if stream["codec_type"] == "video" else "audio"
        if label == "picture":
            frame_count = len(frames)
        entry = {"stream_index": stream["index"], "codec": stream.get("codec_name"), "decode": decoded}
        if decoded["status"] != "pass":
            violations.append(f"{label} stream {stream['index']} decode failed: {'; '.join(decoded['errors'])}")
        try:
            start, end, timing = presentation_timing(stream, frames)
            entry.update(timing)
            windows[stream["index"]] = (start, end)
        except (KeyError, ValueError, ZeroDivisionError) as error:
            violations.append(f"{label} stream {stream['index']} timing unavailable: {error}")
        if label == "picture":
            picture = entry
        else:
            audio_reports.append(entry)

    if duration <= 0 or frame_count <= 0:
        violations.append("duration or frame count is missing")
    if args.expected_fps is not None and (fps is None or abs(fps - args.expected_fps) > 0.01):
        violations.append(f"expected {args.expected_fps:g} fps, found {fps}")
    if args.expected_size and (width, height) != args.expected_size:
        violations.append(f"expected {args.expected_size[0]}x{args.expected_size[1]}, found {width}x{height}")
    if args.max_duration is not None and duration > args.max_duration:
        violations.append(f"duration {duration:g}s exceeds {args.max_duration:g}s")
    if args.max_bytes is not None and file_bytes > args.max_bytes:
        violations.append(f"file size {file_bytes} exceeds {args.max_bytes}")
    picture_window = windows.get(primary.get("index"))
    if args.min_duration is not None:
        if picture_window is None:
            violations.append("minimum duration needs decoded picture presentation timing")
        elif picture_window[1] - picture_window[0] < args.min_duration:
            violations.append(
                f"picture duration {float(picture_window[1] - picture_window[0]):.9g}s "
                f"is below minimum {float(args.min_duration):.9g}s"
            )
    if fps and picture_window and abs(frame_count - fps * (picture_window[1] - picture_window[0])) > 2:
        violations.append("frame count does not match picture duration and frame rate")
    tolerance = 1 / Fraction(primary["avg_frame_rate"]) if fps and fps > 0 else None
    for entry in audio_reports:
        audio_window = windows.get(entry["stream_index"])
        if entry["decode"]["status"] != "pass" or not audio_window or not picture_window:
            continue
        if tolerance is None:
            violations.append("audio/picture timing needs a positive video frame rate for the one-frame tolerance")
            continue
        a_start, a_end = audio_window
        v_start, v_end = picture_window
        offsets = (a_start - v_start, a_end - v_end, (a_end - a_start) - (v_end - v_start))
        entry["picture_offsets_seconds"] = dict(zip(("start", "end", "duration"), map(float, offsets)))
        if any(abs(offset) > tolerance for offset in offsets):
            violations.append(
                f"audio/picture timing mismatch for audio stream {entry['stream_index']}: "
                f"start {float(offsets[0]):+.9g}s, end {float(offsets[1]):+.9g}s, "
                f"duration {float(offsets[2]):+.9g}s; tolerance {float(tolerance):.9g}s (one video frame)"
            )

    report = {
        "status": "pass" if not violations else "fail",
        "video": str(video),
        "duration_seconds": duration,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "codec": primary.get("codec_name"),
        **color,
        "full_range_h264_policy": args.h264_range_policy,
        "compatibility_findings": compatibility_findings,
        "min_duration_seconds": float(args.min_duration) if args.min_duration is not None else None,
        "min_duration_basis": "picture_presentation_span",
        "fps": fps,
        "file_size_bytes": file_bytes,
        "audio_streams": len(audios),
        "audio_policy": args.audio_policy,
        "audio_decode_status": ("not_present" if not audios else
                                "pass" if all(a["decode"]["status"] == "pass" for a in audio_reports) else "fail"),
        "picture": picture,
        "audio": audio_reports,
        "audio_picture_tolerance_seconds": float(tolerance) if tolerance is not None else None,
        "violations": violations,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not violations else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}, indent=2), file=sys.stderr)
        raise SystemExit(2)
