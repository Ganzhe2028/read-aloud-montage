@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在准备朗读合辑工具，第一次可能需要几分钟……

rem 依次寻找可用的 Python（3.11 或更新版本即可）
set "PYCMD="
where py >nul 2>nul
if %errorlevel%==0 (
  for %%V in (3.14 3.13 3.12 3.11) do (
    if not defined PYCMD (
      py -%%V -c "import sys" >nul 2>nul && set "PYCMD=py -%%V"
    )
  )
)
if not defined PYCMD (
  python -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul && set "PYCMD=python"
)
if not defined PYCMD (
  echo 没有找到 Python 3.11 或更新版本。
  echo 请先按“使用说明”安装 Python，再双击本文件。
  pause
  exit /b 1
)

%PYCMD% -m venv .venv
if errorlevel 1 goto failed

rem 优先走国内镜像，下不动再回退官方源
.venv\Scripts\python.exe -m pip --isolated install --timeout 120 --retries 5 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
if errorlevel 1 (
  echo 镜像下载不顺利，改用官方源重试……
  .venv\Scripts\python.exe -m pip --isolated install --timeout 120 --retries 5 -r requirements.txt
)
if errorlevel 1 goto failed

echo 安装完成。以后双击“制作视频-Windows.bat”即可。
pause
exit /b 0

:failed
echo 安装没有完成，请拍下上面的报错；如果提示找不到 Python，请先按“使用说明”安装 Python。
pause
exit /b 1
