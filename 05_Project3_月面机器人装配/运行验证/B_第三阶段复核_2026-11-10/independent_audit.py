"""Independent, read-only audit of stage-3 frozen experiments and raw evidence."""
from pathlib import Path
import csv, json, hashlib, math, collections, sys
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
RUNS = PROJECT/'运行验证/B_第三阶段_2026-11-10'
sys.path[:0] = [str(PROJECT/'B_基础控制与雅可比'),str(PROJECT/'B_关节与夹爪')]
from kinematics import Kinematics, pose_error

def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def csvrows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: yield from csv.DictReader(f)

def audit_run(folder):
    run=RUNS/folder;r=read(run/'result.json');start=read(run/'run_manifest.json')
    assert r['payload_config']=='A-candidate' and r['physics_substeps']==4
    assert r['body_count_min']==r['body_count_max']==19
    assert r['requested_count']==16 and r['preloaded_count']==16
    assert all(x['created_at_physics_step']==0 for x in r['creation_audit'])
    assert r['source_hash']==sha(PROJECT/'C_仿真与装配/run_preloaded_tray_assembly_fast.py')
    for rel,h in start['source_hashes'].items(): assert sha(PROJECT/rel)==h,rel
    payload=read(run/'loaded_payload.json');candidate=read(RUNS/'candidate_payload.json')
    assert abs(payload['mass_kg']-candidate['mass_kg'])<1e-14
    assert np.allclose(payload['inertial_position_m'],candidate['centre_of_mass_in_geometry_frame_m'],atol=1e-14,rtol=0)
    assert np.allclose(np.diag(payload['inertia_diagonal_kg_m2']),candidate['inertia_about_COM_expressed_in_geometry_axes_kg_m2'],atol=1e-14,rtol=0)
    assert payload['geometry_origin_reconstruction_max_error_m']<1e-12
    if r['success']:
        assert r['exit_code']==0 and len(r['placed_items'])==16 and len(r['moves'])==96
        assert all(x['status']=='reached' for x in r['moves']) and not r['collisions']
    else:
        assert r['exit_code']!=0 and r['error']
    release=read(run/'release_diagnostics.json')
    for e in r['events']:
        if e['phase']=='attach':assert all(e['bilateral_contacts']) and e['instantaneous_displacement_m']==0
        if e['phase']=='opened_before_detach':
            tail=[x for x in release if x['item']==e['item']][-5:]
            assert len(tail)==5
            assert all(x['opening_m']>.0355 and not x['contacts_present'] and x['linear_speed_m_s']<.002 and x['angular_speed_rad_s']<.02 for x in tail)
    corrections=[x for x in r['events'] if x['phase']=='grasp_offset_compensation']
    assert bool(corrections)==r['grasp_offset_compensation']
    for e in corrections:
        i=e['item']-1;R=Rotation.from_euler('z',r['target_yaws'][i]).as_matrix()@np.diag([-1.,1.,-1.])
        expected=-(R@e['tcp_frame_origin_offset_m'])[:2]
        assert np.linalg.norm(expected)<=.002 and np.allclose(expected,e['tcp_xy_correction_m'],atol=1e-14,rtol=0)
        assert e['nominal_target_m']==r['targets'][i]
    kin=Kinematics();peak=np.zeros(6);squares=np.zeros(6);speed=np.zeros(6);margin=np.full(6,np.inf)
    phases=collections.Counter();item_phases=collections.defaultdict(set);selected=[];count=0
    group={};prefix=hashlib.sha256();prefix_end=first_comp_time
    for x in csvrows(run/'joint_full_trace.csv'):
        count+=1;time=float(x['time_s']);assert int(x['step'])==count and abs(time-count/240)<1e-10
        q=np.array([float(x[f'q{i}_rad']) for i in range(1,7)])
        dq=np.array([float(x[f'dq{i}_rad_s']) for i in range(1,7)])
        tau=np.array([float(x[f'motor{i}_Nm']) for i in range(1,7)])
        assert np.isfinite(np.r_[q,dq,tau]).all()
        peak=np.maximum(peak,abs(tau));squares+=tau*tau;speed=np.maximum(speed,abs(dq))
        margin=np.minimum(margin,np.minimum(q-kin.lower,kin.upper-q))
        phases[x['phase']]+=1;item_phases[int(x['item'])].add(x['phase'])
        k=(int(x['item']),x['phase'])
        if k not in group:group[k]={'rows':0,'sum_sq':np.zeros(6),'peak':np.zeros(6)}
        group[k]['rows']+=1;group[k]['sum_sq']+=tau*tau;group[k]['peak']=np.maximum(group[k]['peak'],abs(tau))
        if count%2400==0:selected.append(q)
        if time<=prefix_end:prefix.update(json.dumps(x,sort_keys=True).encode())
    assert count==r['telemetry_rows']==round(r['simulated_seconds']*240) and margin.min()>0
    needed={'approach','descend','close','lift','transfer','lower','release','retreat','settle'}
    assert all(needed<=item_phases[i] for i in r['placed_items'])
    Jerr=0.;sample_sigma=[]
    for q in selected:
        eps=1e-6;fd=np.column_stack([pose_error(kin.fk(q+np.eye(6)[j]*eps),kin.fk(q-np.eye(6)[j]*eps))/(2*eps) for j in range(6)])
        Jerr=max(Jerr,float(abs(fd-kin.jacobian(q)).max()));sample_sigma.append(kin.diagnostics(kin.jacobian(q))['scaled_sigma_min'])
    assert Jerr<1e-6
    trace_count=0;pe_max=0.;oe_max=0.;fk_max=0.
    for x in csvrows(run/'b_control_trace.csv'):
        trace_count+=1
        xyz=np.array([float(x[f'actual_{a}_m']) for a in 'xyz']);target=np.array([float(x[f'target_{a}_m']) for a in 'xyz'])
        pe=float(np.linalg.norm(xyz-target));aq=Rotation.from_quat([float(x[f'actual_quat_{a}']) for a in 'xyzw']);tq=Rotation.from_quat([float(x[f'target_quat_{a}']) for a in 'xyzw'])
        oe=float(np.rad2deg((tq*aq.inv()).magnitude()))
        pe_max=max(pe_max,abs(pe-float(x['position_error_m'])));oe_max=max(oe_max,abs(oe-float(x['orientation_error_deg'])))
        if trace_count%200==0:
            fk=kin.fk([float(x[f'q{i}_rad']) for i in range(1,7)])
            fk_max=max(fk_max,float(np.linalg.norm(fk[:3,3]-xyz)))
    assert pe_max<1e-10 and oe_max<1e-4 and fk_max<1e-6
    final=r['final'] if isinstance(r['final'],list) else []
    for x in final:
        assert abs(np.linalg.norm(np.array(x['origin'])-x['target'])-x['position_error_m'])<1e-12
        if r['success']:assert x['position_error_m']<.003 and x['orientation_error_rad']<.05 and x['linear_speed_m_s']<.005 and x['lower_support_contacts']>0
    last_inventory={}
    for x in csvrows(run/'inventory_trace.csv'):last_inventory[int(x['item'])]=x
    inventory_delta=[]
    for x in final:
        inv=last_inventory[x['item']];R=Rotation.from_quat([float(inv['q'+a]) for a in 'xyzw'])
        origin=np.array([float(inv[a]) for a in 'xyz'])-R.apply(candidate['centre_of_mass_in_geometry_frame_m'])
        d=abs(float(np.linalg.norm(origin-x['target']))-x['position_error_m']);inventory_delta.append(d)
        assert d<1e-5,('final/inventory discrepancy',x['item'],d)
    target_count=0
    for e in r['planning_log']:
        if 'goal_q' not in e:continue
        goal=np.eye(4);goal[:3,3]=e['target'];goal[:3,:3]=Rotation.from_euler('z',e['yaw']).as_matrix()@np.diag([-1.,1.,-1.])
        err=pose_error(goal,kin.fk(e['goal_q']))
        assert np.linalg.norm(err[:3])<1e-5 and np.linalg.norm(err[3:])<1e-4
        target_count+=1
    if r['success']:assert target_count==96
    import imageio.v2 as imageio
    video=imageio.get_reader(run/'assembly.mp4');meta=video.get_meta_data();frames=video.count_frames()
    assert meta['fps']==5 and frames==count//48+1
    imageio.imwrite(HERE/(folder+'_last.png'),video.get_data(frames-1));video.close()
    return dict(actual_target_FK_count=target_count,final_inventory_error_difference_m=max(inventory_delta,default=None),success=r['success'],pieces=len(r['placed_items']),move_count=len(r['moves']),error=r['error'],rows=count,simulated_seconds=r['simulated_seconds'],phase_rows=dict(phases),raw_peak_Nm=peak.tolist(),last_substep_equivalent_peak_Nm=(peak*4).tolist(),last_substep_equivalent_RMS_Nm=(np.sqrt(squares/count)*4).tolist(),max_joint_speed_rad_s=speed.tolist(),minimum_limit_margin_deg=float(np.rad2deg(margin.min())),FD_samples=len(selected),FD_max_error=Jerr,FD_sample_min_scaled_sigma=min(sample_sigma),control_rows=trace_count,control_error_recompute_max_position_m=pe_max,control_error_recompute_max_orientation_deg=oe_max,FK_sample_max_error_m=fk_max,max_final_position_mm=max((x['position_error_m']*1000 for x in final),default=None),max_final_orientation_deg=max((math.degrees(x['orientation_error_rad']) for x in final),default=None),max_compensation_mm=max((np.linalg.norm(e['tcp_xy_correction_m'])*1000 for e in corrections),default=0),video_frames=frames,video_duration_s=meta['duration'],pre_compensation_trace_sha256=prefix.hexdigest()),group

manifest=read(RUNS/'experiment_manifest.json')
assert manifest['status']=='runs_finished'
for rel,h in {**manifest['source_hashes'],**manifest['resource_hashes']}.items():assert sha(PROJECT/rel)==h,rel
for rel,h in manifest['source_hashes'].items():assert sha(RUNS/'frozen_source'/rel)==h,rel
off=read(RUNS/'compensation_off/result.json');on=read(RUNS/'compensation_on/result.json')
first_comp_time=min(e['time_s'] for e in on['events'] if e['phase']=='grasp_offset_compensation')
for key in ['initial_inventory','targets','target_yaws','sources','source_yaws','physics_substeps','physics_dt_s','mass_kg','com_from_bottom_m','inertia_diagonal_about_com_kg_m2','release_helper_sha256','self_collision_ignored_pairs']:
    assert off[key]==on[key],key
for name in ['compensation_off','compensation_on']:
    cmd=read(RUNS/name/'run_manifest.json')['argv'][:]
    pos=cmd.index('--output');del cmd[pos:pos+2]
    if '--compensate-grasp-offset' in cmd:cmd.remove('--compensate-grasp-offset')
    if name=='compensation_off':old_cmd=cmd
    else:assert cmd==old_cmd
summary={};groups={}
for name in ['compensation_off','compensation_on']:summary[name],groups[name]=audit_run(name)
assert any(x['success'] for x in summary.values())
assert summary['compensation_off']['pre_compensation_trace_sha256']==summary['compensation_on']['pre_compensation_trace_sha256']
common_items=set(off['placed_items'])&set(on['placed_items'])
common_stats={}
for name,group in groups.items():
    eligible=[g for (i,phase),g in group.items() if i in common_items and phase not in ['initialize','final_settle']]
    N=sum(g['rows'] for g in eligible);ss=sum((g['sum_sq'] for g in eligible),np.zeros(6))
    common_stats[name]={'items':sorted(common_items),'rows':N,'last_substep_equivalent_RMS_Nm':(4*np.sqrt(ss/N)).tolist()}
summary.update(passed=True,one_switch_same_initial_state=True,same_pre_compensation_raw_trace=True,source_hash_count=len(manifest['source_hashes']),resource_hash_count=len(manifest['resource_hashes']),common_completed_items_torque=common_stats)
(HERE/'独立验收结果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
