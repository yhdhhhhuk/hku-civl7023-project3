"""Publish local numerical report and SHA evidence after paired analysis completes."""
from pathlib import Path
import hashlib,json,math
from analyze_experiments import OUT,CODE,ROOT,read,dump

def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(str(x) for x in r)+' |\n' for r in rows)
def fmt(v,n=6):return '未形成最终全结构结果' if v is None else f'{v:.{n}f}'
def main():
 a=read(CODE/'第三阶段结果摘要.json');m=read(OUT/'experiment_manifest.json');s=a['conditions'];ids=['compensation_off','compensation_on'];off,on=[s[x] for x in ids]
 configs=read(OUT/'control_and_model_freeze.json');cal=read(OUT/'feedback_calibration.json');assert len(cal['tests'])==6 and all(x['passed'] for x in cal['tests'])
 for key in ids:assert read(OUT/key/'evidence_audit.json')['runtime_and_resource_hashes_unchanged']
 rows=[]
 for key in ids:
  x=s[key];rows.append([key,f"{x['completed_count']}/16",x['success'],x['moves_reached'],x['release_gates_verified'],x['rows'],fmt(x['simulated_seconds'],4),fmt(x['wall_seconds'],3),fmt(x['final_max_position_error_mm']),fmt(x['final_position_RMS_mm']),fmt(x['final_max_orientation_error_deg']),fmt(x['final_orientation_RMS_deg'])])
 outcome=table(['工况','完成件数','整体成功','运动目标','释放通过','240Hz行数','仿真s','墙钟s','最终位置最大mm','最终位置RMS mm','最终姿态最大°','最终姿态RMS°'],rows)
 movement=table(['工况','TCP终点位置最大mm','TCP终点姿态最大°','关节命令FK跟踪位置RMS mm','命令FK位置峰值mm','命令FK姿态RMS°','最小限位裕度°','全程最小缩放σ','最大缩放条件数','关节最大速度rad/s'],[[key,fmt(s[key]['max_TCP_endpoint_position_mm']),fmt(s[key]['max_TCP_endpoint_orientation_deg']),fmt(s[key]['command_FK_tracking_RMS_mm']),fmt(s[key]['command_FK_tracking_peak_mm']),fmt(s[key]['command_FK_tracking_RMS_deg']),fmt(s[key]['min_joint_margin_deg']),fmt(s[key]['min_scaled_sigma']),fmt(s[key]['max_scaled_condition']),fmt(s[key]['max_joint_velocity_rad_s'])] for key in ids])
 torque=table(['工况','轴','原始峰值N·m','原始RMS N·m','最后子步等效峰值N·m','等效RMS N·m','峰值仿真s／件／阶段'],[[key,f"J{v['joint']}",fmt(v['raw_peak_abs_Nm']),fmt(v['raw_RMS_Nm']),fmt(v['last_substep_equivalent_peak_abs_Nm']),fmt(v['last_substep_equivalent_RMS_Nm']),f"{v['peak_time_s']:.6f}／{v['peak_item']}／{v['peak_phase']}"] for key in ids for v in s[key]['torque']])
 methods=table(['工况','完成关节命令网格预检段','完成竖直IK／在线检查段','实际RRT段','已尝试RRT路线','定义外执行碰撞','19物体恒定'],[[key,s[key]['planning_detail']['command_grid_preflight_executed'],s[key]['planning_detail']['vertical_IK_online_guard_executed'],s[key]['RRT_segments_executed'],s[key]['planning_detail']['RRT_route_trials_attempted'],s[key]['execution_collisions'],True] for key in ids])
 verification=table(['工况','全部控制行数','FK位置最大差m','FK姿态最大差°','72状态FD/J最大差','位置误差重算最大差m','姿态误差重算最大差°','名义/实际目标数'],[[key,s[key]['all_control_rows_verified'],f"{s[key]['all_control_FK_max_position_difference_m']:.3e}",f"{s[key]['all_control_FK_max_orientation_difference_deg']:.3e}",f"{s[key]['FD_Jacobian_72_samples_max_abs']:.3e}",f"{s[key]['position_error_recompute_max_difference_m']:.3e}",f"{s[key]['orientation_error_recompute_max_difference_deg']:.3e}",f"96/{s[key]['actual_target_count']}"] for key in ids])
 paired=''
 if a['paired_deltas_if_both_success']:
  paired=table(['指标','关闭','开启','开启−关闭','相对变化%'],[[key,fmt(v['off']),fmt(v['on']),fmt(v['on_minus_off']),fmt(v['relative_change_percent'],3)] for key,v in a['paired_deltas_if_both_success'].items()])
 else:paired='至少一组没有形成完整16件最终落位结果，不能将缺失项填成零，也不直接比较两组不同工作量的全程RMS。共同完成任务前缀与统计见下节。'
 failures='本轮两组均成功；没有人为构造“修复前失败”。两组的精度／代价差异按实测比较，旧C第10件受阻只作历史背景，不作本轮失败；旧诊断扫描两工况高度不一致，也未用于证明纯XY补偿的间隙因果。'
 if a['failures']:
  failures='\n'.join(f"- {key}：实际完成{len(f['completed_items'])}件；错误`{f['error']}`。最后规划记录详见该工况result.json；检查点／failure.bullet／完整日志与视频保留。" for key,f in a['failures'].items())
 recommended=a['recommendation'];choice=recommended['command_switch']
 tradeoffs=table(['轴','关闭等效峰值N·m','开启等效峰值N·m','开启−关闭峰值','关闭等效RMS','开启等效RMS','开启−关闭RMS'],[[f"J{x['joint']}",fmt(x['off_peak_Nm']),fmt(x['on_peak_Nm']),fmt(x['on_minus_off_peak_Nm']),fmt(x['off_RMS_Nm']),fmt(x['on_RMS_Nm']),fmt(x['on_minus_off_RMS_Nm'])] for x in a['paired_torque_tradeoffs']]) if a['paired_torque_tradeoffs'] else '只有共同完成工作量的统计可比，见common_workload_torque.csv；不拿不等工作量的全程RMS作优劣结论。'
 actual_tradeoff=''
 if a['paired_deltas_if_both_success']:
  delta=a['paired_deltas_if_both_success'];pdelta=delta['final_max_position_error_mm']['relative_change_percent'];odelta=delta['final_max_orientation_error_deg']['relative_change_percent'];prms=delta['final_position_RMS_mm']['relative_change_percent'];orms=delta['final_orientation_RMS_deg']['relative_change_percent']
  largest_peak=max(a['paired_torque_tradeoffs'],key=lambda x:x['on_minus_off_peak_Nm']);largest_relative_rms=max(a['paired_torque_tradeoffs'],key=lambda x:x['on_RMS_Nm']/x['off_RMS_Nm'])
  actual_tradeoff=f"本次开启补偿相对关闭：最大位置误差变化{pdelta:+.3f}%，位置RMS变化{prms:+.3f}%；最大姿态误差变化{odelta:+.3f}%，姿态RMS变化{orms:+.3f}%。并非每件构件都改善。等效峰值增量最大为J{largest_peak['joint']}的{largest_peak['on_minus_off_peak_Nm']:+.6f}N·m；RMS相对增幅最大为J{largest_relative_rms['joint']}的{(largest_relative_rms['on_RMS_Nm']/largest_relative_rms['off_RMS_Nm']-1)*100:+.3f}%（{largest_relative_rms['off_RMS_Nm']:.6f}→{largest_relative_rms['on_RMS_Nm']:.6f}N·m）。这些单次微小力矩差不作统计显著性判断。"
 text=f'''# B第三阶段正式数值评价

实际运行／分析日期：2026年11月10日（香港时间）。本地正式同环境开关对照已完成，技术完整稿由`../B_第三阶段报告/`引用本结果；本说明是数值方法与证据说明，不替代材料／结构签核。起始代码`{m['git_head']}`，同一本机`{m['platform']}`、`{m['machine']}`，两组依次从零运行，无检查点续跑。运行中未修改公共控制代码。

## 实验设计与冻结

实验唯一算法开关是`--compensate-grasp-offset`。两组均使用候选载荷、全程采集、16件和视频；实际命令、开始／结束香港时间、退出状态、源文件／资源哈希在`../运行验证/B_第三阶段_2026-11-10/experiment_manifest.json`。详细模型／控制设置在同目录`control_and_model_freeze.json`、依赖在`dependencies.txt`，运行源码逐字节封存在`frozen_source/`。环境包版本及PyBullet实际二进制SHA见`environment_binary_fingerprint.json`。分析已核对两组源码哈希、候选参数哈希、名义目标、源位姿、物理步长、释放与碰撞设置相同，且运行前后冻结文件未改。

- 机器人：原PiPER固定基座，原六轴及双指URDF；实际导入质量、COM与惯量逐杆记录在`robot_loaded_dynamics.json`。既有机器人加载器未设URDF_USE_INERTIA_FROM_FILE，故其惯量按当前Bullet导入方式处理，不能假定逐字保留URDF惯量张量或属于厂家标定；构件另用该标志且已逐值核对候选惯量。名义TCP为gripper_base下[0,0,0.1358]m。V2几何不变，34凸碰撞子形状；全部16件在第0步前预置，仿真场景19物体恒定。
- 候选均匀密度2500kg/m³，质量{m['payload']['mass_kg']:.14f}kg，质心底面坐标[0,0,{m['payload']['centre_of_mass_in_geometry_frame_m'][2]:.15f}]m；质心惯量diag(7.554717961655561e−6,1.8706254628322218e−5,2.040344e−5)kg·m²。完整JSON见`candidate_payload.json`，实际加载核对在各组`loaded_payload.json`。几何轴即惯性主轴；底面原点p_origin=p_base−R_base COM，未将质心误作底面原点。
- 月面重力1.62m/s²，外部dt=1/240s，每步4子步，控制60Hz；物理求解100次迭代。闭爪命令force1N，开爪1N及有界3N，固定辅助约束maxForce30。保留相对接触缓存参数10⁻⁵及原碰撞／释放门槛。
- 外环任务误差增益3，线速度0.04m/s、角速度0.3rad/s缩放，DLS阻尼0.02、关节率缩放0.35rad/s；关节路线五次过渡，位置电机内环positionGain0.15、velocityGain1、maxVelocity0.6rad/s。名义路线速度与瞬时电机速度是不同概念，完整参数见冻结表。
- 内部目标收敛：0.1mm／0.1°且关节速度<0.02rad/s，连续15控制样本；最终构件：位置<3mm、姿态<0.05rad、线速度<5mm/s且下方支撑接触。它们是组内数值门槛，不是课程评分门槛。

## 补偿方法与因果范围

开启组在lift后读取理想仿真中的构件底面原点与TCP位姿，将抓持偏置转换到TCP局部系，再按目标工具朝向预测水平偏置；以负偏置修正transfer和lower的TCP XY，校正幅度上限2mm。名义构件装配目标不变，retreat仍回到名义XY，未重设构件姿态、关闭碰撞或放宽阈值。它是基于准确仿真状态的几何补偿，不能称为真实视觉或传感闭环。

{outcome}

{paired}

墙钟时间受本机调度、录像和文件写入影响，只作本次耗时记录；仿真时间用于比较执行流程。每工况仅一次，结果不支持统计显著性、成功率置信度或普遍鲁棒性结论。相同平台的固定步长实验避免将历史B/C跨平台差异误作补偿因果证据。

## 三类误差与运动学

{movement}

1. **最终构件误差**：全部装配与最终沉降后，相对名义底面几何原点及姿态计算；位置RMS跨16件，姿态RMS跨16件，不是时间RMS。
2. **TCP终点误差**：每个move达到控制收敛条件时相对该move目标的误差。补偿开启时transfer/lower目标是修正后的TCP目标，构件误差仍相对未修改的名义装配目标。
3. **命令跟踪误差**：在每个约60Hz控制样本比较实际q与q_command；另外独立FK(q_command)与实际TCP比较，衡量电机命令跟踪。逐轴RMS／峰值在`joint_command_tracking.csv`。运动中实际TCP到最终目标的距离另存`TCP_target_tracking.png`；该距离包含正常的搬运动作和目标切换，不能称作轨迹跟踪精度。未宣称笛卡尔路径横向误差或真实机械振动已得到验证。

世界系几何雅可比J为6×6、[线速度;角速度]。缩放W=diag(1/0.3,1/0.3,1/0.3,1,1,1)，对WJ报告最小奇异值与条件数，无未经依据的通用奇异性合格线。名义96姿态均IK通过；实际每个规划目标另核对FK残差与限位／奇异值，补偿目标也在其中。全部240Hz状态重算FK/J／关节限位及URDF速度限值，初始姿态与运动阶段分别记录奇异值。每组72状态用中心差分独立核对J，全部控制行独立FK核对姿态和误差。

{verification}

## 轨迹与碰撞评价

{methods}

以逐段planning_log为准：非竖直段先尝试直连路线、边检查及实际五次命令网格预检；若直连受阻，算法才可能尝试RRT-Connect，不能仅因程序包含RRT而宣称运行用了RRT。竖直descend/lower按2mm路径求IK、0.001rad边检查并在线DLS／命令检查，无预先固定完整命令网格。非竖直关节边实际分辨率0.005rad。旧result汇总字段`exact_command_grid_preflight=False`不能概括全部段，0.001rad汇总也不能代替各段实际分辨率。

控制影子模型包含自身、地面、当前搬运件与其他构件，实际物理步按原碰撞定义检查。机器人2mm自碰撞／地面查询、其他构件50µm查询、物理定义外穿透100µm、允许夹持槽500µm接触、构件对／执行支撑200µm阈值均保留。计划搬运件不允许穿透；物理支撑与夹持接触按定义允许。碰撞0表示未触发定义外条件，不是无接触、正安全间距或连续时间形式化避碰证明；未记录全程最小几何间隙，不能补造间隙裕度。

## 力矩来源、采样与完整统计

本轮六组独立校准通过，结果在`feedback_calibration.json`。POSITION_CONTROL的getJointStates索引3保存原始电机反馈；本机构建4子步下相当于最后子步电机冲量／外部dt，乘4恢复最后子步等效力矩。外部240Hz样本不覆盖全部960Hz内部峰值，也不是4子步平均值。六轴转动关节单位N·m，夹爪直线关节单位N。传感器六维反力及辅助固定约束反馈另存，不与电机力矩相加；未独立标定辅助约束参考系或用它认证真实承载。

全程统计包含初始化、运动、闭爪、释放、等待、沉降；各轴峰值／RMS使用所有实际样本。RMS=√(Στ²/N)，不是仅持件片段；它包含原机器人自重、运动与接触／数值内环影响，不是纯72.6g载荷力矩。持件辅助固定约束按接触门控创建，实际质量与COM惯量始终加载，机器人通过约束接受载荷；这不是纯摩擦抓取，也未用空载逆动力学冒充持件记录。

{torque}

原始force参数六轴100N·m源自模型URDF，独立饱和实验在本机4子步下对应约400N·m最后子步等效数值限幅；夹爪命令1/3N对应约4/12N等效上限。保留既有控制设置，未据低于限幅的曲线推断厂家额定载荷、热安全或真实夹持正压力。

两组共同完成的连续任务前缀为**{a['common_completed_prefix_items']}件**。对比范围：{a['comparison_scope']}。共同工作量的六轴峰值／RMS见`common_workload_torque.csv`；每件放置后沉降的同阶段误差见`common_item_placement_comparison.csv`，与最终全结构误差明确分开。完整分阶段及件号×阶段统计分别保存在各工况`torque_by_phase.csv`及`torque_by_item_phase.csv`。

## 后续正式数值运行方案（主对话数值复核通过）

建议冻结**{recommended['recommended_condition']}**工况，补偿开关为`{choice}`，其余参数按本次manifest保持。选择依据是在所有已成功完成16件的方案中，优先降低当前定位装配任务的最大最终构件位置误差；该方案已通过主对话独立数值复核并被接受，复核证据见`../运行验证/B_第三阶段复核_2026-11-10/独立验收结果.json`。这是一项B数值方案取舍，不是所有指标的加权最优或A材料签核，也未修改共享启动器默认值。

{actual_tradeoff}

开启／关闭两组的位置、姿态和耗时差值已在前表逐项给出，力矩代价如下；正差表示开启后该指标增大，不能只列有利项。即使位置改善，只要姿态或某轴峰值／RMS增大，就属于权衡，不称为全面性能提升。若后续任务将姿态精度或特定轴负担列为优先目标，应重新按这些真实数据选择；更换结构／材料仍须复验。

{tradeoffs}

## 失败分析与局限

{failures}

A现已提供16件设计、转角和名义平地自重支承。本实验继续采用尚待A正式认可的候选材料，不将其写成最终签核。未验证真实制造强度、抗拔／侧连接、倾覆鲁棒性、月面非理想接触、真实感知误差或硬件驱动安全。没有增加无关敏感性试验；本轮至少一个冻结方案完成16件即满足本阶段数值实验验收条件，但全组报告／幻灯片／材料签核仍由相应负责人处理。

## 证据与复核入口

- `第三阶段结果摘要.json`为报告对话的机器读取入口；路径均相对本目录。
- `../运行验证/B_第三阶段_2026-11-10/experiment_manifest.json`记录两组命令、香港时间、退出码与成功状态；`frozen_source/`及资源SHA固定运行版本。
- 各工况`joint_full_trace.csv`为240Hz全部原始关节／夹爪／反力／约束数据；`b_control_trace.csv`约60Hz运动控制行；`trajectory.csv`20Hz当前构件底面位姿，`inventory_trace.csv`2Hz全部构件COM位姿；四者用途不同。
- 各工况`analysis_summary.json`、`actual_target_checks.csv`、`kinematic_trace.csv`、`TCP_endpoint_errors.csv`、`joint_command_tracking.csv`及力矩CSV支撑全部指标。
- `assembly.mp4`为本轮实时物理渲染，`evidence_audit.json`核对帧数／分辨率，`last_frame.png`来自真实末帧；没有插值或拼接旧检查点片段。
- 图表包括各组运动／力矩、限位／奇异值、命令跟踪与最终构件误差，及两组最终误差／共同工作量力矩对比。显示抽样不影响CSV全量峰值统计。
- `evidence_sha256.json`覆盖本阶段代码、结论及原始证据；分析脚本版本与运行源码分别保留。共享CHANGELOG／分工／AGENTS／清单由主对话据验收更新，本对话未提交、推送或发送组员消息。
'''
 (CODE/'第三阶段评价说明.md').write_text(text,encoding='utf8')
 m['analysis']={'complete':True,'summary_path':'../../B_第三阶段正式评价/第三阶段结果摘要.json','method_report_path':'../../B_第三阶段正式评价/第三阶段评价说明.md','detailed_control_model_freeze':'control_and_model_freeze.json','calibration':'feedback_calibration.json','robot_loaded_dynamics':'robot_loaded_dynamics.json','environment_binary_fingerprint':'environment_binary_fingerprint.json'};dump(OUT/'experiment_manifest.json',m)
 files=[f for directory in [OUT,CODE] for f in directory.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name not in ['evidence_sha256.json','publication_manifest.json','publication_check.json']]
 dump(OUT/'evidence_sha256.json',{f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files)})
 print('Report and SHA complete',len(files))
if __name__=='__main__':main()
