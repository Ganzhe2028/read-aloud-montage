#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ -x /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 ]]; then
  PYTHON=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13
elif [[ -x /usr/local/bin/python3.13 ]]; then
  PYTHON=/usr/local/bin/python3.13
elif command -v python3.13 >/dev/null 2>&1; then
  PYTHON=$(command -v python3.13)
else
  echo '请先从说明页安装 Python 3.13，再双击本文件。'
  read '?按回车关闭窗口。'
  exit 1
fi
echo '正在准备朗读合辑工具，第一次可能需要几分钟……'
if ! "$PYTHON" -m venv .venv; then
  echo '准备没有完成，请拍下上面的报错。'
  read '?按回车关闭窗口。'
  exit 1
fi
if .venv/bin/python -m pip --isolated install --timeout 120 --retries 5 -r requirements.txt; then
  echo '安装完成。以后双击“制作视频-Mac.command”即可。'
else
  echo '安装没有完成，请拍下上面的报错。'
  read '?按回车关闭窗口。'
  exit 1
fi
read '?按回车关闭窗口。'
