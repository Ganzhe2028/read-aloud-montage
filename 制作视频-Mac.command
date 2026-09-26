#!/bin/zsh
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  echo '请先双击“首次安装-Mac.command”。'
  read '?按回车关闭窗口。'
  exit 1
fi
echo '正在识别人声并制作视频，请稍等……'
if .venv/bin/python 制作合辑.py; then
  open 成片
else
  echo '制作没有完成，请拍下上面的报错；不要分享旧视频。'
  read '?按回车关闭窗口。'
  exit 1
fi
read '?按回车关闭窗口。'
