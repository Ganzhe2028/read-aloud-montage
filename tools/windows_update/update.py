"""Update an existing installation; preserve its environment, audio and output."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

FILES = ("制作合辑.py", "selection.py")


def apply_update(target: Path, payload: Path) -> Path:
    target = target.resolve()
    for name in (*FILES, "制作视频-Windows.bat"):
        if not (target / name).is_file():
            raise ValueError("选到的不是原来的工具文件夹，请重新选择原来的‘制作视频-Windows.bat’。")
    manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
    if set(manifest["files"]) != set(FILES):
        raise ValueError("更新包文件清单不完整，请重新解压更新包。")
    contents = {}
    for name in FILES:
        data = (payload / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
            raise ValueError(f"更新文件校验未通过：{name}。请重新下载、解压更新包。")
        compile(data, name, "exec")
        contents[name] = data

    # Complete backups before changing either installed file.
    backup = target / "更新备份" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    backup.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(target / name, backup / name)
    replaced = []
    with tempfile.TemporaryDirectory(prefix=".update-", dir=target) as temp_name:
        temp = Path(temp_name)
        for name, data in contents.items():
            (temp / name).write_bytes(data)
        try:
            for name in FILES:
                os.replace(temp / name, target / name)
                replaced.append(name)
            for name, data in contents.items():
                if (target / name).read_bytes() != data:
                    raise OSError(f"更新后的文件核对失败：{name}")
        except Exception as error:
            rollback_errors = []
            for name in reversed(replaced):
                try:
                    shutil.copy2(backup / name, temp / name)
                    os.replace(temp / name, target / name)
                except OSError as rollback_error:
                    rollback_errors.append(f"{name}: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(f"更新未完成，请从‘{backup}’恢复旧文件：{'；'.join(rollback_errors)}") from error
            raise RuntimeError(f"更新未完成，已保留原版：{error}") from error
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        backup = apply_update(args.target_dir, Path(__file__).resolve().parent / "更新文件")
    except Exception as error:
        print(f"更新没有完成：{error}")
        print("请把这个窗口的报错拍照交给协助者。")
        return 1
    print("更新成功！以后照常双击原来的‘制作视频-Windows.bat’即可。")
    print("新制作的视频不超过 4 分钟；已有视频需要重新制作才会变短。")
    print("原音频、成片和已安装的运行环境都保留了。")
    print(f"旧程序已备份到：{backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
