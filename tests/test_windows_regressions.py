"""Regression checks using fake failures, never real reading submissions."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class DetectorErrors(unittest.TestCase):
    def test_import_error_in_chinese_path_is_utf8_even_with_gbk_default(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name) / "中文路径"
            folder.mkdir()
            script = folder / "voice_detect.py"
            shutil.copyfile(ROOT / "voice_detect.py", script)
            env = {**os.environ, "PYTHONIOENCODING": "gbk", "PYTHONUTF8": "0"}
            # -S intentionally hides installed dependencies: fail before main().
            result = subprocess.run(
                [sys.executable, "-S", str(script)], input="[]",
                capture_output=True, encoding="utf-8", env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ModuleNotFoundError", result.stderr)
            self.assertIn("中文路径", result.stderr)

    def test_parent_retains_error_and_old_video_when_detector_fails(self):
        spec = importlib.util.spec_from_file_location("reading_test", ROOT / "制作合辑.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for raw_bytes in (False, True):
            with self.subTest(raw_bytes=raw_bytes), tempfile.TemporaryDirectory() as name:
                folder = Path(name)
                inputs, output = folder / "input", folder / "output"
                inputs.mkdir()
                output.mkdir()
                (inputs / "artificial.wav").write_bytes(b"artificial failure fixture")
                old_video = output / "previous.mp4"
                old_video.write_bytes(b"previous video sentinel")
                if raw_bytes:
                    body = "sys.stderr.buffer.write('模拟错误'.encode('gbk'))"
                else:
                    body = "print('模拟检测器启动失败', file=sys.stderr)"
                (folder / "voice_detect.py").write_text(
                    f"import sys\n{body}\nraise SystemExit(1)\n", encoding="utf-8",
                )
                env = {**os.environ, "PYTHONIOENCODING": "gbk", "PYTHONUTF8": "0"}
                with patch.object(module, "ROOT", folder), patch.object(module, "ffmpeg_path", return_value="unused"), patch.dict(os.environ, env, clear=True):
                    with self.assertRaisesRegex(RuntimeError, "本地人声检测无法启动") as error:
                        module.build(inputs, output)
                if not raw_bytes:
                    self.assertIn("模拟检测器启动失败", str(error.exception))
                self.assertEqual(old_video.read_bytes(), b"previous video sentinel")
                self.assertEqual(list(output.iterdir()), [old_video])


class WindowsLauncher(unittest.TestCase):
    def test_batch_remains_ascii(self):
        (ROOT / "制作视频-Windows.bat").read_bytes().decode("ascii")

    @unittest.skipUnless(sys.platform == "win32", "requires Windows cmd.exe")
    def test_alias_that_is_found_but_cannot_run_shows_install_guidance(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            binary = folder / "bin"
            binary.mkdir()
            # Mimic the Store alias: discoverable executable, nonzero on -c.
            source = "public class Alias { public static int Main(string[] args) { return 1; } }"
            env = {**os.environ, "ALIAS_SOURCE": source, "ALIAS_EXE": str(binary / "python.exe")}
            powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            subprocess.run(
                [str(powershell), "-NoProfile", "-Command", "$ErrorActionPreference='Stop'; Add-Type -TypeDefinition $env:ALIAS_SOURCE -OutputAssembly $env:ALIAS_EXE -OutputType ConsoleApplication"],
                env=env, check=True, capture_output=True, timeout=60,
            )
            launcher = folder / "launch.bat"
            shutil.copyfile(ROOT / "制作视频-Windows.bat", launcher)
            env["PATH"] = str(binary) + os.pathsep + env["PATH"]
            result = subprocess.run(
                [os.environ["COMSPEC"], "/d", "/c", "launch.bat"], cwd=folder,
                env=env, input="\n", capture_output=True, encoding="utf-8", errors="replace", timeout=30,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("finish the setup first", result.stdout)
            self.assertNotIn("The build did not finish", result.stdout)


if __name__ == "__main__":
    unittest.main()
