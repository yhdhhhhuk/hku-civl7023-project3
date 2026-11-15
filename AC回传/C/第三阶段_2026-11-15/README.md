# C第三阶段交付入口

基线：小组main 9806992；日期：2026-11-15。

- C_第三阶段技术章节.md：可合并技术正文。
- A报告一致性核对.md：核对范围与人工待办。
- 汇报讲稿与问答.md：C角色约4分钟讲稿。
- C_第三阶段汇报_定稿.pptx：完成运行审计后生成的6页可编辑汇报。
- 本机复现结果.md：完成后填写的本机指标、命令和视频来源。
- 原始证据：仓库runs/C_stage3/；完整交付ZIP另存E:/7023/deliverables/C_stage3_2026-11-15/。

复现命令（在E:/7023执行，输出目录不得已存在）：

```powershell
.\.venv\Scripts\python.exe project3_stage2/第三阶段入口.py calibrate --output runs/C_stage3/new_calibration
.\.venv\Scripts\python.exe project3_stage2/第三阶段入口.py full --output runs/C_stage3/new_full
.\.venv\Scripts\python.exe project3_stage2/第三阶段入口.py analyze --input project3_stage2/runs/C_stage3/new_full --calibration project3_stage2/runs/C_stage3/new_calibration/反馈字段独立核对.json
.\.venv\Scripts\python.exe project3_stage2/scripts/audit_c_stage3.py project3_stage2/runs/C_stage3/new_full
```

Windows结果目录采用ASCII路径；原始模型加载由既有ASCII缓存处理。保留失败，不覆盖B归档，不放宽碰撞阈值。候选材料、辅助抓持、理想仿真位姿、离散碰撞及最后子步力矩限制均保留。人工签核与全组演练待完成。


## GitHub下载与证据恢复

大采样CSV以.csv.gz无损发布；原始SHA及字节数在仓库evidence_compression.json。下载后在仓库根运行：

```powershell
python restore_evidence.py --prefix runs/C_stage3/
```

恢复后可运行scripts/audit_c_stage3.py核对full01。原速及4倍速视频、载荷、命令、校准、分析和独立审计随Git发布。checkpoint.json与checkpoint.bullet只在本地完整ZIP保留，复现从零启动无需它们。ZIP本身不放入Git，避免重复大文件。旧ZIP仍是生成时的本地交付快照，以当前Git提交及更新日志判断最新说明。

发布状态：2026-11-15已推送小组main，成果提交f116148。组员可直接同步当前main；没有代发聊天或邮件消息。
