@echo off
chcp 65001 >nul
cd /d "%~dp0.."
if not exist "05_Project3_月面机器人装配\.venv\Scripts\python.exe" (
  echo 请先按仓库README创建Python 3.12虚拟环境并安装requirements.txt。
  pause
  exit /b 1
)
set PYTHONDONTWRITEBYTECODE=1
"05_Project3_月面机器人装配\.venv\Scripts\python.exe" 第三阶段入口.py full --gui %*
if errorlevel 1 pause
