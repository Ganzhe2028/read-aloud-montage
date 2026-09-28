@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto run
set "PY=python"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 goto run
echo A working Python 3.11 or newer was not found on this computer.
echo Please open the guide html file in this folder and finish the setup first.
pause
exit /b 1

:run
"%PY%" windows_entry.py
if errorlevel 1 goto failed
pause
exit /b 0

:failed
echo The build did not finish. Please take a photo of the Chinese messages above
echo and send it for help. Do not share an older video as this round's result.
pause
exit /b 1
