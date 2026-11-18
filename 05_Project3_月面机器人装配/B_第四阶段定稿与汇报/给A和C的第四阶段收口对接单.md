# 给 A 和 C 的第四阶段最终收口对接单（11月19日组内验收前）

- **整理日期**：2026年11月17日（11月18日更新落位误差、力矩与汇报口径）
- **目标节点**：**11月18日** 合并通读与第二次10分钟联排 → **11月19日 23:59** 组内最终验收锁版 → 11月26日课堂汇报（20%） → 11月30日 Moodle 提交报告与幻灯片（报告30%）
- **统一交付语言**：按 `2026 CIVL 7023_Course Overview.pdf` 第6页英文学术规范，**正式提交版报告与汇报幻灯片统一采用英文**（好消息：A 的 `A03_Stage3_Engineering_EN.png` 和 B 的全部实验图表本身已是英文坐标轴，无需重画图）。

---

## 一、B 已备妥可直接合入的材料清单

| 用途 | 文件路径 | 给谁用 |
|---|---|---|
| **总报告 B 英文定稿模块**（含文献综述 2.2、方法 3.2［含 `Table B1` URDF参数表与公式 (1)–(8)］、结果讨论 4.2–4.3［含 `Table B2/B3` 与落位误差分解］、结论边界及 8 条标准 APA 文献） | [B_Stage4_Report_Module_EN.md](B_Stage4_Report_Module_EN.md) | **给 A 直接粘贴进英文总报告** |
| **水平 XY 与有符号竖向落位偏差图** | [图表/layer_dz_xy_decomposition.png](图表/layer_dz_xy_decomposition.png)（对应数据 [XY与竖向误差分解.csv](XY与竖向误差分解.csv)） | **给 A 作报告讨论图。C 可直接使用 B3 的逐件 XY 图与姿态代价。** |
| **B 个人汇报幻灯片（原生可编辑 16:9 `.pptx`，共4页正片＋1页备份，与 C 母版同源）** | [B_Stage4_Slides_EN.pptx](B_Stage4_Slides_EN.pptx)（版面总览 [图表/B_Stage4_Slides_Preview.png](图表/B_Stage4_Slides_Preview.png)） | **给 C 一键并入全组最终 PPTX** |
| **B 逐页 3.5 分钟英文讲稿 + 全组 5 分钟答辩 10 大高频英文问答库** | [B_Stage4_Slides_and_QA_EN.md](B_Stage4_Slides_and_QA_EN.md) | **A / B / C 演练与 11月26日答辩共用** |
| **参数、依赖与模型边界冻结包 + 第四阶段代表性复现证据** | [参数与环境定稿包.json](参数与环境定稿包.json) · [第四阶段交叉复现说明.md](../运行验证/B_第四阶段复现_2026-11-17/第四阶段交叉复现说明.md) | **全组备查与最终锁版追溯** |

---

## 二、请 A 在 11月19日前完成的收口动作（结构 CAD 与英文总报告统稿）

- 表 B2 的有符号竖向均值（下／上层）为关闭 `+0.039943 / +0.129918 mm`、开启 `+0.039939 / +0.129902 mm`。两组碰撞裕度均为 `50 μm`，层间台阶表述为观测结果。姿态最大误差增加 `0.030921°`，随 XY 收益同时报告。
- 表 B3 保留第 11 件转运的 J1 峰值 `15.196 N·m`。Bullet 加载总质量 `4.67 kg` 含固定基座 `1.02 kg`，各力矩分量的贡献需另作分解。

1. **按 `Course Overview.pdf` 第6页硬性格式定稿英文 Word 报告**：
   - **版式四要素**：全文 `Times New Roman`、`12 point`、四周页边距 **`2.5 cm`**（注意 11月13日中文初稿实测边距为 `1.90–2.10 cm`、字体为 `Arial/雅黑`、行距约 `1.22` 倍，须统一重设）、**`Single spacing`（单倍行距）**。
   - **标准章节结构**：
     - `Title`（≤ 20 words，填写真实组员姓名与 HKU UID，移除“第三阶段完整报告初稿 / A、B、C”内部字样）
     - `Abstract`（严格控制在 **150–250 English words**，同时写明 `72.03%` 位置误差下降收益与 `+19.87%` 姿态／`+2.27%` J6 RMS 力矩折中）
     - `Keywords`（≤ 5 个英文关键词，例如：`Lunar in-situ construction; Sintered regolith simulant; Robotic assembly; Damped least squares; Pose error compensation`）
     - `1. Introduction`（月面原位建造背景、研究目标与本文工作概览）
     - `2. Literature Review`（整合 A 的烧结月壤／互锁砌块文献 + [B_Stage4_Report_Module_EN.md](B_Stage4_Report_Module_EN.md) 第 2.2 节 + C 的采样运动规划文献，共约 10–14 篇标准 APA 第7版文献，移除仓库 `Part A/B/C` 自引）
     - `3. Research Methodology`（3.1 A构件几何与八边形排布［**务必插入英文四视图 `A03_Stage3_Engineering_EN.png`** 并裁切 `A_八边形CAD.png` 多余白边］；3.2 直接并入 B 模块 `Table B1` 与公式 `(1)–(8)`；3.3 C 场景、碰撞守卫、分层释放高度 `+16.0 / +14.5 mm` 与稳定门控）
     - `4. Results and Discussion`（并入 B 模块 `Table B2`、`Table B3`、时域曲线 `compensation_on/joint_motion_torque.png` 及新增分解图 `layer_dz_xy_decomposition.png`；保留 C Windows `full01` 第10件预检拦截案例与第三阶段同机双成功的边界区分）
     - `5. Conclusions`、`Acknowledgements`、`References`（APA 7th）。
   - **查重红线**：提交前核对 `Turnitin similarity ≤ 10%, AI similarity ≤ 10%`（不含 References）。
2. **完成候选材料定稿表述闭环**：
   - 请正式确认采用 `2,500 kg/m³`（`72.6067 g`）作为本项目冻结的文献参考均匀刚体材料假设（引用 Ginés-Palomares et al., 2023），将报告正文中“正式材料采用待 A 确认”替换为面向阅卷教师的正式建模范围声明。
3. **提供 A 个人英文汇报页（约 3 页，时长控制在 3 分钟内）** 给 C 合并。

---

## 三、请 C 在 11月19日前完成的收口动作（全组英文 PPT、倍速视频与 Windows 复现）

1. **合并全组英文最终汇报 `.pptx`（及防乱码 `.pdf` 备份）**：
   - C 已发布[第三阶段六页汇报材料](../../AC回传/C/第三阶段_2026-11-15/C_第三阶段汇报_定稿.pptx)、[Windows 复现记录](../../AC回传/C/第三阶段_2026-11-15/本机复现结果.md)及[该次运行的四倍速视频](../../runs/C_stage3/full01/assembly_4x.mp4)。合并时区分 C 的跨机结果和 B 的同机对照，按视频实际来源标注字幕。
   - 请将 **A（3页）+ [B_Stage4_Slides_EN.pptx](B_Stage4_Slides_EN.pptx)（正片4页，已采用与你完全相同的母版和尺寸，可直接复制幻灯片）+ C（3–4页英文规划、避碰、演示与总结）** 合并为一份 10–11 页的全组最终英文 PPTX，并将全组核心精度／力矩口径统一到**第三阶段同机对照表**（`0.9358 → 0.2617 mm`、`0.1556° → 0.1865°`、`607.13 s`、`64 direct + 32 vertical + 0 RRT`）。
2. **基于第三阶段选定视频导出汇报用倍速短片**：
   - 选定工况原速视频 [compensation_on/assembly.mp4](../运行验证/B_第三阶段_2026-11-10/compensation_on/assembly.mp4) 长达 `607.2 s`（10分07秒），无法在 10 分钟汇报中原速播完；请**基于该文件**导出 8× 倍速版（约 76 秒）或关键阶段剪辑版嵌入 PPT（画面注明 `8x speed from continuous 607.13s physics run`），同时保留原速 `assembly.mp4` 作为正式提交视频，**切勿混播第二阶段旧视频 `runs/C_stage2/full02_compensated/assembly_4x.mp4`**。
3. **Windows 端第四阶段快速复现与两次联排记录**：
   - 同步仓库后，在 Windows ASCII 父目录运行 `python 第三阶段入口.py verify` 与 `python 第三阶段入口.py single`（并测试新增的 [启动第三阶段推荐装配.cmd](../启动第三阶段推荐装配.cmd)），回传简明复现结果；11月18–19日组织两次 10 分钟全组联排（A 3:00 + B 3:30 + C 3:30）并记录用时。
