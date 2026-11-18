#!/bin/zsh
set -e
cd "$(dirname "$0")/.."
if [[ ! -x 05_Project3_月面机器人装配/.venv/bin/python ]]; then
  print '项目虚拟环境不存在，请先按仓库README建立Python 3.12虚拟环境并安装requirements.txt。'
  exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec 05_Project3_月面机器人装配/.venv/bin/python 第三阶段入口.py full --gui "$@"
