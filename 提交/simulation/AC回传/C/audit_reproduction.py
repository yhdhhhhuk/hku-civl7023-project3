"""Independent evidence checks for C reproduction; never modifies raw records."""
from pathlib import Path
import json,csv,math,hashlib,sys
root=Path(__file__).resolve().parents[2]
folder=Path(sys.argv[1]).resolve()
r=json.loads((folder/'result.json').read_text(encoding='utf8'))
assert r['success'] and r['exit_code']==0 and not r['collisions']
n=r['requested_count']; assert r['placed_items']==list(range(1,n+1))
assert len(r['moves'])==n*6 and all(x['status']=='reached' for x in r['moves'])
order=[0,1,7,2,6,3,5,4]
for i,target in enumerate(r['targets']):
 theta=order[i%8]*math.pi/4
 expected=[.26+.076*math.cos(theta),.03+.076*math.sin(theta),.022*(i//8)]
 assert max(abs(x-y) for x,y in zip(target,expected))<1e-12
comp=[x for x in r['events'] if x['phase']=='grasp_offset_compensation']
if r.get('grasp_offset_compensation'):
 assert len(comp)==n and all(math.hypot(*x['tcp_xy_correction_m'])<=.002 for x in comp)
assert r['payload_config']=='A-candidate' and r['preloaded_count']==16
candidate=json.loads((root/'05_Project3_月面机器人装配/A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json').read_text(encoding='utf8'))
loaded=json.loads((folder/'loaded_payload.json').read_text(encoding='utf8'))
assert abs(loaded['mass_kg']-candidate['mass_kg'])<1e-12
assert max(abs(x-y) for x,y in zip(loaded['inertial_position_m'],candidate['centre_of_mass_in_geometry_frame_m']))<1e-14
assert max(abs(loaded['inertia_diagonal_kg_m2'][i]-candidate['inertia_about_COM_expressed_in_geometry_axes_kg_m2'][i][i]) for i in range(3))<1e-14
assert loaded['geometry_origin_reconstruction_max_error_m']<1e-12
assert r['initial_scene_body_count']==r['body_count_min']==r['body_count_max']==19
assert all(x['created_at_physics_step']==0 for x in r['creation_audit'])
assert len(r['scene_snapshots'])==n*6 and all(x['obstacle_count']==15 for x in r['scene_snapshots'])
assert all(x['status']=='executed' for x in r['planning_log'])
a=[x for x in r['events'] if x['phase']=='attach'];assert len(a)==n
assert all(all(x['bilateral_contacts']) and x['instantaneous_displacement_m']==0 for x in a)
rel=[x for x in r['events'] if x['phase']=='opened_before_detach'];assert len(rel)==n
assert all(x['opening_m']>.0355 and not x['contacts_present'] and x['stable_clear_samples']>=5 for x in rel)
with (folder/'joint_full_trace.csv').open(encoding='utf-8-sig',newline='') as f:
 count=0
 for count,row in enumerate(csv.DictReader(f),1):
  assert int(row['step'])==count and abs(float(row['time_s'])-count/240)<1e-10
  assert all(math.isfinite(float(row[f'motor{j}_Nm'])) for j in range(1,7))
assert count==r['telemetry_rows']==round(r['simulated_seconds']*240)
with (folder/'inventory_trace.csv').open(encoding='utf-8-sig',newline='') as f:
 groups={}
 for row in csv.DictReader(f):groups.setdefault(row['time_s'],set()).add(int(row['item']))
assert all(v==set(range(1,17)) for v in groups.values())
for name,h in json.loads((folder/'run_manifest.json').read_text(encoding='utf8'))['source_hashes'].items():
 p=root/'05_Project3_月面机器人装配'/name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h,name
p=r['planning_log']
summary=dict(status='PASS',completed_items=n,telemetry_rows=count,inventory_samples=len(groups),scene_snapshots=len(r['scene_snapshots']),command_preflight_segments=sum(x.get('command_preflight',False) for x in p),vertical_segments=sum(x.get('method')=='cartesian_vertical_checked' for x in p),planner_methods={str(k):sum(x.get('method')==k for x in p) for k in set(x.get('method') for x in p)},max_position_error_mm=max(x['position_error_m'] for x in r['final'])*1000,max_orientation_error_deg=math.degrees(max(x['orientation_error_rad'] for x in r['final'])),release_escalations=sum(x['recovered_after_escalation'] for x in rel),source_hashes_match=True,nominal_targets_unchanged=True,grasp_offset_compensation=bool(r.get('grasp_offset_compensation')),maximum_xy_compensation_mm=max([math.hypot(*x['tcp_xy_correction_m'])*1000 for x in comp] or [0]),notes='Discrete evidence audit; not a continuous collision or structural safety proof.')
(folder/'C独立证据核对.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
