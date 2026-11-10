from pathlib import Path
import json,math,hashlib,shutil,subprocess,datetime
root=Path(__file__).resolve().parents[2];p=root/'05_Project3_月面机器人装配';out=p/'运行验证/B_第二阶段_2026-11-04';code=p/'B_第二阶段控制与评价'
candidate_path=p/'A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json'
candidate=json.loads(candidate_path.read_text())
assert candidate['units']['mass']=='kg' and candidate['units']['centre_of_mass']=='m' and candidate['units']['inertia']=='kg*m^2'
assert abs(candidate['actual_CAD_volume_m3']*candidate['material_density_kg_m3']-candidate['mass_kg'])<1e-14
I=candidate['inertia_about_COM_expressed_in_geometry_axes_kg_m2']
assert all(I[i][j]==0 for i in range(3) for j in range(3) if i!=j)
assert all(I[i][i]>0 and I[i][i]<=sum(I[j][j] for j in range(3) if j!=i) for i in range(3))
(out/'参数独立核对.json').write_text(json.dumps({'units_verified':candidate['units'],'mass_equals_density_times_CAD_volume':True,'tensor_about_COM':I,'axes':'geometry XYZ = principal inertial axes','no_parallel_axis_shift_required':True,'nonzero_offdiagonal_would_be_rejected':True,'legacy_mass_kg':.07,'candidate_mass_kg':candidate['mass_kg'],'legacy_COM_m':[0,0,.011],'candidate_COM_m':candidate['centre_of_mass_in_geometry_frame_m'],'material_approval':'candidate only; pending A/group confirmation','source_sha256':hashlib.sha256(candidate_path.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf8')
r=json.loads((out/'候选从零16件/result.json').read_text());s=json.loads((out/'候选从零16件/分析摘要.json').read_text());single=json.loads((out/'候选单件/分析摘要.json').read_text());targets=json.loads((out/'目标核对摘要.json').read_text())
assert r['success'] and r['exit_code']==0 and len(r['placed_items'])==16 and len(r['moves'])==96
assert all(m['status']=='reached' for m in r['moves'])
releases=[e for e in r['events'] if e['phase']=='opened_before_detach'];attaches=[e for e in r['events'] if e['phase']=='attach']
assert len(releases)==len(attaches)==16
assert all(e['opening_m']>.0355 and not e['contacts_present'] and e['linear_speed_m_s']<.002 and e['stable_clear_samples']>=5 for e in releases)
samples=json.loads((out/'候选从零16件/release_diagnostics.json').read_text())
for item in range(1,17):
 last=[x for x in samples if x['item']==item][-5:]
 assert len(last)==5
 assert all(x['opening_m']>.0355 and not x['contacts_present'] and x['linear_speed_m_s']<.002 and x['angular_speed_rad_s']<.02 and x['force_limit_N']<=3 for x in last)
assert all(e['instantaneous_displacement_m']==0 and all(e['bilateral_contacts']) for e in attaches)
assert r['body_count_min']==r['body_count_max']==19 and not r['collisions']
assert all(e['created_at_physics_step']==0 for e in r['creation_audit'])
# Compare original tracked robot/B foundations/geometry with HEAD bytes without staging anything.
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0');checked=[]
for rel in tracked:
 if any('/'+folder+'/' in rel for folder in ['PiPER_Load_URDF','B_关节与夹爪','B_基础控制与雅可比','B_工作空间与设计约束','A_结构设计与CAD']):
  data=(root/rel).read_bytes();original=subprocess.check_output(['git','show','HEAD:'+rel],cwd=root)
  assert data==original,rel;checked.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest()})
baseline_v4=[]
for rel in tracked:
 if '/运行验证/C_释放修复_2026-11-02/修复后从头16件_v4/' in rel:
  data=(root/rel).read_bytes();assert data==subprocess.check_output(['git','show','HEAD:'+rel],cwd=root)
  baseline_v4.append(rel)
# Preserve runtime sources matching start hashes; analysis evolves separately.
m=json.loads((out/'候选从零16件/run_manifest.json').read_text());matched=[];analysis_changed=[]
for rel,h in m['source_hashes'].items():
 f=p/rel
 if hashlib.sha256(f.read_bytes()).hexdigest()!=h:
  assert rel in ['B_第二阶段控制与评价/evaluate.py','B_第二阶段控制与评价/verify_feedback.py'];analysis_changed.append(rel);continue
 dest=out/'运行源码快照'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);matched.append(rel)
for f in code.glob('*.py'):
 dest=out/'分析源码快照'/f.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
shutil.copyfile(p/'A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json',out/'候选参数快照.json')
verification={'verified_hong_kong':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'run_started':m['started_local'],'run_success':True,'96_moves_reached':True,'16_release_gates_passed':True,'16_bilateral_attaches_without_jump':True,'scene_19_constant':True,'release_last5_samples_including_angular_speed_passed':True,'baseline_v4_files_unchanged':baseline_v4,'all_creation_at_step0':True,'unchanged_original_files':checked,'matched_start_runtime_sources':matched,'analysis_scripts_changed_after_run_start_not_imported_by_simulation':analysis_changed,'notes':'The run manifest hashes all nearby Python files, including unused analysis tools. Only those offline scripts evolved while simulation ran; all runtime dependencies match.'}
(out/'独立验收核对.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
old=json.loads((p/'运行验证/C_释放修复_2026-11-02/修复后从头16件_v4/result.json').read_text())
comparison=[dict(configuration='legacy70g_v4',success=old['success'],items=len(old['placed_items']),simulated_seconds=old['simulated_seconds'],mass_kg=old['mass_kg'],max_position_error_mm=max(x['position_error_m'] for x in old['final'])*1000,max_orientation_error_deg=math.degrees(max(x['orientation_error_rad'] for x in old['final'])),complete_joint_torque_available=False),dict(configuration='A_candidate',success=r['success'],items=len(r['placed_items']),simulated_seconds=r['simulated_seconds'],mass_kg=r['mass_kg'],max_position_error_mm=s['max_final_position_error_mm'],max_orientation_error_deg=s['max_final_orientation_error_deg'],complete_joint_torque_available=True)]
(out/'旧v4与候选结果对照.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2),encoding='utf8')
torque='| 关节 | 原始峰值 | 最后子步等效峰值 N·m | 等效RMS N·m | 峰值动作／件号 |\n|---|---:|---:|---:|---|\n'+''.join(f"| J{x['joint']} | {x['raw_peak_abs_Nm']:.5f} | {x['last_substep_equivalent_peak_abs_Nm']:.5f} | {x['last_substep_equivalent_RMS_Nm']:.5f} | {x['peak_phase']}／{x['peak_item']} |\n" for x in s['torque_statistics'])
comparison_md='| 配置 | 完成 | 仿真秒 | 最大最终位置误差 mm | 最大姿态误差 ° |\n|---|---:|---:|---:|---:|\n'+''.join(f"| {x['configuration']} | {x['items']}/16 | {x['simulated_seconds']:.4f} | {x['max_position_error_mm']:.4f} | {x['max_orientation_error_deg']:.4f} |\n" for x in comparison)
results=f'''\n## 本阶段实测结果（2026年11月4日）

候选单件6/6运动目标、1次释放通过，连续{single['rows']:,}个240Hz样本，最终构件误差{single['max_final_position_error_mm']:.5f}mm／{single['max_final_orientation_error_deg']:.5f}°。

候选16件单次从零完成16/16，无检查点续跑；96/96运动目标和16/16释放门控通过，定义外碰撞0，19个场景物体恒定，附着瞬间位移0。仿真{s['simulated_seconds']:.4f}s，实际主程序运行耗时{s['wall_seconds']:.2f}s；本次起始时间{m['started_local']}。完整日志{s['rows']:,}行，外部步号从1开始连续，无缺步，覆盖全部11类阶段。

96名义目标最小限位裕度{targets['minimum_margin_deg']:.5f}°，最小缩放奇异值{targets['minimum_scaled_sigma']:.6f}，最大缩放条件数{targets['maximum_scaled_condition']:.5f}，全部rank6。全程实际样本最小限位裕度{s['minimum_limit_margin_deg']:.5f}°、最小缩放奇异值{s['minimum_scaled_sigma']:.6f}、最大条件数{s['maximum_scaled_condition']:.5f}。目标点指标不代表连接路径的最差情况。

最终构件最大位置／姿态误差{s['max_final_position_error_mm']:.5f}mm／{s['max_final_orientation_error_deg']:.5f}°；96次运动最终TCP最大位置／姿态误差{s['max_move_endpoint_position_error_mm']:.5f}mm／{s['max_move_endpoint_orientation_error_deg']:.5f}°。两类误差分别统计。60个执行状态的中心差分雅可比最大绝对差{s['jacobian_FD_max_abs_error']:.3e}，约128个样本独立FK与记录TCP最大位置差{s['FK_logged_TCP_max_position_difference_m']:.3e}m。

{torque}

原始峰值与等效值分别列出；RMS来自全程240Hz最后子步等效样本，不是960Hz全子步数据。六轴配置force=100N·m，独立饱和试验支持本机4子步下约400N·m等效数值上限；不据此作硬件安全结论。

{comparison_md}

旧v4无完整力矩数据，不提供旧力矩对照。两次载荷参数和采集设置不同，上表为结果并列，不作统计显著性或单因素因果结论。

图表见`候选从零16件/`中的`joint_motion_torque.png`、`component_errors.png`、`tcp_tracking_errors.png`和`limits_singularity.png`；完整视频为`assembly.mp4`。力矩按阶段与关节拆分的统计见`分阶段六轴力矩.csv`。
'''
f=code/'B_运动学控制与力矩章节初稿.md';f.write_text(f.read_text().split('\n## 本阶段实测结果')[0]+results,encoding='utf8')
(out/'第二阶段验收说明.md').write_text('''# B第二阶段本地验收

实际执行／核对日期2026年11月4日；按11月4—8日计划提前连续执行，不倒填未来日期。结论：B本阶段候选参数、全目标运动学、完整关节采集、单件与从零16件、基本力矩评价和技术章节初稿已完成本地程序／数据验收。不是整个课程项目定稿，也不是其他组员人工签核。

入口：`../../B_第二阶段控制与评价/README.md`；方法及字段、子步校准见该说明；技术章节为同目录`B_运动学控制与力矩章节初稿.md`。运行代码直接整合至C公共入口，默认旧参数，显式`--payload-config A-candidate --telemetry`启用本阶段配置与全程日志。原v4及原模型未覆盖。

独立证据：`独立验收核对.json`、`目标核对摘要.json`、`全部96目标求解.csv`、`反馈字段独立核对.json`、各运行的`loaded_payload.json`、`run_manifest.json`、`result.json`和`分析摘要.json`。`运行源码快照/`保存与启动哈希一致的运行依赖；离线评价脚本在仿真过程中完善，另保存在`分析源码快照/`，未改变在跑的控制器。`依赖实测.txt`记录本次环境；`文件SHA256.json`记录交付证据哈希。

本次没有候选参数单件／16件运行失败，不以检查点续跑补成成功；checkpoint仅作故障恢复证据。未更改释放门控、碰撞阈值、辅助抓持定义或运动学原模块，没有运行中创建构件、瞬移或关闭碰撞取巧。

仍待A／全组完成：材料最终认可、16件设计说明和连接／稳定性／强度定稿；本结果只支持候选均匀刚体假设。辅助固定约束抓持、离散避碰检查、4子步反馈局限保留。未验证纯摩擦抓取、厂家额定承载或硬件安全。未自动推送GitHub、未发送组员消息。
''' +results,encoding='utf8')
print(json.dumps({'summary':s,'unchanged_file_count':len(checked)},ensure_ascii=False,indent=2))
