#!/bin/zsh
set -e
cd "${0:A:h}"

# 依次寻找可用的 Python（3.11 或更新版本即可）
PYTHON=""
for candidate in \
  /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 \
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 \
  /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
  /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
  /usr/local/bin/python3.14 \
  /usr/local/bin/python3.13 \
  /usr/local/bin/python3.12 \
  /usr/local/bin/python3.11 \
  python3.14 python3.13 python3.12 python3.11 python3; do
  if [[ "$candidate" == */* ]]; then
    [[ -x "$candidate" ]] || continue
    cmd="$candidate"
  else
    command -v "$candidate" >/dev/null 2>&1 || continue
    cmd=$(command -v "$candidate")
  fi
  if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PYTHON="$cmd"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo '没有找到 Python 3.11 或更新版本。'
  echo '请先按“使用说明”安装 Python，再双击本文件。'
  read '?按回车关闭窗口。'
  exit 1
fi

echo "使用 $($PYTHON -c 'import sys; print("Python", sys.version.split()[0])') 准备朗读合辑工具，第一次可能需要几分钟……"
if ! "$PYTHON" -m venv .venv; then
  echo '准备没有完成，请拍下上面的报错。'
  read '?按回车关闭窗口。'
  exit 1
fi

# 优先走国内镜像，下不动再回退官方源
if .venv/bin/python -m pip --isolated install --timeout 120 --retries 5 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt; then
  echo '安装完成。以后双击“制作视频-Mac.command”即可。'
else
  echo '镜像下载不顺利，改用官方源重试……'
  if .venv/bin/python -m pip --isolated install --timeout 120 --retries 5 -r requirements.txt; then
    echo '安装完成。以后双击“制作视频-Mac.command”即可。'
  else
    echo '安装没有完成，请拍下上面的报错。'
    read '?按回车关闭窗口。'
    exit 1
  fi
fi
read '?按回车关闭窗口。'
