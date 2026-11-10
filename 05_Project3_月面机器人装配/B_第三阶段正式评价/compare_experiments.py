"""Build machine-readable paired summary and fair common-workload comparison."""
from pathlib import Path
import sys,json,hashlib,math,csv,os
os.environ.setdefault('MPLCONFIGDIR',os.path.join(__import__('tempfile').gettempdir(),'civl7023-matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_experiments import OUT,CODE,ROOT,read,dump,csvwrite,torque_stats

def compare():
 manifest=read(OUT/'experiment_manifest.json');assert len(manifest['conditions'])==2 and manifest['status']=='runs_finished'
 ids=['compensation_off','compensation_on'];summaries={key:read(OUT/key/'analysis_summary.json') for key in ids};results={key:read(OUT/key/'result.json') for key in ids}
 for key,r in results.items():
  assert r['payload_config']=='A-candidate' and r['physics_substeps']==4 and r['contact_breaking_relative_factor']==1e-5
  assert r['grasp_offset_compensation']==(key=='compensation_on')
  provenance=read(OUT/key/'run_manifest.json');assert provenance['source_hashes']==manifest['source_hashes']
  assert provenance['candidate_sha256']==manifest['resource_hashes']['A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json']
 for field in ['mass_kg','com_from_bottom_m','inertia_diagonal_about_com_kg_m2','sources','source_yaws','targets','target_yaws','physics_dt_s','physics_substeps','contact_breaking_relative_factor','release_force_stages_N','gripper_force_limit_N_per_finger','self_collision_ignored_pairs','source_hash']:
  assert results[ids[0]][field]==results[ids[1]][field],field
 assert all(x['all_frozen_files_unchanged_after_run'] for x in manifest['conditions'])
 common=set(summaries[ids[0]]['completed_items'])&set(summaries[ids[1]]['completed_items']);k=0
 while k+1 in common:k+=1
 both_success=all(s['success'] for s in summaries.values());common_torque=[]
 for key in ids:
  d=np.load(OUT/key/'derived_signals.npz');mask=(d['items']<=k)
  if not both_success:mask&=d['phase']!='final_settle'
  if k:
   stats=torque_stats(d['raw_torque'],d['time'],d['items'],d['phase'],mask)
   for row in stats:common_torque.append({'condition':key,'common_prefix_items':k,'include_final_settle':both_success,**row})
 csvwrite(OUT/'common_workload_torque.csv',common_torque)
 immediate=[]
 for item in range(1,k+1):
  row={'item':item}
  for key in ids:row[key+'_immediate_after_settle_position_error_mm']=next(x['position_error_m']*1000 for x in results[key]['item_results'] if x['item']==item)
  row['on_minus_off_mm']=row['compensation_on_immediate_after_settle_position_error_mm']-row['compensation_off_immediate_after_settle_position_error_mm'];immediate.append(row)
 csvwrite(OUT/'common_item_placement_comparison.csv',immediate)
 scalar_rows=[]
 for key,s in summaries.items():
  scalar_rows.append({name:s[name] for name in ['condition','success','completed_count','moves_reached','release_gates_verified','simulated_seconds','wall_seconds','rows','final_max_position_error_mm','final_position_RMS_mm','final_max_orientation_error_deg','final_orientation_RMS_deg','max_TCP_endpoint_position_mm','max_TCP_endpoint_orientation_deg','command_FK_tracking_RMS_mm','command_FK_tracking_peak_mm','min_joint_margin_deg','max_joint_velocity_rad_s','min_scaled_sigma','max_scaled_condition','execution_collisions','RRT_segments_executed']})
 csvwrite(OUT/'condition_summary.csv',scalar_rows)
 deltas={}
 if both_success:
  for field in ['final_max_position_error_mm','final_position_RMS_mm','final_max_orientation_error_deg','final_orientation_RMS_deg','max_TCP_endpoint_position_mm','command_FK_tracking_RMS_mm','simulated_seconds','wall_seconds']:
   off=summaries[ids[0]][field];on=summaries[ids[1]][field];deltas[field]={'off':off,'on':on,'on_minus_off':on-off,'relative_change_percent':(on/off-1)*100 if off else None}
  finalcmp=[]
  for a,b in zip(results[ids[0]]['final'],results[ids[1]]['final']):
   finalcmp.append(dict(item=a['item'],off_position_mm=a['position_error_m']*1000,on_position_mm=b['position_error_m']*1000,off_orientation_deg=math.degrees(a['orientation_error_rad']),on_orientation_deg=math.degrees(b['orientation_error_rad'])))
  csvwrite(OUT/'final_component_comparison.csv',finalcmp)
  fig,axs=plt.subplots(1,2,figsize=(12,4));x=np.arange(1,17)
  for ax,a,b,ylabel in [(axs[0],'off_position_mm','on_position_mm','Final component position error (mm)'),(axs[1],'off_orientation_deg','on_orientation_deg','Final component orientation error (deg)')]:
   ax.bar(x-.18,[r[a] for r in finalcmp],.36,label='Compensation off');ax.bar(x+.18,[r[b] for r in finalcmp],.36,label='Compensation on');ax.set_ylabel(ylabel);ax.set_xlabel('Component');ax.set_xticks(x)
  axs[0].legend();fig.tight_layout();fig.savefig(OUT/'comparison_final_errors.png',dpi=170);plt.close(fig)
 if common_torque:
  fig,axs=plt.subplots(1,2,figsize=(12,4));x=np.arange(1,7)
  for ax,field,label in [(axs[0],'last_substep_equivalent_peak_abs_Nm','Last-substep equivalent peak (N m)'),(axs[1],'last_substep_equivalent_RMS_Nm','Last-substep equivalent RMS (N m)')]:
   for key,shift in zip(ids,[-.18,.18]):ax.bar(x+shift,[r[field] for r in common_torque if r['condition']==key],.36,label=key)
   ax.set_xticks(x);ax.set_xlabel('Joint');ax.set_ylabel(label)
  axs[0].legend();fig.suptitle(f'Matched completed workload: first {k} components');fig.tight_layout();fig.savefig(OUT/'comparison_common_torque.png',dpi=170);plt.close(fig)
 failures={key:dict(error=s['collision_guard_failure'],completed_items=s['completed_items'],last_planning_entry=results[key]['planning_log'][-1] if results[key]['planning_log'] else None) for key,s in summaries.items() if not s['success']}
 successful=[key for key in ids if summaries[key]['success']]
 assert successful
 selected=min(successful,key=lambda key:summaries[key]['final_max_position_error_mm'])
 recommendation={'recommended_condition':selected,'compensate_grasp_offset':selected=='compensation_on','basis':'Among complete16-piece successes, prioritize maximum final component position error for the current positioning/assembly task; explicitly retain angular-error and torque tradeoffs, no universal performance dominance claim','scope':'B本阶段已接受的正式数值方案，主对话独立数值复核通过；非A材料签核、硬件安全认证或全组最终交付确认','parent_review_evidence':'../运行验证/B_第三阶段复核_2026-11-10/独立验收结果.json','command_switch':'--compensate-grasp-offset' if selected=='compensation_on' else 'omit --compensate-grasp-offset'}
 torque_tradeoff=[]
 if both_success:
  for x,y in zip(off_torque:=summaries[ids[0]]['torque'],on_torque:=summaries[ids[1]]['torque']):
   torque_tradeoff.append(dict(joint=x['joint'],off_peak_Nm=x['last_substep_equivalent_peak_abs_Nm'],on_peak_Nm=y['last_substep_equivalent_peak_abs_Nm'],on_minus_off_peak_Nm=y['last_substep_equivalent_peak_abs_Nm']-x['last_substep_equivalent_peak_abs_Nm'],off_RMS_Nm=x['last_substep_equivalent_RMS_Nm'],on_RMS_Nm=y['last_substep_equivalent_RMS_Nm'],on_minus_off_RMS_Nm=y['last_substep_equivalent_RMS_Nm']-x['last_substep_equivalent_RMS_Nm']))
 csvwrite(OUT/'paired_torque_tradeoffs.csv',torque_tradeoff)
 answer={'recommendation':recommendation,'paired_torque_tradeoffs':torque_tradeoff,'schema_version':1,'experiment_date_HK':'2026-11-10','git_head':manifest['git_head'],'manifest_path':'../运行验证/B_第三阶段_2026-11-10/experiment_manifest.json','status':'analysis_complete','same_host_same_source_verified':True,'only_condition_switch':'--compensate-grasp-offset','conditions':summaries,'common_completed_prefix_items':k,'comparison_scope':'Both entire from-zero 16-component tasks including initialization/final settle' if both_success else f'Only first {k} completed component tasks including initialization, excluding final_settle; unequal incomplete full-run RMS not treated as comparable','paired_deltas_if_both_success':deltas,'failures':failures,'feedback_calibration_path':'../运行验证/B_第三阶段_2026-11-10/feedback_calibration.json','nominal_target_summary':read(OUT/'nominal_target_summary.json'),'files':{'condition_summary_csv':'../运行验证/B_第三阶段_2026-11-10/condition_summary.csv','common_torque_csv':'../运行验证/B_第三阶段_2026-11-10/common_workload_torque.csv','common_item_comparison':'../运行验证/B_第三阶段_2026-11-10/common_item_placement_comparison.csv','evidence_sha256':'../运行验证/B_第三阶段_2026-11-10/evidence_sha256.json'},'interpretation_limits':['One run per condition: no statistical reliability or repeatability claim','Candidate uniform rigid material, not final A material approval','Assisted fixed-constraint grasp, not pure friction grasp','Compensation reads ideal simulated poses after lift; not real vision/sensing','Only transfer/lower XY changed; nominal target and retreat XY unchanged','240Hz last-substep equivalent motor effort: not all960Hz extrema or interval mean','Model motor limits not manufacturer rated capacity; no hardware safety claim','Discrete edge/command/contact checks not continuous-time collision proof']}
 assert any(s['success'] for s in summaries.values()),'No condition passed16; diagnose before acceptance'
 dump(CODE/'第三阶段结果摘要.json',answer)
 print(json.dumps({'completed':[summaries[x]['completed_count'] for x in ids],'common_prefix':k,'deltas':deltas},ensure_ascii=False,indent=2))
 return answer
if __name__=='__main__':compare()
