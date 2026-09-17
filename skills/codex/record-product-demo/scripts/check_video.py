#!/usr/bin/env python3
"""Print a quick JSON health check for a demo video."""

from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a demo video and print JSON facts.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--expected-fps", type=float)
    parser.add_argument("--expected-size", type=size, metavar="WIDTHxHEIGHT")
    parser.add_argument("--max-duration", type=float)
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--allow-audio", action="store_true")
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        parser.error(f"Video is not a file: {video}")

    probe = run([
        tool("ffprobe"), "-v", "error", "-count_frames", "-show_streams",
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
    frame_count = int(primary.get("nb_read_frames", 0) or 0)
    width = int(primary.get("width", 0) or 0)
    height = int(primary.get("height", 0) or 0)

    violations: list[str] = []
    if len(videos) != 1:
        violations.append(f"expected one video stream, found {len(videos)}")
    if audios and not args.allow_audio:
        violations.append(f"unexpected audio streams: {len(audios)}")
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
    if fps and duration and abs(frame_count - fps * duration) > 2:
        violations.append("frame count does not match duration and frame rate")

    decode = run([
        tool("ffmpeg"), "-v", "error", "-i", str(video),
        "-map", "0:v:0", "-f", "null", "-",
    ])
    if decode.returncode or decode.stderr.strip():
        violations.append(f"decode failed: {decode.stderr.strip() or decode.returncode}")

    report = {
        "status": "pass" if not violations else "fail",
        "video": str(video),
        "duration_seconds": duration,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "codec": primary.get("codec_name"),
        "fps": fps,
        "file_size_bytes": file_bytes,
        "audio_streams": len(audios),
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
