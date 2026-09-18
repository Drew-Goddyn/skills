"""Browser-free audio-policy and timing regressions; requires FFmpeg/ffprobe."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_video import presentation_timing, tool


CHECKER = Path(__file__).with_name("check_video.py")


def make_media(directory: Path) -> None:
    """Tiny deterministic inputs; corrupt an audio packet, never the video."""
    video = ["-f", "lavfi", "-i", "testsrc2=size=160x90:rate=30:duration=2"]
    encode = ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]

    def create(name, args):
        subprocess.run([tool("ffmpeg"), "-v", "error", "-nostdin", "-n", *args, str(directory / name)],
                       capture_output=True, check=True)

    def tone(duration="2"):
        return ["-f", "lavfi", "-i", f"sine=frequency=880:sample_rate=48000:duration={duration}"]

    create("silent.mp4", video + encode)
    for name, duration in [("aligned.mp4", "2"), ("long-audio.mp4", "2.2"), ("short-audio.mp4", "1.8")]:
        create(name, video + tone(duration) + encode + ["-c:a", "aac"])
    create("padded-aac.mp4", ["-f", "lavfi", "-i", "testsrc2=size=160x90:rate=120:duration=2.033333333333"]
           + tone("2.033333333333") + encode + ["-c:a", "aac"])
    for name, v_offset, a_offset in [("delayed-audio.mkv", 0, 0.2), ("shared-start.mkv", 0.5, 0.5)]:
        graph = f"[0:v]setpts=PTS+{v_offset}/TB[v];[1:a]asetpts=PTS+{a_offset}/TB[a]"
        create(name, video + tone() + ["-filter_complex", graph, "-map", "[v]", "-map", "[a]"]
               + encode + ["-c:a", "pcm_s16le", "-avoid_negative_ts", "disabled"])
    for name, samples in [("one-frame-long.mov", 97600), ("over-one-frame.mov", 97601)]:
        create(name, video + tone("3") + ["-af", f"atrim=end_sample={samples}"] + encode + ["-c:a", "pcm_s16le"])
    create("digital-silence.mp4", video + ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "2"]
           + encode + ["-c:a", "aac"])
    packets = json.loads(subprocess.check_output([
        tool("ffprobe"), "-v", "error", "-select_streams", "a", "-show_packets", "-of", "json",
        str(directory / "aligned.mp4"),
    ]))["packets"]
    packet = packets[-3]
    data = bytearray((directory / "aligned.mp4").read_bytes())
    pos, length = int(packet["pos"]), int(packet["size"])
    data[pos:pos + length] = b"\xff" * length
    (directory / "broken-audio.mp4").write_bytes(data)
    create("broken-second-track.mp4", ["-i", str(directory / "aligned.mp4"), "-i", str(directory / "broken-audio.mp4"),
                                      "-map", "0:v", "-map", "0:a", "-map", "1:a", "-c", "copy"])


class MediaChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="check-video-audio-")
        cls.media = Path(cls.scratch.name)
        make_media(cls.media)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def check(self, name, *options):
        result = subprocess.run([sys.executable, str(CHECKER), str(self.media / name), *options],
                                text=True, capture_output=True)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0 if report["status"] == "pass" else 1)
        return report

    def test_silent_default_and_explicit_policy(self):
        for options in [(), ("--audio-policy", "forbid"), ("--audio-policy", "allow"), ("--allow-audio",)]:
            with self.subTest(options=options):
                result = self.check("silent.mp4", *options)
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["audio_decode_status"], "not_present")
        required = self.check("silent.mp4", "--audio-policy", "require")
        self.assertEqual(required["violations"], ["required audio is missing"])
        self.assertEqual(required["audio_decode_status"], "not_present")

    def test_present_audio_is_decoded_under_each_policy(self):
        for options in [("--audio-policy", "require"), ("--audio-policy", "allow"), ("--allow-audio",)]:
            with self.subTest(options=options):
                result = self.check("aligned.mp4", *options)
                self.assertEqual(result["status"], "pass", result)
                self.assertEqual(result["audio_decode_status"], "pass")
                self.assertGreater(result["audio"][0]["decoded_sample_count"], 0)
        forbidden = self.check("aligned.mp4")
        self.assertEqual(forbidden["violations"], ["unexpected audio streams: 1"])
        self.assertEqual(forbidden["audio_decode_status"], "pass")

    def test_timing_mismatch_is_not_a_picture_count_error(self):
        for name, delta in [("long-audio.mp4", 0.2), ("short-audio.mp4", -0.2)]:
            with self.subTest(name=name):
                result = self.check(name, "--audio-policy", "require")
                self.assertEqual(result["status"], "fail")
                self.assertEqual(len(result["violations"]), 1, result)
                self.assertIn("audio/picture timing mismatch", result["violations"][0])
                self.assertEqual(result["frame_count"], 60)
                self.assertEqual(result["picture"]["duration_seconds"], 2)
                self.assertAlmostEqual(result["audio"][0]["duration_seconds"], 2 + delta)

    def test_start_times_share_a_clock(self):
        shifted = self.check("shared-start.mkv", "--audio-policy", "require")
        self.assertEqual(shifted["status"], "pass", shifted)
        self.assertEqual(shifted["picture"]["start_seconds"], 0.5)
        self.assertEqual(shifted["audio"][0]["start_seconds"], 0.5)
        delayed = self.check("delayed-audio.mkv", "--audio-policy", "require")
        self.assertEqual(delayed["status"], "fail")
        self.assertEqual(delayed["picture"]["duration_seconds"], delayed["audio"][0]["duration_seconds"])
        self.assertIn("start +0.2s", delayed["violations"][0])

    def test_aac_padding_is_not_extra_soundtrack(self):
        result = self.check("padded-aac.mp4", "--audio-policy", "require")
        self.assertEqual(result["status"], "pass", result)
        audio = result["audio"][0]
        self.assertGreater(audio["decoded_end_seconds"] - audio["end_seconds"], 1 / 120)
        self.assertLessEqual(
            abs(audio["duration_seconds"] - result["picture"]["duration_seconds"]),
            1 / 120,
        )
        self.assertGreater(audio["signalled_tail_trim_seconds"], 0)

    def test_exact_one_frame_boundary(self):
        self.assertEqual(self.check("one-frame-long.mov", "--audio-policy", "require")["status"], "pass")
        too_long = self.check("over-one-frame.mov", "--audio-policy", "require")
        self.assertEqual(too_long["status"], "fail")
        self.assertIn("audio/picture timing mismatch", too_long["violations"][0])

    def test_broken_audio_and_every_track_are_checked(self):
        for name in ["broken-audio.mp4", "broken-second-track.mp4"]:
            for options in [(), ("--allow-audio",), ("--audio-policy", "require")]:
                with self.subTest(name=name, options=options):
                    result = self.check(name, *options)
                    self.assertEqual(result["status"], "fail")
                    self.assertEqual(result["audio_decode_status"], "fail")
                    self.assertEqual(result["picture"]["decode"]["status"], "pass")
                    self.assertEqual(result["audio"][-1]["decode"]["status"], "fail")
                    self.assertTrue(any("audio stream" in v and "decode failed" in v for v in result["violations"]))

    def test_decodable_digital_silence_is_not_an_audibility_test(self):
        self.assertEqual(self.check("digital-silence.mp4", "--audio-policy", "require")["status"], "pass")

    def test_existing_video_limits(self):
        for options, diagnostic in [
            (("--expected-size", "320x180"), "expected 320x180"),
            (("--expected-fps", "24"), "expected 24 fps"),
            (("--max-duration", "1"), "duration 2s exceeds 1s"),
            (("--max-bytes", "1"), "file size"),
        ]:
            with self.subTest(options=options):
                result = self.check("silent.mp4", *options)
                self.assertEqual(result["status"], "fail")
                self.assertTrue(any(diagnostic in v for v in result["violations"]))

    def test_empty_or_untimed_decode_cannot_supply_valid_timing(self):
        stream = {"codec_type": "audio", "time_base": "1/48000", "sample_rate": "48000"}
        for frames in [[], [{"nb_samples": 1024}], [{"pts": 0, "nb_samples": 0}]]:
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                presentation_timing(stream, frames)


if __name__ == "__main__":
    unittest.main()
