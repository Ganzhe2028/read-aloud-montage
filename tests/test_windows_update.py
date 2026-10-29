"""Check update, backup, rollback and preservation using artificial files."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("windows_update_test", ROOT / "tools/windows_update/update.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class WindowsUpdate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.target = self.folder / "旧工具 中文 [一期]"
        self.payload = self.folder / "payload"
        self.target.mkdir()
        self.payload.mkdir()
        self.original = {}
        manifest = {"files": {}}
        for index, name in enumerate(updater.FILES):
            old = f"# old {index}\n".encode()
            new = f"# new {index}\n".encode()
            self.original[name] = old
            (self.target / name).write_bytes(old)
            (self.payload / name).write_bytes(new)
            manifest["files"][name] = hashlib.sha256(new).hexdigest()
        (self.target / "制作视频-Windows.bat").write_bytes(b"original launcher")
        for name in ("待处理音频/artificial.wav", "成片/previous.mp4", ".venv/keep.txt"):
            path = self.target / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"preserve this")
        (self.payload / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_updates_only_two_files_and_backs_up_originals(self):
        backup = updater.apply_update(self.target, self.payload)
        for name in updater.FILES:
            self.assertEqual((self.target / name).read_bytes(), (self.payload / name).read_bytes())
            self.assertEqual((backup / name).read_bytes(), self.original[name])
        for name in ("待处理音频/artificial.wav", "成片/previous.mp4", ".venv/keep.txt"):
            self.assertEqual((self.target / name).read_bytes(), b"preserve this")
        self.assertEqual((self.target / "制作视频-Windows.bat").read_bytes(), b"original launcher")

    def test_corrupt_payload_changes_nothing(self):
        (self.payload / "selection.py").write_text("# corrupted")
        with self.assertRaisesRegex(ValueError, "校验未通过"):
            updater.apply_update(self.target, self.payload)
        self.assertFalse((self.target / "更新备份").exists())
        for name in updater.FILES:
            self.assertEqual((self.target / name).read_bytes(), self.original[name])

    def test_second_file_failure_restores_first_file(self):
        real_replace = updater.os.replace
        failed = False

        def replace(source, destination):
            nonlocal failed
            if Path(destination).name == "selection.py" and not failed:
                failed = True
                raise PermissionError("artificial locked file")
            return real_replace(source, destination)

        with patch.object(updater.os, "replace", side_effect=replace):
            with self.assertRaisesRegex(RuntimeError, "已保留原版"):
                updater.apply_update(self.target, self.payload)
        for name in updater.FILES:
            self.assertEqual((self.target / name).read_bytes(), self.original[name])

    def test_wrong_folder_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "不是原来的工具"):
            updater.apply_update(self.folder, self.payload)


if __name__ == "__main__":
    unittest.main()
