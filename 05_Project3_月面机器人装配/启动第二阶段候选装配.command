#!/bin/zsh
set -e
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
exec 05_Project3_月面机器人装配/.venv/bin/python 第二阶段入口.py full --gui "$@"
