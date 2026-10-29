"""Build a small, offline update ZIP for already-installed Windows copies."""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = "朗读合辑-4分钟更新包/"
    files = {}
    manifest = {"files": {}}
    for name in ("制作合辑.py", "selection.py"):
        data = (ROOT / name).read_bytes()
        compile(data, name, "exec")
        files["更新文件/" + name] = data
        manifest["files"][name] = hashlib.sha256(data).hexdigest()
    files["更新文件/manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    files["update.py"] = (ROOT / "tools/windows_update/update.py").read_bytes()
    files["update.ps1"] = (ROOT / "tools/windows_update/update.ps1").read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8-sig")
    files["双击更新.bat"] = (
        '@echo off\r\nchcp 65001 >nul\r\ncd /d "%~dp0"\r\n'
        '"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" '
        '-NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0update.ps1"\r\n'
        'set "UPDATE_EXIT=%errorlevel%"\r\npause\r\nexit /b %UPDATE_EXIT%\r\n'
    ).encode("ascii")
    files["先看这里.txt"] = (
        "这是给已经装好朗读合辑的人用的小更新包，不用重新安装。\r\n\r\n"
        "1. 微信下载 ZIP 后，右键选‘全部解压’。\r\n"
        "2. 先关闭正在制作视频的窗口，再双击解压出来的‘双击更新.bat’。\r\n"
        "3. 在弹出的选择窗口里，找到以前那套工具，选中‘制作视频-Windows.bat’，点‘打开’。\r\n"
        "4. 看到‘更新成功’就好了。以后仍然双击原来的制作入口。\r\n\r\n"
        "新做的视频不超过 4 分钟；投稿多时自动缩短选段，尽量都收录。\r\n"
        "已有的视频不会自动变短，需要重新制作。\r\n"
        "音频、成片和已安装环境都保留；旧程序会自动存进原文件夹的‘更新备份’。\r\n"
        "不用联网，不用输入命令，不用运行首次安装。请保留更新包里的全部文件。\r\n"
        "更新失败时，把窗口报错拍照交给协助者，不要分享旧视频冒充新结果。\r\n\r\n"
        "验证情况：更新、备份和失败恢复测试已通过；已收到 Windows 实机更新成功反馈。\r\n"
    ).encode("utf-8-sig")
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    with tempfile.TemporaryDirectory(prefix="update-zip-", dir=output.parent) as name:
        archive_path = Path(name) / output.name
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename, data in files.items():
                archive.writestr(prefix + filename, data)
        with zipfile.ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity check failed")
        archive_path.replace(output)
    print(json.dumps({"file": str(output), "bytes": output.stat().st_size,
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
