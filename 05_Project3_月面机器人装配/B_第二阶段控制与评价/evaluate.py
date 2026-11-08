"""Recompute target IK, log continuity, limits, Jacobians, and torque statistics."""
import csv,json,sys,math,os
os.environ.setdefault("MPLCONFIGDIR",os.path.join(__import__("tempfile").gettempdir(),"civl7023-matplotlib"))
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'B_基础控制与雅可比'),str(ROOT/'B_关节与夹爪')]
from kinematics import Kinematics,pose,pose_error
from piper_robot import DEMO_POSE
from C_仿真与装配.preloaded_tray_layout import tray_slots
OUT=ROOT/'运行验证/B_第二阶段_2026-11-04'
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def write_csv(path,rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def target_check():
 kin=Kinematics();q=DEMO_POSE.copy();rows=[]
 order=[0,1,7,2,6,3,5,4];slots=tray_slots()
 for i in range(16):
  sector=order[i%8];theta=sector*math.pi/4;target=[.26+.076*math.cos(theta),.03+.076*math.sin(theta),.022*(i//8)]
  yaw=(theta+math.pi)%math.pi-math.pi/2;src=slots[i]['position'];sy=slots[i]['yaw']
  for phase,pos,a in [('approach',[*src[:2],.082],sy),('descend',[*src[:2],.014],sy),('lift',[*src[:2],.082],sy),('transfer',[*target[:2],.082],yaw),('lower',[*target[:2],target[2]+(.0145 if i>=8 else .016)],yaw),('retreat',[*target[:2],.082],yaw)]:
   quat=Rotation.from_matrix(Rotation.from_euler('z',a).as_matrix()@np.diag([-1.,1.,-1.])).as_quat()
   T=pose(pos,quat);ik=kin.inverse(T,q);q=np.array(ik['q_rad']);diag=kin.diagnostics(kin.jacobian(q))
   row=dict(item=i+1,phase=phase,x_m=pos[0],y_m=pos[1],z_m=pos[2],yaw_rad=a,position_residual_m=ik['position_residual_m'],orientation_residual_rad=ik['orientation_residual_rad'],joint_margin_deg=float(np.rad2deg(np.minimum(q-kin.lower,kin.upper-q).min())),sigma_min=diag['scaled_sigma_min'],condition=diag['scaled_condition'],rank=diag['rank'])
   row.update({f'q{j+1}_rad':v for j,v in enumerate(q)});rows.append(row)
 write_csv(OUT/'全部96目标求解.csv',rows)
 save('目标核对摘要.json',dict(targets=len(rows),minimum_margin_deg=min(x['joint_margin_deg'] for x in rows),minimum_scaled_sigma=min(x['sigma_min'] for x in rows),maximum_scaled_condition=max(x['condition'] for x in rows),all_rank6=all(x['rank']==6 for x in rows),length_scale_m=.3))
 print('96 targets checked',flush=True)
def analyze(folder):
 out=OUT/folder; result=json.loads((out/'result.json').read_text())
 with (out/'joint_full_trace.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 steps=np.array([int(r['step']) for r in rows]);t=np.array([float(r['time_s']) for r in rows]);assert np.all(np.diff(steps)==1) and steps[0]==1 and np.allclose(np.diff(t),1/240,atol=1e-12,rtol=0)
 assert len(rows)==round(result['simulated_seconds']*240)==result['telemetry_rows']
 q=np.array([[float(r[f'q{i}_rad']) for i in range(1,7)] for r in rows]);dq=np.array([[float(r[f'dq{i}_rad_s']) for i in range(1,7)] for r in rows]);raw=np.array([[float(r[f'motor{i}_Nm']) for i in range(1,7)] for r in rows]);eff=raw*result['physics_substeps']
 assert np.isfinite(q).all() and np.isfinite(dq).all() and np.isfinite(raw).all()
 assert np.max(abs(raw))<=100+1e-6
 kin=Kinematics();margin=np.rad2deg(np.minimum(q-kin.lower,kin.upper-q));assert margin.min()>0
 phases={phase:sum(r['phase']==phase for r in rows) for phase in sorted(set(r['phase'] for r in rows))}
 expected={'initialize','approach','descend','close','lift','transfer','lower','release','retreat','settle','final_settle'};assert expected==set(phases)
 # Independent central finite differences verify analytical Jacobian at 60 executed states.
 fdmax=0.;sigma=[];condition=[]
 for k in np.linspace(0,len(q)-1,60,dtype=int):
  J=kin.jacobian(q[k]);eps=1e-6;Jfd=np.column_stack([pose_error(kin.fk(q[k]+np.eye(6)[j]*eps),kin.fk(q[k]-np.eye(6)[j]*eps))/(2*eps) for j in range(6)])
  fdmax=max(fdmax,float(np.max(np.abs(J-Jfd))))
 # Inspect every external sample for singularity, without claiming continuous certification.
 for qi in q:
  d=kin.diagnostics(kin.jacobian(qi));sigma.append(d['scaled_sigma_min']);condition.append(d['scaled_condition'])
 assert fdmax<1e-6
 stats=[]
 import xml.etree.ElementTree as ET
 from piper_robot import URDF
 joints={j.get('name'):j for j in ET.parse(URDF).getroot().findall('joint')}
 for j in range(6):
  idx=int(np.argmax(abs(eff[:,j])));limit=float(joints[f'joint{j+1}'].find('limit').get('effort'))
  stats.append(dict(joint=j+1,raw_peak_abs_Nm=float(abs(raw[:,j]).max()),last_substep_equivalent_peak_abs_Nm=float(abs(eff[:,j]).max()),last_substep_equivalent_RMS_Nm=float(np.sqrt(np.mean(eff[:,j]**2))),peak_time_s=t[idx],peak_item=int(rows[idx]['item']),peak_phase=rows[idx]['phase'],configured_motor_force_argument_Nm=limit,empirical_substep_equivalent_clamp_Nm=limit*4,minimum_limit_margin_deg=float(margin[:,j].min()),max_velocity_rad_s=float(abs(dq[:,j]).max())))
 write_csv(out/'六轴力矩统计.csv',stats)
 phase_stats=[]
 for phase in phases:
  mask=np.array([r['phase']==phase for r in rows])
  for j in range(6):phase_stats.append(dict(phase=phase,joint=j+1,samples=int(mask.sum()),peak_abs_last_substep_equivalent_Nm=float(abs(eff[mask,j]).max()),RMS_last_substep_equivalent_Nm=float(np.sqrt(np.mean(eff[mask,j]**2)))))
 write_csv(out/'分阶段六轴力矩.csv',phase_stats)
 actual_goals=[]
 for entry in result['planning_log']:
  qi=np.array(entry['goal_q']);d=kin.diagnostics(kin.jacobian(qi))
  actual_goals.append(dict(item=entry['item'],phase=entry['phase'],status=entry['status'],joint_margin_deg=float(np.rad2deg(np.minimum(qi-kin.lower,kin.upper-qi).min())),sigma_min=d['scaled_sigma_min'],condition=d['scaled_condition'],rank=d['rank']))
 write_csv(out/'实际执行目标限位与奇异性.csv',actual_goals)

 with (out/'b_control_trace.csv').open(encoding='utf-8-sig') as f:trace=list(csv.DictReader(f))
 actual_xyz=np.array([[float(r[f'actual_{a}_m']) for a in 'xyz'] for r in trace]);target_xyz=np.array([[float(r[f'target_{a}_m']) for a in 'xyz'] for r in trace])
 pe=np.linalg.norm(target_xyz-actual_xyz,axis=1)
 aq=Rotation.from_quat([[float(r[f'actual_quat_{a}']) for a in 'xyzw'] for r in trace]);tq=Rotation.from_quat([[float(r[f'target_quat_{a}']) for a in 'xyzw'] for r in trace])
 oe=np.rad2deg((tq*aq.inv()).magnitude())
 pe_diff=float(np.max(abs(pe-np.array([float(r['position_error_m']) for r in trace]))));oe_diff=float(np.max(abs(oe-np.array([float(r['orientation_error_deg']) for r in trace]))))
 assert pe_diff<1e-10 and oe_diff<1e-4
 fkmax=0
 for r in trace[::max(1,len(trace)//128)]:
  T=kin.fk([float(r[f'q{i}_rad']) for i in range(1,7)])
  fkmax=max(fkmax,float(np.linalg.norm(T[:3,3]-[float(r[f'actual_{a}_m']) for a in 'xyz'])))
 summary=dict(all_control_error_rows_recomputed=len(trace),position_error_recompute_max_difference_m=pe_diff,orientation_error_recompute_max_difference_deg=oe_diff,rows=len(rows),dt_s=1/240,continuous=True,phase_rows=phases,minimum_limit_margin_deg=float(margin.min()),minimum_scaled_sigma=float(min(sigma)),maximum_scaled_condition=float(max(x for x in condition if x is not None)),jacobian_FD_max_abs_error=fdmax,FK_logged_TCP_max_position_difference_m=fkmax,torque_statistics=stats,move_count=len(result['moves']),release_count=sum(e['phase']=='opened_before_detach' for e in result['events']),max_final_position_error_mm=1000*max(r['position_error_m'] for r in result['final']),max_final_orientation_error_deg=math.degrees(max(r['orientation_error_rad'] for r in result['final'])),max_move_endpoint_position_error_mm=1000*max(r['final_position_error_m'] for r in result['moves']),max_move_endpoint_orientation_error_deg=max(r['final_orientation_error_deg'] for r in result['moves']),success=result['success'],simulated_seconds=result['simulated_seconds'],wall_seconds=result['wall_seconds'])
 save(folder+'/分析摘要.json',summary)
 # Plot full externally sampled signals; display downsampled curve only.
 fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True);stride=max(1,len(t)//18000)
 for j in range(6):
  axs[0].plot(t[::stride],np.rad2deg(q[::stride,j]),label=f'J{j+1}',lw=.7);axs[1].plot(t[::stride],dq[::stride,j],lw=.7);axs[2].plot(t[::stride],eff[::stride,j],lw=.7)
 axs[0].legend(ncol=6);axs[0].set_ylabel('q (deg)');axs[1].set_ylabel('dq (rad/s)');axs[2].set_ylabel('Last-substep equivalent (N m)');axs[2].set_xlabel('Simulation time (s)');fig.suptitle('A candidate | assisted grasp | lunar gravity | external samples at 240 Hz')
 fig.tight_layout();fig.savefig(out/'joint_motion_torque.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(11,4));ids=[r['item'] for r in result['final']];axs[0].bar(ids,[r['position_error_m']*1000 for r in result['final']]);axs[1].bar(ids,[math.degrees(r['orientation_error_rad']) for r in result['final']]);axs[0].set_ylabel('Final component position error (mm)');axs[1].set_ylabel('Final component orientation error (deg)')
 for ax in axs:ax.set_xlabel('Component');ax.set_xticks(ids)
 fig.tight_layout();fig.savefig(out/'component_errors.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True)
 tt=[float(r['time_s']) for r in trace]
 axs[0].semilogy(tt,[max(1e-7,float(r['position_error_m'])*1000) for r in trace],lw=.6);axs[0].set_ylabel('TCP target error (mm)')
 axs[1].semilogy(tt,[max(1e-7,float(r['orientation_error_deg'])) for r in trace],lw=.6);axs[1].set_ylabel('TCP target error (deg)');axs[1].set_xlabel('Simulation time (s)')
 fig.suptitle('Target-relative transients include target changes; endpoint errors reported separately');fig.tight_layout();fig.savefig(out/'tcp_tracking_errors.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True);axs[0].plot(t[::stride],margin.min(axis=1)[::stride]);axs[0].set_ylabel('Minimum joint margin (deg)');axs[1].plot(t[::stride],np.array(sigma)[::stride]);axs[1].set_ylabel('Scaled minimum singular value');axs[1].set_xlabel('Simulation time (s)');fig.tight_layout();fig.savefig(out/'limits_singularity.png',dpi=160);plt.close(fig)
 print(folder,summary,flush=True)
if __name__=='__main__':
 if len(sys.argv)==1:target_check()
 else:analyze(sys.argv[1])
