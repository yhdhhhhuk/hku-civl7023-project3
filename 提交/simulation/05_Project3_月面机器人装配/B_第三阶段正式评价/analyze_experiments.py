"""Stage 3: same-host paired evidence, full-sample statistics, failure-safe comparison."""
from pathlib import Path
import os,sys,csv,json,math,hashlib,collections,xml.etree.ElementTree as ET
os.environ.setdefault('MPLCONFIGDIR',os.path.join(__import__('tempfile').gettempdir(),'civl7023-matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];CODE=Path(__file__).resolve().parent;OUT=ROOT/'运行验证/B_第三阶段_2026-11-10'
sys.path[:0]=[str(ROOT),str(ROOT/'B_基础控制与雅可比'),str(ROOT/'B_关节与夹爪')]
from kinematics import Kinematics,pose,pose_error
from piper_robot import DEMO_POSE,URDF
KIN=Kinematics()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def csvwrite(p,rows):
 if not rows:return
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def csvread(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def numeric_log(p):
 # Streaming parse retains compact float arrays, not millions of Python strings.
 with p.open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f);fields=rd.fieldnames;labels={'phase','attached'};num=[x for x in fields if x not in labels]
  data=[];phases=[];attached=[]
  for row in rd:
   data.append([float(row[x]) for x in num]);phases.append(row['phase']);attached.append(row['attached']=='True')
 a=np.array(data);assert np.isfinite(a).all()
 return {name:a[:,j] for j,name in enumerate(num)},np.array(phases),np.array(attached)
def jacobian_batch(q):
 # FK/J is still evaluated at every recorded state; avoids per-state SVD overhead.
 n=len(q);J=np.empty((n,6,6));fk=np.empty((n,4,4))
 for i,qi in enumerate(q):fk[i],J[i]=KIN.evaluate(qi)
 singular=np.linalg.svd(np.einsum('ij,njk->nik',KIN.W,J),compute_uv=False)
 return fk,J,singular
def torque_stats(raw,t,items,phases,mask=None):
 if mask is None:mask=np.ones(len(t),dtype=bool)
 indices=np.flatnonzero(mask);rows=[]
 for j in range(6):
  a=raw[mask,j];idx=int(indices[np.argmax(abs(a))]);rows.append(dict(joint=j+1,samples=int(mask.sum()),duration_s=int(mask.sum())/240,raw_peak_abs_Nm=float(abs(a).max()),raw_RMS_Nm=float(np.sqrt(np.mean(a*a))),last_substep_equivalent_peak_abs_Nm=float(abs(a).max()*4),last_substep_equivalent_RMS_Nm=float(np.sqrt(np.mean(a*a))*4),peak_time_s=float(t[idx]),peak_item=int(items[idx]),peak_phase=str(phases[idx]),motor_force_API_argument_Nm=100,last_substep_equivalent_numeric_clamp_Nm=400))
 return rows
def nominal_targets():
 from C_仿真与装配.preloaded_tray_layout import tray_slots
 q=DEMO_POSE.copy();rows=[];order=[0,1,7,2,6,3,5,4]
 for i,slot in enumerate(tray_slots()):
  theta=order[i%8]*math.pi/4;target=[.26+.076*math.cos(theta),.03+.076*math.sin(theta),.022*(i//8)];yaw=(theta+math.pi)%math.pi-math.pi/2;src=slot['position'];sy=slot['yaw']
  for phase,pos,a in [('approach',[*src[:2],.082],sy),('descend',[*src[:2],.014],sy),('lift',[*src[:2],.082],sy),('transfer',[*target[:2],.082],yaw),('lower',[*target[:2],target[2]+(.0145 if i>=8 else .016)],yaw),('retreat',[*target[:2],.082],yaw)]:
   R=Rotation.from_euler('z',a).as_matrix()@np.diag([-1.,1.,-1.]);T=np.eye(4);T[:3,:3]=R;T[:3,3]=pos;ik=KIN.inverse(T,q);q=np.array(ik['q_rad']);d=KIN.diagnostics(KIN.jacobian(q))
   rows.append(dict(item=i+1,phase=phase,x_m=pos[0],y_m=pos[1],z_m=pos[2],yaw_rad=a,position_residual_m=ik['position_residual_m'],orientation_residual_rad=ik['orientation_residual_rad'],joint_margin_deg=float(np.rad2deg(np.minimum(q-KIN.lower,KIN.upper-q).min())),scaled_sigma_min=d['scaled_sigma_min'],scaled_condition=d['scaled_condition'],rank=d['rank'],**{f'q{j+1}_rad':float(v) for j,v in enumerate(q)}))
 assert len(rows)==96 and all(x['rank']==6 for x in rows)
 csvwrite(OUT/'nominal_96_targets.csv',rows)
 dump(OUT/'nominal_target_summary.json',dict(count=96,all_rank6=True,min_joint_margin_deg=min(r['joint_margin_deg'] for r in rows),min_scaled_sigma=min(r['scaled_sigma_min'] for r in rows),max_scaled_condition=max(r['scaled_condition'] for r in rows),characteristic_length_m=.3))

def analyze(condition):
 folder=OUT/condition;r=read(folder/'result.json');n,ph,attached=numeric_log(folder/'joint_full_trace.csv');t=n['time_s'];items=n['item'];steps=n['step'].astype(int)
 assert np.array_equal(steps,np.arange(1,len(t)+1)) and len(t)==r['telemetry_rows']==round(r['simulated_seconds']*240)
 assert np.max(abs(t-steps/240))<1e-10
 q=np.column_stack([n[f'q{i}_rad'] for i in range(1,7)]);dq=np.column_stack([n[f'dq{i}_rad_s'] for i in range(1,7)]);raw=np.column_stack([n[f'motor{i}_Nm'] for i in range(1,7)])
 arm_limits={j.get('name'):j.find('limit').attrib for j in ET.parse(URDF).getroot().findall('joint') if j.get('type')=='revolute'}
 velocity_limits=np.array([float(arm_limits[f'joint{i}']['velocity']) for i in range(1,7)])
 margin=np.rad2deg(np.minimum(q-KIN.lower,KIN.upper-q));assert margin.min()>0 and abs(raw).max()<=100+1e-6
 fk,J,sv=jacobian_batch(q);sigma=sv[:,-1];cond=sv[:,0]/sigma
 fdmax=0
 for idx in np.linspace(0,len(t)-1,72,dtype=int):
  eps=1e-6;fd=np.column_stack([pose_error(KIN.fk(q[idx]+np.eye(6)[j]*eps),KIN.fk(q[idx]-np.eye(6)[j]*eps))/(2*eps) for j in range(6)])
  fdmax=max(fdmax,float(abs(fd-J[idx]).max()))
 assert fdmax<1e-6
 stats=torque_stats(raw,t,items,ph);csvwrite(folder/'torque_full_run.csv',stats)
 phase_stats=[];item_phase=[]
 for phase in sorted(set(ph)):
  for row in torque_stats(raw,t,items,ph,ph==phase):phase_stats.append({'phase':phase,**row})
 for item in sorted(set(items.astype(int))):
  for phase in sorted(set(ph[items==item])):
   for row in torque_stats(raw,t,items,ph,(items==item)&(ph==phase)):item_phase.append({'item':item,'phase':phase,**row})
 csvwrite(folder/'torque_by_phase.csv',phase_stats);csvwrite(folder/'torque_by_item_phase.csv',item_phase)
 # Every external sample gets an independently recomputed FK/J diagnostic.
 csvwrite(folder/'kinematic_trace.csv',[dict(step=int(steps[i]),time_s=float(t[i]),item=int(items[i]),phase=str(ph[i]),minimum_joint_margin_deg=float(margin[i].min()),scaled_sigma_min=float(sigma[i]),scaled_condition=float(cond[i]),rank=int(np.sum(sv[i]>1e-8))) for i in range(len(t))])
 targetrows=[]
 for e in r['planning_log']:
  if 'goal_q' not in e:continue
  qi=np.array(e['goal_q']);R=Rotation.from_euler('z',e['yaw']).as_matrix()@np.diag([-1.,1.,-1.]);T=np.eye(4);T[:3,:3]=R;T[:3,3]=e['target'];err=pose_error(T,KIN.fk(qi));d=KIN.diagnostics(KIN.jacobian(qi))
  targetrows.append(dict(item=e['item'],phase=e['phase'],status=e['status'],position_residual_m=float(np.linalg.norm(err[:3])),orientation_residual_rad=float(np.linalg.norm(err[3:])),joint_margin_deg=float(np.rad2deg(np.minimum(qi-KIN.lower,KIN.upper-qi).min())),scaled_sigma_min=d['scaled_sigma_min'],scaled_condition=d['scaled_condition'],rank=d['rank']))
 assert all(x['position_residual_m']<1e-5 and x['orientation_residual_rad']<1e-4 for x in targetrows)
 csvwrite(folder/'actual_target_checks.csv',targetrows)
 trace=csvread(folder/'b_control_trace.csv');tt=np.array([float(x['time_s']) for x in trace]);trace_steps=np.rint(tt*240).astype(int)-1
 actual=np.array([[float(x[f'actual_{a}_m']) for a in 'xyz'] for x in trace]);target=np.array([[float(x[f'target_{a}_m']) for a in 'xyz'] for x in trace]);pe=np.linalg.norm(target-actual,axis=1)
 aq=Rotation.from_quat([[float(x[f'actual_quat_{a}']) for a in 'xyzw'] for x in trace]);tq=Rotation.from_quat([[float(x[f'target_quat_{a}']) for a in 'xyzw'] for x in trace]);oe=np.rad2deg((tq*aq.inv()).magnitude())
 pediff=float(abs(pe-[float(x['position_error_m']) for x in trace]).max());oediff=float(abs(oe-[float(x['orientation_error_deg']) for x in trace]).max());fkdiff=float(np.linalg.norm(fk[trace_steps,:3,3]-actual,axis=1).max())
 assert pediff<1e-10 and oediff<1e-4 and fkdiff<1e-8
 qtrace=np.array([[float(x[f'q{i}_rad']) for i in range(1,7)] for x in trace]);qcommand=np.array([[float(x[f'q{i}_command_rad']) for i in range(1,7)] for x in trace])
 qtracking=qtrace-qcommand
 command_fk=np.array([KIN.fk(qi) for qi in qcommand]);command_pe=np.linalg.norm(command_fk[:,:3,3]-actual,axis=1)
 command_oe=np.rad2deg((Rotation.from_matrix(command_fk[:,:3,:3])*aq.inv()).magnitude())
 command_stats=[dict(joint=j+1,samples=len(trace),joint_command_error_RMS_deg=float(np.rad2deg(np.sqrt(np.mean(qtracking[:,j]**2)))),joint_command_error_peak_abs_deg=float(np.rad2deg(abs(qtracking[:,j]).max()))) for j in range(6)]
 csvwrite(folder/'joint_command_tracking.csv',command_stats)
 # Compare quaternion FK orientation for all logged control states as well.
 fkangle=np.rad2deg((Rotation.from_matrix(fk[trace_steps,:3,:3])*aq.inv()).magnitude());assert fkangle.max()<1e-5
 moves=[]
 for e,mv in zip([x for x in r['planning_log'] if x['status']=='executed'],r['moves']):
  moves.append(dict(item=e['item'],phase=e['phase'],position_error_mm=mv['final_position_error_m']*1000,orientation_error_deg=mv['final_orientation_error_deg'],duration_s=mv['duration_s']))
 csvwrite(folder/'TCP_endpoint_errors.csv',moves)
 # Validate all completed release gates, and each attach's lack of displacement.
 diagnostics=read(folder/'release_diagnostics.json');releases=[x for x in r['events'] if x['phase']=='opened_before_detach'];attaches=[x for x in r['events'] if x['phase']=='attach']
 for e in releases:
  last=[x for x in diagnostics if x['item']==e['item'] and x['time_s']<=e['time_s']+1e-9][-5:]
  assert len(last)==5 and all(x['opening_m']>.0355 and not x['contacts_present'] and x['linear_speed_m_s']<.002 and x['angular_speed_rad_s']<.02 for x in last)
 assert all(all(x['bilateral_contacts']) and x['instantaneous_displacement_m']==0 for x in attaches)
 assert r['body_count_min']==r['body_count_max']==19 and all(x['created_at_physics_step']==0 for x in r['creation_audit'])
 payload=read(folder/'loaded_payload.json');manifest=read(OUT/'experiment_manifest.json');c=manifest['payload']
 assert payload['mass_kg']==c['mass_kg'] and np.allclose(payload['inertial_position_m'],c['centre_of_mass_in_geometry_frame_m'],atol=1e-14,rtol=0) and np.allclose(payload['inertia_diagonal_kg_m2'],np.diag(c['inertia_about_COM_expressed_in_geometry_axes_kg_m2']),atol=1e-14,rtol=0)
 final=r['final'] if isinstance(r['final'],list) else []
 final_position_formula_max_difference=0.
 if final:
  final_position_formula_max_difference=max(abs(float(np.linalg.norm(np.array(x['origin'])-x['target']))-x['position_error_m']) for x in final)
  assert final_position_formula_max_difference<1e-12
 inventory=csvread(folder/'inventory_trace.csv');last_inventory={}
 for x in inventory:last_inventory[int(x['item'])]=x
 inventory_crosscheck=[]
 for x in final:
  inv=last_inventory[x['item']];quat=[float(inv[a]) for a in ['qx','qy','qz','qw']];rot=Rotation.from_quat(quat);origin=np.array([float(inv[a]) for a in ['x','y','z']])-rot.apply(np.array(r['com_from_bottom_m']))
  inventory_crosscheck.append(dict(item=x['item'],sample_time_s=float(inv['time_s']),time_before_final_s=r['simulated_seconds']-float(inv['time_s']),position_error_mm=float(np.linalg.norm(origin-x['target'])*1000),orientation_error_deg=float((Rotation.from_euler('z',r['target_yaws'][x['item']-1]).inv()*rot).magnitude()*180/math.pi),position_difference_from_final_origin_mm=float(np.linalg.norm(origin-x['origin'])*1000)))
 csvwrite(folder/'last_inventory_pose_crosscheck.csv',inventory_crosscheck)
 if r['success']:
  assert not attached[ph=='final_settle'].any()
  assert len(final)==16 and len(releases)==16 and len(moves)==96 and not r['collisions']
  assert all(x['position_error_m']<.003 and x['orientation_error_rad']<.05 and x['linear_speed_m_s']<.005 and x['lower_support_contacts']>0 for x in final)
 csvwrite(folder/'final_component_errors.csv',[dict(item=x['item'],position_error_mm=x['position_error_m']*1000,orientation_error_deg=math.degrees(x['orientation_error_rad']),linear_speed_m_s=x['linear_speed_m_s'],lower_support_contacts=x['lower_support_contacts']) for x in final])
 methods=collections.Counter(x.get('method','missing') for x in r['planning_log'] if x['status']=='executed')
 correction=[dict(item=e['item'],correction_x_mm=e['tcp_xy_correction_m'][0]*1000,correction_y_mm=e['tcp_xy_correction_m'][1]*1000,magnitude_mm=float(np.linalg.norm(e['tcp_xy_correction_m'])*1000)) for e in r['events'] if e['phase']=='grasp_offset_compensation'];csvwrite(folder/'compensation_offsets.csv',correction)
 # Sensor wrench and grasp constraint are kept separate from generalized motor torques.
 constraint=np.column_stack([n['constraint_'+x] for x in ['Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm']]);assert np.max(abs(constraint[~attached]))==0
 executed_entries=[x for x in r['planning_log'] if x['status']=='executed']
 planning_detail=dict(command_grid_preflight_executed=sum(bool(x.get('command_preflight',False)) for x in executed_entries),vertical_IK_online_guard_executed=sum(x.get('method')=='cartesian_vertical_checked' for x in executed_entries),RRT_route_trials_attempted=sum(y.get('method')=='RRT_Connect' for x in r['planning_log'] for y in x.get('route_trials',[])),exact_command_grid_valid_trials=sum(y.get('command_grid_valid',False) for x in r['planning_log'] for y in x.get('route_trials',[])),failed_planning_entries=[x for x in r['planning_log'] if x['status']!='executed'])
 worst_sigma_index=int(np.argmin(sigma));worst_margin_index,worst_margin_joint=np.unravel_index(np.argmin(margin),margin.shape)
 summary=dict(minimum_sigma_location={'time_s':float(t[worst_sigma_index]),'item':int(items[worst_sigma_index]),'phase':str(ph[worst_sigma_index])},minimum_limit_margin_location={'time_s':float(t[worst_margin_index]),'item':int(items[worst_margin_index]),'phase':str(ph[worst_margin_index]),'joint':int(worst_margin_joint)+1},release_escalated_items=[x['item'] for x in releases if x['recovered_after_escalation']],release_max_force_API_N=max((x['force_limit_N'] for x in releases),default=None),final_position_formula_max_difference_m=final_position_formula_max_difference,last_inventory_crosscheck_time_note='Independent COM/quaternion reconstruction at last2Hz sample, not exact final instant; see last_inventory_pose_crosscheck.csv',URDF_velocity_limits_rad_s=velocity_limits.tolist(),URDF_velocity_violation_count=int(np.sum(abs(dq)>velocity_limits+1e-9)),joint_command_tracking=command_stats,command_FK_tracking_RMS_mm=float(np.sqrt(np.mean(command_pe**2))*1000),command_FK_tracking_peak_mm=float(command_pe.max()*1000),command_FK_tracking_RMS_deg=float(np.sqrt(np.mean(command_oe**2))),command_FK_tracking_peak_deg=float(command_oe.max()),planning_detail=planning_detail,condition=condition,success=r['success'],exit_code=r['exit_code'],completed_items=r['placed_items'],completed_count=len(r['placed_items']),moves_reached=len(moves),release_gates_verified=len(releases),attach_zero_jump_verified=len(attaches),simulated_seconds=r['simulated_seconds'],wall_seconds=r['wall_seconds'],rows=len(t),continuous_240Hz=True,phase_counts=dict(collections.Counter(ph)),all_control_rows_verified=len(trace),position_error_recompute_max_difference_m=pediff,orientation_error_recompute_max_difference_deg=oediff,all_control_FK_max_position_difference_m=fkdiff,all_control_FK_max_orientation_difference_deg=float(fkangle.max()),FD_Jacobian_72_samples_max_abs=fdmax,min_joint_margin_deg=float(margin.min()),max_joint_velocity_rad_s=float(abs(dq).max()),per_joint_min_margin_deg=margin.min(axis=0).tolist(),per_joint_max_velocity_rad_s=abs(dq).max(axis=0).tolist(),min_scaled_sigma=float(sigma.min()),max_scaled_condition=float(cond.max()),all_actual_samples_rank6=bool(np.all(sv[:,-1]>1e-8)),min_sigma_excluding_initialize=float(sigma[ph!='initialize'].min()),max_TCP_endpoint_position_mm=max(x['position_error_mm'] for x in moves),max_TCP_endpoint_orientation_deg=max(x['orientation_error_deg'] for x in moves),TCP_target_relative_motion_RMS_mm=float(np.sqrt(np.mean(pe*pe))*1000),TCP_target_relative_motion_peak_mm=float(pe.max()*1000),TCP_target_relative_motion_RMS_deg=float(np.sqrt(np.mean(oe*oe))),TCP_target_relative_motion_peak_deg=float(oe.max()),final_max_position_error_mm=max((x['position_error_m']*1000 for x in final),default=None),final_position_RMS_mm=float(np.sqrt(np.mean([x['position_error_m']**2 for x in final]))*1000) if final else None,final_max_orientation_error_deg=max((math.degrees(x['orientation_error_rad']) for x in final),default=None),final_orientation_RMS_deg=float(np.sqrt(np.mean([x['orientation_error_rad']**2 for x in final]))*180/math.pi) if final else None,torque=stats,planning_methods_actual=dict(methods),RRT_segments_executed=methods['RRT_Connect'],planning_status_counts=dict(collections.Counter(x['status'] for x in r['planning_log'])),execution_collisions=len(r['collisions']),collision_guard_failure=r['error'],scene_body_count=19,compensation_count=len(correction),max_compensation_mm=max((x['magnitude_mm'] for x in correction),default=0),reaction_wrench_units='raw API Fx,Fy,Fz N; Mx,My,Mz N*m, not motor effort',constraint_wrench_raw_peak_abs=abs(constraint).max(axis=0).tolist(),gripper_raw_motor_peak_abs_N=[float(abs(n['motor7_N']).max()),float(abs(n['motor8_N']).max())],gripper_last_substep_equivalent_peak_abs_N=[float(abs(n['motor7_N']).max()*4),float(abs(n['motor8_N']).max()*4)],actual_target_count=len(targetrows),actual_target_min_margin_deg=min(x['joint_margin_deg'] for x in targetrows),actual_target_min_sigma=min(x['scaled_sigma_min'] for x in targetrows),actual_target_max_condition=max(x['scaled_condition'] for x in targetrows))
 dump(folder/'analysis_summary.json',summary)
 # Compact derived signals permit cross-condition plots without re-reading huge logs.
 np.savez_compressed(folder/'derived_signals.npz',time=t,items=items,phase=ph,q=q,dq=dq,raw_torque=raw,sigma=sigma,condition=cond,min_margin=margin.min(axis=1),trace_time=tt,TCP_error_mm=pe*1000,TCP_error_deg=oe)
 plot_condition(folder,condition,t,q,dq,raw,sigma,margin.min(axis=1),tt,pe,oe,final,command_pe,command_oe)
 print(condition,json.dumps(summary,ensure_ascii=False),flush=True)
 return summary

def plot_condition(folder,condition,t,q,dq,raw,sigma,margin,tt,pe,oe,final,command_pe,command_oe):
 stride=max(1,len(t)//16000);fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True)
 for j in range(6):
  axs[0].plot(t[::stride],np.rad2deg(q[::stride,j]),label=f'J{j+1}',lw=.7);axs[1].plot(t[::stride],dq[::stride,j],lw=.7);axs[2].plot(t[::stride],4*raw[::stride,j],lw=.7)
 axs[0].legend(ncol=6);axs[0].set_ylabel('q (deg)');axs[1].set_ylabel('dq (rad/s)');axs[2].set_ylabel('Last-substep equivalent (N m)');axs[2].set_xlabel('Simulation time (s)');fig.suptitle(condition+' | candidate payload | lunar gravity | assisted grasp');fig.tight_layout();fig.savefig(folder/'joint_motion_torque.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True);axs[0].plot(t[::stride],margin[::stride]);axs[0].set_ylabel('Minimum joint margin (deg)');axs[1].plot(t[::stride],sigma[::stride]);axs[1].set_ylabel('Scaled minimum singular value');axs[1].set_xlabel('Simulation time (s)');fig.tight_layout();fig.savefig(folder/'limits_singularity.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True);axs[0].semilogy(tt,np.maximum(pe*1000,1e-7),lw=.5);axs[0].set_ylabel('TCP target-relative error (mm)');axs[1].semilogy(tt,np.maximum(oe,1e-7),lw=.5);axs[1].set_ylabel('TCP target-relative error (deg)');axs[1].set_xlabel('Simulation time (s)');fig.suptitle('Target changes produce normal transient error; endpoints reported separately');fig.tight_layout();fig.savefig(folder/'TCP_target_tracking.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True);axs[0].plot(tt,command_pe*1000,lw=.5);axs[0].set_ylabel('Command FK - actual TCP (mm)');axs[1].plot(tt,command_oe,lw=.5);axs[1].set_ylabel('Command FK - actual TCP (deg)');axs[1].set_xlabel('Simulation time (s)');fig.suptitle('Motor command tracking, separate from distance to motion endpoint');fig.tight_layout();fig.savefig(folder/'command_tracking.png',dpi=160);plt.close(fig)
 if final:
  fig,axs=plt.subplots(1,2,figsize=(11,4));ids=[x['item'] for x in final];axs[0].bar(ids,[x['position_error_m']*1000 for x in final]);axs[1].bar(ids,[math.degrees(x['orientation_error_rad']) for x in final]);axs[0].set_ylabel('Final component position error (mm)');axs[1].set_ylabel('Final component orientation error (deg)')
  for ax in axs:ax.set_xlabel('Component');ax.set_xticks(ids)
  fig.tight_layout();fig.savefig(folder/'final_component_errors.png',dpi=160);plt.close(fig)

if __name__=='__main__':
 if len(sys.argv)==1:nominal_targets()
 else:analyze(sys.argv[1])
