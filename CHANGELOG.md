# 项目更新日志

按香港时间倒序记录A／B／C共享更新。Git提交记录逐行差异，本日志说明变更、验证范围、组员对接与发布状态。

## 填写约定

- A、B、C各自完成一项有意义的修改时，随该修改更新本文件；同一天可分别记录。
- 写明负责人、修改内容与路径、验证结果、对其他人的影响，以及需要谁继续处理。
- 本地完成的内容先放在“待发布”；推送成功后再移入对应日期的“已发布”记录，并填写Git提交号。打包、邀请协作者或本地测试通过，都不代表代码已推送。
- 修改几何、坐标、单位、质量／惯量、启动命令或依赖时，写清前后差异；新增／删除文件时同步维护相应文件清单。
- 验证只写实际执行的范围，保留失败及限制；不把历史结果、新参数结果和跨机复现混在一起。
- Git提交保留逐行改动，本日志说明组员需要知道的变化；完整原始运行数据仍放在各次独立结果目录。

## 待发布

### 本地保留而未作为完整原始资料发布

11月5日历史AC交接ZIP、11月4日B第二阶段原始大日志／视频、同步前备份和个人环境继续在B本地保留；11月10日第三阶段两组日志及视频已另行发布，不能混作同一批次；B控制／采集／评价代码已随C的11月8日提交发布，B结果摘要和图表本轮随A证据提供。不能再把“整份第二阶段均未上传”当作当前状态。

## 已发布

### 2026-11-19 | C English review across stages and stage-4 technical handoff (published)

- Scope: C-owned narratives, templates, issues, presentations and stage-4 delivery. A/B originals are unchanged. Scanned 331 tracked C-scoped files; 21 English delivery documents/decks pass the Han-character check. Compatibility paths and immutable raw/frozen evidence remain original, with explicit dispositions in C_stage4/language_audit.json.
- Changes: English historical/current C chapters, notes and decks; four-slide stage-4 module; B+C combined review deck (eight main slides plus B backup, pending A); PDF image backups; 8x selected B formal video with English overlay and SHA lineage; ASCII-named headless launcher; submission/C copy in the existing submission tree.
- Verification: 161-file/10-log package check, six calibration cases, new Windows single run (11300 rows, 0.0399591 mm, 0.000977302 degrees), independent audit and 236-frame check passed. The 8x video has 3036 frames at 40 fps, lasting 75.9 s. PPT package/layout/import checks passed. PDFs were rendered and inspected. No new full 16-component run is claimed.
- Packaging correction: adding C logs to the shared compression index initially invalidated B's manifest. C now uses a separate index and restore script; the original shared index is unchanged and package verification passes again.
- Repairs/limits: preserved the real stage-2 chart workbook when import omitted its relationship; normalised an invalid B alignment enum only in the temporary combined-deck copy. Native PDF export lacked a runtime font module, so backups use verified slide images; editable originals remain PPTX. Frozen source hashes, model parameters and archived evidence are unchanged.
- Pending: A's three English personal slides and two actual timed group rehearsals. A material approval, final Word/report sign-off and course submission remain member actions. No messages sent and no approval fabricated.
- Entry: C_stage4/README.md and the new C_Stage4_EN subfolder in the submission tree. Published content commit: e2e482aca2db316c44d3223aa6f13d7ee4944734; pushed to group main successfully. Remote SHA verification is recorded in the publication receipt.

### 2026-11-18｜B 个人提交目录与第四阶段发布核对

B 整理 [个人提交材料](提交/README.md)。A 可取英文报告与五张配图，C 可取可编辑汇报页，B 可取讲稿、答辩题、源码、模型和仿真证据。独立复制整个目录后，使用项目 Python 环境重新跑通补偿单件，记录 11,300 行，并核对五页 PPT 和报告图件。第四阶段数据复核确认归档六组校准通过，单件关节日志原始 SHA 匹配。本次未重新运行全套 16 件。

已整合 C 的第三阶段提交 `f116148` 和发布记录 `673cee4`。根目录压缩索引包含新增的六份 C 日志，原 14 条记录一致。更新第三阶段发布清单中这一份共享索引的字节数与 SHA，使仓库入口继续核验 161 项及 10 份 B 压缩日志。提交目录的仿真副本使用配套的历史清单和索引，同项核验通过。A 负责合并全组报告和 CAD，C 负责合并汇报页、视频及联排记录。

成果提交 [`125de28`](https://github.com/yhdhhhhuk/hku-civl7023-project3/commit/125de288fbe7ae001b7388c2801f931449902b39) 已推送公开仓库 main。提交目录共 334 个文件。


### 2026-11-18｜B第四阶段报告、汇报与复核脚本修订

B负责。英文报告表B2据两组原始坐标修正两层平均竖向偏差，并同步讲稿、答辩及交接说明。表B3修复列标题，书籍DOI已校正。力矩讨论引用J1在第11件转运时的实测等效峰值15.196 N·m。B3正片改为逐件水平误差单图，列出最大姿态误差增加0.031°。A合并修订后的英文模块，C采用同目录新版PPT及讲稿。

主对话在仅含第四阶段压缩关节日志的临时下载式副本中独立运行复核脚本。正常副本通过11,300步与原始SHA校验。将校准记录改成失败，或在保持字节数和行数的情况下修改一个数据字符，均以非零退出。更新后的PPT生成器可从副本生成5页，已逐页检查实际渲染。第三阶段发布清单161项及10份日志通过。验证复用本机项目解释器。修订随 `125de28` 发布。


### 2026-11-17｜B完成第四阶段控制评价定稿、代表性交叉复现、英文报告模块与个人汇报材料

- **负责人：** B（用户本人）。
- **变更：** 新增 `05_Project3_月面机器人装配/B_第四阶段定稿与汇报/`（含控制与评价定稿说明、对齐课程第6页规范的英文报告插入模块 `B_Stage4_Report_Module_EN.md`、与C同母版的16:9可编辑 `B_Stage4_Slides_EN.pptx`、3.5分钟英文讲稿与10题答辩问答库 `B_Stage4_Slides_and_QA_EN.md`、水平XY与实测竖向偏差分解数据／300DPI图、依赖与参数冻结包 `参数与环境定稿包.json` 及给A/C的收口对接单）；新增 `运行验证/B_第四阶段复现_2026-11-17/` 保存本轮校准与补偿单件复现证据（大日志以 `.csv.gz` 无损共享）；补齐 `启动第二阶段候选装配.command` 可执行权限，修复 `启动C装配演示.cmd` 默认Windows输出为ASCII目录，新增 `启动第三阶段推荐装配.command`／`.cmd`。共享控制／规划Python源码、模型参数及第三阶段封存文件零改动。
- **验证：** `python 第三阶段入口.py verify` 161文件及10份无损压缩日志校验通过；新跑6组反馈校准6/6通过；补偿版代表性单件 `single01_compensated` 从零1/1完成（退出码0、恒定19物体、6段到达、11300行240Hz连续采样、236帧视频、C独立审计 `audit_reproduction.py` PASS），最终位置误差`0.039958mm`、姿态`0.000977°`、XY补偿量`0.020105mm`，与11月10日第三阶段开启组第1件差值为`0.0m`；分解全16件确认纯水平最大误差`0.926721→0.227289mm`（降`75.474%`），下／上层竖向静态偏移恒为`+0.040mm`／`+0.130mm`；PPTX内部47个XML部件解析核验通过。本轮未重新跑满16件或Windows真机安装。
- **影响与对接：** A可直接将 `B_Stage4_Report_Module_EN.md`（含URDF表、公式1–8、表B2/B3与8条APA文献）及 `layer_dz_xy_decomposition.png` 并入最终英文Word报告并完成材料定稿声明；C可直接将 `B_Stage4_Slides_EN.pptx` 正片4页并入全组英文PPT、基于 `compensation_on/assembly.mp4` 导出汇报倍速视频并回传Windows端复现及联排记录。
- **同步状态：** 第四阶段随 `125de28` 推送 GitHub main。

### 2026-11-15 | C stage-3 Windows reproduction and handoff (published)

- Owner: C. Integrated A/B baseline 9806992, added independent audit, report module, consistency review, six-slide deck and speaking notes. Formal paired experiments, historical failure and Windows reproduction are kept distinct.
- Verification: six calibration cases, single run and uninterrupted full 16/16 run passed. Full result: 607.183333 s, 145724 rows, maximum errors 0.350763 mm / 0.586786 degrees; 64 direct + 32 vertical segments; zero out-of-definition collisions. Twelve independent checks, 3036 physical frames and full analysis passed; all 69 resources match B.
- Failures and limits: sparse-checkout omissions were resolved; BOM/target-subset audit and PPT font/image/link issues were repaired. No physics threshold changed. Candidate material, assistance, ideal pose and discrete checks remain limitations.
- Remaining actions: group approval, final report/presentation integration and rehearsals.
- Published changes: f116148; publication record: 673cee4. Large CSVs are lossless gzip with original-byte SHA verification; video and reports are tracked. Checkpoints and full ZIP remain local.
- Entry: C_stage4 now provides English delivery copies and maps the historical stage-3 handoff paths. Raw evidence: runs/C_stage3/.

### 2026-11-13｜接收A第三阶段CAD与完整报告初稿

- **负责人：** A交付，B工作区整合。
- **变更：** 原59文件按版本整合至AC回传/A/第三阶段_2026-11-13/，新增A-03中英文总装／接口DWG、DXF和预览、结构定版说明、完整报告初稿及正式结果表。单发的两份DWG与ZIP内同名文件相同，共用同一入口；第二阶段资料完整保留。
- **验证：** 40项来源SHA与现有仓库一致，32条目标／最终落位记录、48项力矩和34项工况汇总值复核通过；两份DXF均毫米单位、各9尺寸实体。查看工程图预览，核对Word关键数值并保持原稿字节。原生CAD复开来自A证据，本轮未在本机重算CAD、重跑仿真或验收Word版式。
- **影响与对接：** A沿用正式对照使用的V2几何和候选载荷作为CAD定版；未改控制／模型／已验收B、C结果。材料仍候选，正式采用待A本人签核；总报告仍为初稿，第四阶段继续一致性核对与演练。
- **同步状态：** 已推送现有公开仓库main，成果提交`f0548758b4e1788bf546251bd2bbb39a0243af11`，792个Git文件；随后文档提交补记实际发布状态，未向组员发送消息。
- **入口：** [最新A资料](AC回传/A/第三阶段_2026-11-13/README.md)。原ZIP及SHA归档本地交付包/收到的A原包/。

### 2026-11-10｜B第三阶段正式对照与技术完整稿（已发布）

- **负责人：** B；主对话协调并独立验收，机器人对话执行实验，给AC交流对话撰写章节。
- **变更：** 基于`dbcc96698dbe876792955e3e2db65d8289cf9bbb`冻结当前A/C整合代码，在同一本机完成抓持偏置补偿关闭／开启两次从零16件对照。新增`B_第三阶段正式评价/`的运行、全量分析、证据核对与定稿工具，`B_第三阶段报告/`的技术完整稿／方法核对／A-C交接说明；原始证据在`运行验证/B_第三阶段_2026-11-10/`（均在项目子目录内）。共享控制器、PiPER、V2几何、候选参数和旧结果未修改。
- **结果：** 两组均16/16、96目标、16释放、定义外碰撞0、19物体恒定；240Hz日志145676／145712行，仿真606.9833／607.1333s。最大最终位置误差0.935791→0.261732mm，姿态0.155598→0.186519°。按定位优先接受开启补偿方案，同时报告姿态及部分轴力矩代价；原有启动器默认不变；本次另增第三阶段入口，默认采用候选参数及补偿开启。
- **验证：** 主对话独立核对25源码／69资源SHA、全部日志连续性／六轴峰值RMS、192实际目标FK、全部64927控制行误差、每组60状态FD雅可比、32释放门控、补偿公式及6071视频帧；与交付统计一致，6组反馈校准通过。见`运行验证/B_第三阶段复核_2026-11-10/第三阶段独立验收说明.md`。两组本轮均成功，不以历史C失败冒充对照组失败。
- **影响与对接：** A采用最新B章节／图表并确认候选材料；C统一显式`--payload-config A-candidate --telemetry --compensate-grasp-offset`及对应视频。保留辅助抓持、理想仿真位姿、离散碰撞和最后子步力矩采样范围；机器人实际导入惯量已另存，不声称厂家标定。更新根分工、计划、记忆及本地文件清单。
- **干净副本核对：** 不含.git／.venv的下载式副本通过161个发布文件校验、10份原始CSV恢复、本机6组校准、补偿单件及分析；单件11300行，位置误差0.0399577mm。复用现有解释器依赖，未重新跑两组16件或验证Windows安装。
- **发布整理：** 新增第三阶段下载校验／无损恢复／独立目录运行入口，10份大CSV以gzip发布并核对原始字节SHA；两组完整视频、图表、报告、冻结源码和独立验收一起发布，6个本地检查点／派生缓存不入Git。README与发布清单同步，旧课件／环境／交付ZIP不加入。
- **同步状态：** 已推送公开仓库main，成果提交`c915fec9294a2f975eae21a8be859f6f94a40e23`；远端提交一致，匿名main ZIP返回HTTP200。随后文档提交补记本条发布状态；未代发组员消息。

### 2026-11-10｜A第二阶段接收与C版本同步

- **负责人：** B工作区整合，A提供A-R02，C提供已合并的复现版本。
- **变更：** A原包62文件及Word原稿已整合到`AC回传/A/`，新增统一入口、接收核对和来源哈希；C的代码、完整视频、压缩日志、章节及PPT已同步到本地。README、A／C说明与两份文件清单更新，原本地改动有备份和Git安全快照。
- **验证：** A的44项来源SHA全部一致；C四份原始日志字节SHA与连续性通过，成功运行的释放、场景及力矩复算通过。本机6组校准、补偿单件、11300行分析和236帧视频通过，误差0.0399577mm／0.0009775°。未再次运行完整16件，未重新安装Windows环境或原生CAD重算。
- **影响与对接：** 直接使用当前main即可，无须再导入旧ZIP；复现C成功工况需显式`--compensate-grasp-offset`。A已补设计和基本自重支承，但材料正式采用仍待本人确认。控制算法、参数和封存原始结果未修改。
- **同步状态：** 已推送小组仓库main；成果提交`39a22dbf3d162758044fe6c3cb5d6ccee1e45495`（在C提交`2833a87320706f6891ee1559ff6283b082b5f233`上接续）。发布后再补记本条状态，未改写成果提交。
- **入口：** [本轮整合记录](AC回传/第二阶段整合记录_2026-11-10.md)。

### 2026-11-08 | C stage-2 handoff and group repository publication

- Integrated the 5 November package on baseline 430bbe22746fe3493b62877bf22e9fcd2406d7bc, including candidate payload, 240 Hz telemetry, local calibration and analysis.
- Fixed Windows non-ASCII model/checkpoint paths with an ASCII asset cache and output directories. Original full01 stopped before component-10 lowering after nine placements; failure evidence remains in runs/C_stage2/full01/.
- Added optional --compensate-grasp-offset based on ideal simulated post-lift state, with a 2 mm bound. Targets, geometry, mass, contact criteria, dynamics and B control algorithm remain unchanged.
- Six local calibration cases and single run passed. full02_compensated completed 16/16 from zero: 607.1833 s, maximum position error 0.3508 mm and orientation error 0.5868 degrees, 145724 continuous rows, constant 19-body scene, 16 zero-displacement attachments and 3036 verified frames.
- Actual planning: 64 checked direct quintic segments plus 32 vertical sampled DLS segments; zero RRT execution. No recorded out-of-definition collision or 3 N release escalation.
- Delivered chapter, issues, reproduction record, original/4x videos, five slides and notes. The 478-file ZIP and SHA checks passed; extracted calibration and robot/component loading passed, not a second full run.
- Commits: bd9b7a3 and 905aa40. PR #1 merged on 8 November as 33b9bc3b97d227d4a60001dc0589d04b281c4456. Full archive: https://github.com/jinnmy-chen/hku-civl7023-project3/releases/tag/c-stage2-20261108 . ZIP SHA256: 945765183ea6997bf8cf77a56a9b4d7fa97e5367f56db84b88dcb7e5cc80d8d6.
- A integrates and confirms candidate material/structure; B reviews torque interpretation and reproduces. No group approval was prefilled. Uniform candidate material, assisted grasping, ideal pose, discrete checks, last-substep feedback, corner gaps and absent lateral connections limit the result. This was stage 2, not completion of the course project.

### 2026-11-04｜首次GitHub共享基线

- 发布代码、模型、A首阶段CAD及旧70g释放修复v4结果，276文件。旧v4从零16/16，最大构件误差0.8226mm／0.2878°。
- 提交：`430bbe22746fe3493b62877bf22e9fcd2406d7bc`。该版本为历史基线，已被11月8日C版本接续。

## 后续填写模板

复制以下内容到“待发布”顶部；推送后再补全提交号并移入“已发布”。

```markdown
### YYYY-MM-DD｜一句话说明本次更新

- **负责人：** A／B／C（姓名或GitHub账号）。
- **变更：** 改了什么、为什么改，相关文件／目录。
- **验证：** 实际执行的命令或检查、结果目录、通过／失败与未验证范围。
- **影响与对接：** 参数／接口／运行方法是否变化，其他组员要做什么。
- **同步状态：** 仅本地／已推送；已推送时填写提交号。
```
