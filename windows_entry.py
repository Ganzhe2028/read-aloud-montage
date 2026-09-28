"""Windows 双击入口：由“制作视频-Windows.bat”调用，转发到“制作合辑.py”。

.bat 里放中文会触发 Windows 命令行的解析问题，所以提示信息都放在这里。
每次运行会把窗口里的文字同步写进“运行日志.log”；出问题时，把这个文件
发给会处理的人，就能看清当时发生了什么。
"""

from __future__ import annotations

import io
import os
import platform
import runpy
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "制作合辑.py"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
LOG = ROOT / "运行日志.log"


class Tee(io.TextIOBase):
    """把输出同时送到窗口和日志文件；日志写失败不影响制作本身。"""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, text):
        for stream in self._streams:
            try:
                stream.write(text)
                stream.flush()
            except Exception:
                pass
        return len(text)

    def flush(self):
        for stream in self._streams:
            try:
                stream.flush()
            except Exception:
                pass


def main() -> int:
    try:
        log = LOG.open("w", encoding="utf-8")
    except OSError:
        log = None
    if log is not None:
        sys.stdout = Tee(sys.stdout, log)
        sys.stderr = Tee(sys.stderr, log)

    print(f"运行时间：{datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"程序位置：{ROOT}")
    print(f"系统版本：{platform.version()} · Python {sys.version.split()[0]}")
    print("-" * 40)

    if not VENV_PYTHON.is_file():
        print("还没有完成首次安装：请先双击“首次安装-Windows.bat”，看到“安装完成”后再回来。")
        return 1

    print("正在识别人声并制作视频，请稍等……")
    sys.argv = [str(SCRIPT)]
    try:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code in (None, "") else 1)
    except Exception:
        traceback.print_exc()
        code = 1
    else:
        code = 0

    print("-" * 40)
    print(f"结束时间：{datetime.now():%Y-%m-%d %H:%M:%S} · 退出码：{code}")
    if code == 0:
        try:
            os.startfile(str(ROOT / "成片"))
        except OSError:
            pass
    else:
        print(f"本次没有完成。如需帮助，请把这个文件夹里的“{LOG.name}”一起发出来。")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
