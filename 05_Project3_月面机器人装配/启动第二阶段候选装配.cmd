@echo off
chcp 65001 >nul
cd /d "%~dp0.."
if not exist "05_Project3_月面机器人装配\.venv\Scripts\python.exe" (
 echo 请先按给C说明建立Python3.12环境。
 pause
 exit /b 1
)
"05_Project3_月面机器人装配\.venv\Scripts\python.exe" 第二阶段入口.py full --gui %*
if errorlevel 1 pause
