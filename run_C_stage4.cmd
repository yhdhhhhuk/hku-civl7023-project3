@echo off
setlocal
cd /d "%~dp0"
set "C_STAGE4_PY=python"
if exist "..\.venv\Scripts\python.exe" set "C_STAGE4_PY=..\.venv\Scripts\python.exe"
if "%~1"=="" (
  "%C_STAGE4_PY%" run_stage3.py single
) else (
  "%C_STAGE4_PY%" run_stage3.py %*
)
exit /b %errorlevel%
