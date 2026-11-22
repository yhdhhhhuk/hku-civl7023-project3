# A 第四阶段交付与验收

A 的 11 月 18 日 B 更新版于 11 月 22 日接收。英文报告、A 的三页英文汇报和正式 CAD 源件通过接收核对。总装 STL 有 128 条开边，仅作预览，实体总装使用 STEP、FreeCAD 或 DWG。

| 材料 | 入口 |
|---|---|
| 全组英文报告 | [可编辑 Word](01_Report/CIVL7023_Project3_Final_Report_EN.docx) · [PDF](01_Report/CIVL7023_Project3_Final_Report_EN.pdf) |
| CAD、装配、英语图纸 | [单件](02_CAD/01_Component/) · [总装 STEP](02_CAD/02_Assembly/Octagon16_mm.step) · [总装原生 CAD](02_CAD/02_Assembly/) · [英文 A03 图纸](02_CAD/03_Engineering_Drawing/) |
| A 的三页英文汇报 | [PPTX](03_A汇报/PartA_Presentation_EN.pptx) · [PDF](03_A汇报/PartA_Presentation_EN.pdf) · [讲稿](03_A汇报/PartA_Speaking_Guide_EN.txt) · [问答](03_A汇报/PartA_Questions_and_Answers_EN.txt) |
| 16 件物体位姿与运行数据 | [初始与目标位姿](04_一致性检查/Component_Initial_and_Target_Poses.csv) · [四工况汇总](04_一致性检查/Run_Summary_Recomputed.csv) |
| B 汇报、报告模块与推荐工况 | [B 交付入口](../../../提交/README.md) · [补偿开启组原速视频](../../../提交/simulation/05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/compensation_on/assembly.mp4) |
| C 汇报合并、Windows 单件与会议记录入口 | [C 第四阶段](../../../提交/C_Stage4_EN/README.md) |
| 完整性记录 | [独立验收](验收核对.json) · [A 原始清单](PACKAGE_SHA256.json) · [原版交付说明](00_README_EN.txt) |

## 核对结果

- ZIP 共 106 个文件，清单列出的 105 项字节数和 SHA-256 全部一致。63 项来源文件核对到 A 标注的 Git 版本，另外核对 5 个视频身份及 B 个人交付。正式双工况的四份 gzip 解压字节及 SHA 一致。重新读取 302,688 行关节记录，核对 240 Hz 连续性、两组六轴等效峰值和全程及活动段 RMS。三组全装配与一组单件的汇总分别与其记录一致。
- 从原始坐标复算 16 件名义位姿与正式对照。两组均从零完成 16 件及 96 个目标。最大三维位置误差 0.935791 → 0.261732 mm，最大水平误差 0.926721 → 0.227289 mm，最大姿态误差 0.155598° → 0.186519°。最大 J1 等效峰值 15.196 N·m 对应补偿开启组第 11 件转运。11,300 行单件记录与完整装配分别列证。
- Word 与 A 的 PPTX 均在本机渲染逐页检查，分别为 18 页及 3 页，与随包 PDF 页数一致。报告有 8 表、8 图，正文样式为 Times New Roman 12 pt、单倍行距、四边约 2.5 cm。核对课程概览第 6 页的题名、摘要、关键词、五章及参考文献要求。
- 单件 STL 米版和毫米版尺寸、闭合性及体积相符。总装 STEP 的 16 个部件实例坐标和方向均与仿真表一致。A03 DXF 为毫米、含 9 个尺寸实体。DWG 实体重开与 CAD 内核审计引用 A 的记录。本轮没有重新跑仿真。

## 提交前的组内动作

补齐英文姓名、学号和组号，确认课程提交要求及相似度回执。2500 kg/m³ 是报告和仿真的候选有效密度，材料签核待确认。C 可合并 A 的三页正片并记录实际全组联排。A 的报告沿用交付时的 B 正式全程对照、C Windows 全装配和 B 单件复现。

## 原始文件定位

A 随包原始说明和核对记录按字节保留。完整原 ZIP 及 SHA 在本地交付包归档。工作目录直接收录 96 个原文件，另有 10 个源文件经字节核对后复用现有仓库路径。原清单里的这 10 个相对路径在 [独立验收的复用映射](验收核对.json) 中对应现有文件。
