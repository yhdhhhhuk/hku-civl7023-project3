# B第三阶段正式数值评价

本目录只维护同机同代码的补偿开／关正式实验及数值评价；技术章节由`../B_第三阶段报告/`维护。冻结的候选材料仍待A最终认可，实验不等待材料人工签核。

## 本轮文件

- `run_experiments.py`：冻结源文件、模型及目标SHA、载荷／时间步／门槛和依赖，串行运行两个全16件工况。发现已有manifest会拒绝覆盖。
- `analyze_experiments.py`：名义96目标、全部240Hz实际关节状态FK/J／限位／奇异值、72状态中心差分J、全部控制行FK和误差复算、TCP终点／目标距离瞬态／关节命令跟踪、全程／分阶段力矩，支持真实失败。
- `compare_experiments.py`：核对同源同配置，按共同完成构件前缀比较力矩及立即落位误差。两者全成功才并列最终16件结果及全程RMS。
- `audit_evidence.py`：源文件／资源未变及原始物理视频帧数／末帧核对。
- `write_results.py`：读取成对结果，生成完整评价说明（含已接受的开关建议、动力学／环境证据入口），最后刷新全部证据SHA。
- `finalize_experiments.py`：等待两组运行结束后，依次执行全量分析→两组审核→成对比较→完整说明与SHA定稿；不追加物理实验。
- `第三阶段结果摘要.json`：机器可读取的正式结果与路径入口；仅结果分析全部完成后生成。
- `第三阶段评价说明.md`：方法、冻结表、精确结果、改进代价与适用范围。

原始证据统一位于`../运行验证/B_第三阶段_2026-11-10/`，主manifest为`experiment_manifest.json`。所有文档和JSON路径相对本目录或该证据目录；运行manifest命令以仓库根目录为cwd。

## 复现与分析

复用项目`.venv`。本轮实际执行了`run_experiments.py`，它依次执行以下两个命令（在仓库根目录，输出目录须新建以免覆盖证据）：

```sh
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/C_仿真与装配/run_preloaded_tray_assembly_fast.py --payload-config A-candidate --telemetry --limit 16 --video --output 05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/reproduction_off
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/C_仿真与装配/run_preloaded_tray_assembly_fast.py --payload-config A-candidate --telemetry --limit 16 --video --output 05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/reproduction_on --compensate-grasp-offset
```

不得同时执行，以免共享网格缓存冲突。完整原命令、开始／结束香港时间及进程退出码在manifest中。目录不同只是输出位置；实验变量仅补偿开关。

本次固定证据位置的分析命令：

```sh
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/analyze_experiments.py
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/analyze_experiments.py compensation_off
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/analyze_experiments.py compensation_on
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/audit_evidence.py compensation_off
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/audit_evidence.py compensation_on
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/compare_experiments.py
```

反馈校准用原有第二阶段程序另存本轮证据，不改旧结果：

```sh
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第二阶段控制与评价/verify_feedback.py --output 05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/feedback_calibration.json
```

统计取全部实际样本；总览曲线为显示抽样到约16,000点，无法从图像读取所有尖峰。全程240Hz采集覆盖等待和释放；TCP／命令日志约60Hz仅覆盖运动。`kinematic_trace.csv`给出所有物理步的独立诊断，`derived_signals.npz`是为复核／绘图保存的无损派生数值数组，不替代原始CSV。

`probe_robot_model.py`只读加载相同PiPER，另存各连杆实际动态属性到`robot_loaded_dynamics.json`；机器人沿用既有导入惯量处理，构件则显式保留候选实体惯量。环境二进制指纹另见`environment_binary_fingerprint.json`。`evidence_sha256.json`的键相对`05_Project3_月面机器人装配/`，便于项目内独立复核。

## 定稿顺序与复核状态

本轮主对话独立数值复核已通过，正式数值方案接受`compensation_on`；材料签核／硬件安全认证另行处理。复核证据在`../运行验证/B_第三阶段复核_2026-11-10/独立验收结果.json`。

正式生成顺序为：`run_experiments.py`串行两组物理运行 → `analyze_experiments.py`逐组全量分析 → `audit_evidence.py`逐组核对 → `compare_experiments.py`生成成对摘要／已接受的推荐字段 → **`write_results.py`生成完整评价说明并最后刷新SHA**。最后一步不可省略：compare只生成机器摘要及对比图，不负责完整方法说明、动力学／环境指纹入口和交付SHA。

`finalize_experiments.py`封装运行结束后的上述定稿步骤，等待manifest的`runs_finished`后才开始，不重新运行物理仿真。若仅调整本阶段说明／复核状态，更新相应生成脚本与摘要后只运行`write_results.py`，保持数值与原始证据不变。代码及证据定稿后不要再改文件而不刷新SHA。

```sh
05_Project3_月面机器人装配/.venv/bin/python 05_Project3_月面机器人装配/B_第三阶段正式评价/write_results.py
```

## GitHub下载版

优先读[数据说明](../运行验证/B_第三阶段_2026-11-10/README.md)。下载包先在仓库根目录运行`python 第三阶段入口.py verify`；重算原始数据前运行`python 第三阶段入口.py restore`恢复10份无损CSV。checkpoint和NPZ缓存未发布，运行分析会重建NPZ。封存源码中包含当时本机的旧acceptance检查器，但它未被装配入口导入；下载版核对工具在live缺少该历史文件时，明确改用冻结副本验证其SHA。其余运行依赖／资源仍逐项核对。

重生成封存分析会改变派生文件和发布校验，建议保留干净下载副本。自己的试验通过新增第三阶段入口的single/full写入独立目录；该入口默认候选材料、全程日志和开启补偿，加`--without-compensation`才关闭补偿，原有启动器默认值未修改。

发布整理在上述数值定稿之后执行：`python scripts/prepare_stage3_logs.py`无损压缩大CSV → `write_results.py`刷新本地完整交付SHA → `python scripts/build_stage3_manifest.py`生成精确下载清单 → `python 第三阶段入口.py verify`校验。GitHub发布状态统一见根CHANGELOG。发布后如更新任何被校验文件，必须重新生成清单，不以旧下载SHA验证新版本。
