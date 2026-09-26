@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在准备朗读合辑工具，第一次可能需要几分钟……
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.13 -m venv .venv
) else (
  python -m venv .venv
)
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip --isolated install --timeout 120 --retries 5 -r requirements.txt
if errorlevel 1 goto failed
echo 安装完成。以后双击“制作视频-Windows.bat”即可。
pause
exit /b 0
:failed
echo 安装没有完成，请拍下上面的报错；如果找不到 Python，请先按说明页安装 Python 3.13。
pause
exit /b 1
