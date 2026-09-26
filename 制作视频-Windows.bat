@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先双击“首次安装-Windows.bat”。
  pause
  exit /b 1
)
echo 正在识别人声并制作视频，请稍等……
.venv\Scripts\python.exe 制作合辑.py
if errorlevel 1 (
  echo 制作没有完成，请拍下上面的报错；不要分享旧视频。
  pause
  exit /b 1
)
start "" "%CD%\成片"
pause
