# HKU CIVL 7023 Project 3

月面构件设计与PiPER六轴机械臂装配。当前方案为槽榫V2、两层16件八边形。A第二阶段设计、B第三阶段同机正式对照及技术章节、C跨机复现与补偿版工程已整合在同一仓库中。

[下载整个项目](https://github.com/yhdhhhhuk/hku-civl7023-project3/archive/refs/heads/main.zip) · [更新日志](CHANGELOG.md) · [仓库文件清单](仓库文件清单.md)

## A／C先看第三阶段成果

下载上方main ZIP并解压后，A可直接读取[B技术完整章节](05_Project3_月面机器人装配/B_第三阶段报告/B_第三阶段技术章节.md)合并总报告；C按[第三阶段对接说明](05_Project3_月面机器人装配/B_第三阶段报告/给A和C的第三阶段对接说明.md)复现、使用视频和图表。无需再导入历史交接ZIP。

| 2026-11-10同机正式对照 | 关闭补偿 | 开启补偿（本阶段采用） |
|---|---:|---:|
| 从零完成／运动目标／释放 | 16件／96／16 | 16件／96／16 |
| 最终构件最大位置误差 | 0.935791mm | 0.261732mm |
| 最终构件最大姿态误差 | 0.155598° | 0.186519° |
| 连续240Hz日志 | 145676行 | 145712行 |
| 仿真时长 | 606.9833s | 607.1333s |

两组定义外碰撞均为0，均通过独立数值复核。以定位优先采用开启补偿：最大位置误差下降72.031%，最大姿态误差增加19.872%，部分轴力矩略增。每组仅一次，不声称全面性能提升或统计可靠性。

- [正式评价说明／精确统计](05_Project3_月面机器人装配/B_第三阶段正式评价/第三阶段评价说明.md) · [机器结果摘要](05_Project3_月面机器人装配/B_第三阶段正式评价/第三阶段结果摘要.json)
- [两组视频、图表、压缩日志和冻结配置](05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/) · [独立验收](05_Project3_月面机器人装配/运行验证/B_第三阶段复核_2026-11-10/第三阶段独立验收说明.md)

第三阶段新增入口默认采用已接受的候选参数＋补偿；旧入口保留各自原默认设置。下载校验只需Python标准库，无须先安装仿真环境：

```sh
python 第三阶段入口.py verify
```

大CSV使用`.csv.gz`无损发布，`verify`会检查压缩内容的原始字节数与SHA。要重新分析封存日志，先执行`python 第三阶段入口.py restore`；仅查看章节、图表和视频无需恢复。恢复约565MB原始CSV。检查点与派生NPZ缓存留在本地，发布清单明确列出，不影响原始数据分析。完整安装步骤如下。

## 当前入口

| 内容 | 入口 |
|---|---|
| A第二阶段设计、材料状态与报告 | [A资料说明](AC回传/A/README.md) |
| 总报告初稿 | [Markdown](AC回传/A/第二阶段总报告初稿.md) · [Word原稿](AC回传/A/CIVL7023_Project3_第二阶段总报告初稿.docx) |
| 单件／六件／16件CAD | [A模型](05_Project3_月面机器人装配/A_结构设计与CAD/README_本地使用.md) |
| B运动学、控制、力矩与采集 | [B第二阶段](05_Project3_月面机器人装配/B_第二阶段控制与评价/README.md) |
| C方法、失败与成功记录 | [C复现](AC回传/C/跨机复现记录.md) · [本地运行](05_Project3_月面机器人装配/C_仿真与装配/README_本地运行.md) |
| C成功补偿版数据及视频 | [full02_compensated](runs/C_stage2/full02_compensated/) |
| C原方案受阻证据 | [full01](runs/C_stage2/full01/)；9件完成后第10件下放前受阻 |
| 本轮接收和核对 | [整合记录](AC回传/第二阶段整合记录_2026-11-10.md) |

## 安装和运行

新克隆或下载当前main可直接建立环境，无须再导入11月5日ZIP。已有工作目录先保存个人改动，再同步。使用Python 3.12，以下均在仓库根目录执行。

Windows PowerShell：

```powershell
py -3.12 -m venv 05_Project3_月面机器人装配/.venv
$py = ".\05_Project3_月面机器人装配\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install -r 05_Project3_月面机器人装配/requirements.txt
& $py -m pip check
& $py 第二阶段入口.py calibrate --output runs/local/calibration01
& $py 第二阶段入口.py single --compensate-grasp-offset --output runs/local/single01
& $py 第三阶段入口.py full --output runs/local/stage3_full01
& $py 第三阶段入口.py analyze --input runs/local/stage3_full01 --calibration runs/local/calibration01/反馈字段独立核对.json
```

Windows请将仓库放在简短的ASCII父路径，如`E:/7023/project3`，模型缓存及Bullet检查点输出需要ASCII路径。

macOS／Linux：

```bash
python3.12 -m venv 05_Project3_月面机器人装配/.venv
P3_PY=05_Project3_月面机器人装配/.venv/bin/python
"$P3_PY" -m pip install --upgrade pip setuptools wheel
"$P3_PY" -m pip install -r 05_Project3_月面机器人装配/requirements.txt
"$P3_PY" -m pip check
"$P3_PY" 第二阶段入口.py calibrate --output runs/local/calibration01
"$P3_PY" 第二阶段入口.py single --compensate-grasp-offset --output runs/local/single01
"$P3_PY" 第三阶段入口.py full --output runs/local/stage3_full01
"$P3_PY" 第三阶段入口.py analyze --input runs/local/stage3_full01 --calibration runs/local/calibration01/反馈字段独立核对.json
```

每次使用新输出目录；入口拒绝覆盖已有目录。第二阶段入口的single／full明确使用A-candidate、全程采集与录像；加`--gui`显示界面。第三阶段入口的single／full默认补偿开启，加`--without-compensation`运行关闭补偿的对照。不要覆盖`runs/C_stage2/`封存证据。

部分平台需要C++构建工具；本机Mac若遇fdopen编译错误，可用已验证方式安装：

```bash
CPPFLAGS='-Dfdopen=fdopen' "$P3_PY" -m pip install --no-build-isolation pybullet==3.2.7
```

旧`启动C装配演示`仍默认70g；新`启动第二阶段候选装配`使用候选参数，但补偿仍须显式添加。上述第三阶段full命令用于复现本阶段采用的补偿方案；控制和物理模型未因此改变。

## 数据和验证范围

C原始关节日志以`.csv.gz`无损保存，可直接解压；需要全部恢复时，在仓库根目录运行`python restore_evidence.py`，会核对原始SHA256。个人新试验用`runs/local/`等独立目录；课件、环境、历史ZIP和临时输出不发布。

| 运行 | 完成数 | 最大构件位置／姿态误差 | 说明 |
|---|---:|---|---|
| B候选基线 | 16/16 | 0.9358mm／0.1556° | 未补偿；摘要和图在A证据目录，原始大日志在B本地交接包 |
| C full01 | 9/16 | 不作为完整成功结果 | 第10件下放前碰撞预检受阻 |
| C full02_compensated | 16/16 | 0.3508mm／0.5868° | Windows从零运行，145724行240Hz数据、96运动目标 |
| 11月10日本地同步检查 | 1/1 | 0.0400mm／0.0010° | 补偿版单件、6组校准和分析通过；未再次跑全16件 |

B／C差异同时包含补偿方法与运行环境差异，不能解释为纯跨平台误差。A保留2500kg/m³均匀刚体材料的候选状态，正式采用仍待本人签核。支承说明适用于名义平地自重条件。抓取使用辅助固定约束，补偿使用理想仿真位姿，碰撞检查为离散采样。已校准的最后子步等效力矩不代表960Hz全部峰值或实机安全限值。
