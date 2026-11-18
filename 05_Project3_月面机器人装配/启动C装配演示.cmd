@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先按仓库README创建Python 3.12虚拟环境并安装requirements.txt。
  pause
  exit /b 1
)
set PYTHONDONTWRITEBYTECODE=1
echo %* | findstr /I /C:"--output" >nul
if errorlevel 1 (
  for /f %%T in ('".venv\Scripts\python.exe" -c "import time; print(time.strftime('%%Y%%m%%d_%%H%%M%%S'))"') do set "P3_STAMP=%%T"
  ".venv\Scripts\python.exe" "C_仿真与装配\run_preloaded_tray_assembly_fast.py" --gui --output "..\runs\local\c_legacy_%P3_STAMP%" %*
) else (
  ".venv\Scripts\python.exe" "C_仿真与装配\run_preloaded_tray_assembly_fast.py" --gui %*
)
if errorlevel 1 pause
