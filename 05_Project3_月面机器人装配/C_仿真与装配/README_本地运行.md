# C第二阶段本地运行

C第二阶段已通过PR #1合并，本地于2026年11月10日同步。直接使用当前main，无须再次导入旧ZIP。安装和跨平台命令见[根README](../../README.md)，方法及结果见[C复现记录](../../AC回传/C/跨机复现记录.md)。原记录中的“未推送”是11月7日封存时的历史状态，当前发布状态以[CHANGELOG](../../CHANGELOG.md)为准。

在仓库根目录，用本机Python环境执行：

```bash
05_Project3_月面机器人装配/.venv/bin/python 第二阶段入口.py calibrate --output runs/local/calibration01
05_Project3_月面机器人装配/.venv/bin/python 第二阶段入口.py single --compensate-grasp-offset --output runs/local/single01
05_Project3_月面机器人装配/.venv/bin/python 第二阶段入口.py full --compensate-grasp-offset --output runs/local/full01
05_Project3_月面机器人装配/.venv/bin/python 第二阶段入口.py analyze --input runs/local/full01 --calibration runs/local/calibration01/反馈字段独立核对.json
```

Windows把Python路径换为`05_Project3_月面机器人装配/.venv/Scripts/python.exe`，项目父路径和输出用ASCII。每次选择新输出目录，不要覆盖`runs/C_stage2/`封存结果。

包装器显式选择A-candidate、telemetry和录像；补偿须传`--compensate-grasp-offset`。主程序和旧`启动C装配演示`仍默认legacy70g；新`启动第二阶段候选装配`默认候选但不会自动打开补偿。去掉补偿选项可做未补偿对照。

原版full01完成9件后第10件预检受阻；full02_compensated从零16/16，最大构件误差0.3508mm／0.5868°，145724行240Hz记录。压缩日志可用根restore_evidence.py恢复并校验。补偿依赖理想仿真位姿，辅助固定约束、离散碰撞检查与候选材料限制保留。
