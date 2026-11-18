# B第三阶段正式实验数据

本目录发布2026年11月10日同机、同代码、同候选参数下的补偿关闭／开启两次从零16件实验。两组均16/16、96目标、16释放通过；定义外碰撞0，19物体恒定。精确指标见[condition_summary.csv](condition_summary.csv)，全部方法与权衡见[评价说明](../../B_第三阶段正式评价/第三阶段评价说明.md)。

| 工况 | 最大最终位置误差 | 最大姿态误差 | 240Hz行数 | 原始物理视频 |
|---|---:|---:|---:|---|
| 关闭 | 0.935791mm | 0.155598° | 145676 | [视频](compensation_off/assembly.mp4) |
| 开启（本阶段采用） | 0.261732mm | 0.186519° | 145712 | [视频](compensation_on/assembly.mp4) |

## 下载后使用

在仓库根目录，用任意兼容Python3版本执行：

```sh
python 第三阶段入口.py verify
python 第三阶段入口.py restore
```

verify检查本次发布清单及10份gzip的原始字节／SHA，不需要仿真依赖。restore只恢复第三阶段10份大CSV，不恢复旧C数据、不覆盖已有不同内容。查看章节、图表、视频无需恢复。需要重算封存日志时先restore，再按[分析说明](../../B_第三阶段正式评价/README.md)执行；它会重建派生CSV／图表／NPZ，之后原发布校验可能因派生文件重生成而变化，应保留一份干净下载副本作原始参照。自己的物理试跑用第三阶段入口single/full，写入runs/local等新目录。

各工况的joint_full_trace.csv.gz是全部外部240Hz物理步，b_control_trace.csv.gz约60Hz运动记录，inventory_trace.csv.gz为2Hz全构件COM，trajectory.csv.gz为20Hz当前构件几何原点，kinematic_trace.csv.gz为全量独立运动学诊断。CSV格式与恢复后的内容未改变。

`publication_manifest.json`是下载发布清单，路径键相对仓库根目录；列出发布文件、10个压缩恢复映射及6个仅本地文件。`evidence_sha256.json`是本地完整交付证据清单，包含未发布的恢复检查点、派生缓存和恢复前不存在的原始CSV，不能在尚未恢复的ZIP目录直接按“每项必须存在”检查。下载校验请用上面的verify。

未发布的checkpoint.json/.bullet仅用于本地故障恢复；derived_signals.npz是可从CSV重建的分析缓存。两组均从零成功，使用已发布原始CSV、result、释放／场景记录、源码冻结、环境及视频即可复算，不依赖这些缓存。

候选材料仍待A签核。辅助固定约束、理想仿真位姿补偿、离散避碰及最后子步等效力矩的限制保持原说明，不表示真实感知、纯摩擦抓取或厂家承载认证。
