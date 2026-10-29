"""Duration and checklist regressions, using artificial detector results."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from selection import allocate_excerpt_lengths

ROOT = Path(__file__).resolve().parents[1]


class DurationAllocation(unittest.TestCase):
    def test_short_montage_and_empty_input_stay_unchanged(self):
        self.assertEqual(allocate_excerpt_lengths([4, 17, 21], 239), [4, 17, 21])
        self.assertEqual(allocate_excerpt_lengths([], 239), [])
        self.assertEqual(allocate_excerpt_lengths([20, 20], 40), [20, 20])

    def test_short_clips_keep_their_time_and_long_clips_share_the_rest(self):
        lengths = allocate_excerpt_lengths([21] * 15 + [3, 5], 239)
        self.assertEqual(lengths[-2:], [3, 5])
        self.assertEqual(lengths[:15], [15.4] * 15)
        self.assertAlmostEqual(sum(lengths), 239)

    def test_rounding_never_exceeds_budget(self):
        for count in (12, 13, 20, 100, 200):
            with self.subTest(count=count):
                lengths = allocate_excerpt_lengths([21] * count, 239)
                self.assertEqual(len(lengths), count)
                self.assertLessEqual(sum(lengths), 239 + 1e-9)
                self.assertGreater(min(lengths), 0)


class BuildDuration(unittest.TestCase):
    def test_all_valid_files_and_actual_excerpts_are_in_checklist(self):
        spec = importlib.util.spec_from_file_location("duration_build_test", ROOT / "制作合辑.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            inputs = folder / "input"
            inputs.mkdir()
            (folder / ".work").mkdir()
            results = []
            for index in range(17):
                source = inputs / f"artificial-{index:02d}.wav"
                source.write_bytes(f"artificial {index}".encode())
                # Include a short reading after a long silent opening.
                speech = [(10, 13)] if index == 16 else [(0, 21)]
                results.append({"path": str(source), "speech": speech, "duration": 21})
            for label, extra in (
                ("broken", {"error": "artificial failure"}),
                ("silent", {"speech": [], "duration": 30}),
            ):
                source = inputs / f"{label}.wav"
                source.write_bytes(label.encode())
                results.append({"path": str(source), **extra})
            (inputs / "duplicate.wav").write_bytes((inputs / "artificial-00.wav").read_bytes())
            results.sort(key=lambda item: Path(item["path"]).name.casefold())
            extracted = []

            def extract(executable, source, excerpt, destination):
                extracted.append((source.name, excerpt))
                destination.write_bytes(b"artificial extracted clip")

            def render(executable, background, excerpts, destination, temp):
                self.assertEqual(len(excerpts), 17)
                self.assertLessEqual(sum(e.end - e.start for _, e in extracted), 239)
                destination.write_bytes(b"artificial assembled video")

            detected = subprocess.CompletedProcess([], 0, json.dumps(results), "")
            with (
                patch.object(module, "ROOT", folder),
                patch.object(module, "ffmpeg_path", return_value="unused"),
                patch.object(module.subprocess, "run", return_value=detected),
                patch.object(module, "make_background", return_value=True),
                patch.object(module, "extract_audio", side_effect=extract),
                patch.object(module, "render_video", side_effect=render),
            ):
                _, report, included, skipped = module.build(inputs, folder / "output")
            self.assertEqual((included, skipped), (17, 3))
            content = report.read_text(encoding="utf-8")
            self.assertEqual(content.count("已缩短选段"), 16)
            for filename, excerpt in extracted:
                self.assertIn(filename, content)
                self.assertIn(f"{excerpt.start:.1f}–{excerpt.end:.1f} 秒", content)
                self.assertGreater(excerpt.speech_seconds, 0)
            self.assertAlmostEqual(extracted[-1][1].end - extracted[-1][1].start, 3.3)


if __name__ == "__main__":
    unittest.main()
