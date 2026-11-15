"""Independent C run audit. Does not modify physics or archived B evidence."""
import csv, json, hashlib, math, sys
from pathlib import Path
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'05_Project3_月面机器人装配'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(folder):
 r=read(folder/'result.json'); m=read(folder/'run_manifest.json'); n=r['requested_count']
 checks={}
 checks['success']=r['success'] and len(r['placed_items'])==n
 checks['scene']=r['body_count_min']==r['body_count_max']==19 and r['preloaded_count']==16
 checks['snapshots']=len(r['scene_snapshots'])==n*6 and all(s['obstacle_count']==15 and len(s['poses'])==16 for s in r['scene_snapshots'])
 checks['collisions']=len(r['collisions'])==0
 checks['planning']=len(r['planning_log'])==6*n and all(x['status']=='executed' for x in r['planning_log'])
 methods=Counter(x['method'] for x in r['planning_log'])
 attach=[e for e in r['events'] if e['phase']=='attach']
 checks['attach']=len(attach)==n and all(all(e['bilateral_contacts']) and e['instantaneous_displacement_m']==0 for e in attach)
 release=[e for e in r['events'] if e['phase']=='opened_before_detach']
 checks['release']=len(release)==n and all(e['stable_clear_samples']>=5 and not e['contacts_present'] and e['opening_m']>.0355 and e['linear_speed_m_s']<.002 for e in release)
 checks['runtime_sources']=all(sha(PROJECT/rel)==h for rel,h in m['source_hashes'].items())
 inventories=defaultdict(set)
 with (folder/'inventory_trace.csv').open(encoding='utf-8-sig') as f:
  for row in csv.DictReader(f): inventories[row['time_s']].add(int(row['item']))
 checks['inventory']=all(v==set(range(1,17)) for v in inventories.values()) and bool(inventories)
 count=0; peak=[0.]*6; squares=[0.]*6; continuous=True
 with (folder/'joint_full_trace.csv').open(encoding='utf-8-sig') as f:
  for count,row in enumerate(csv.DictReader(f),1):
   continuous &= int(row['step'])==count and abs(float(row['time_s'])-count/240)<1e-7
   for j in range(6):
    x=float(row[f'motor{j+1}_Nm'])*4;peak[j]=max(peak[j],abs(x));squares[j]+=x*x
 checks['telemetry']=continuous and count==r['telemetry_rows']==round(r['simulated_seconds']*240)
 checks['final']=len(r['final'])==n and all(f['position_error_m']<.003 and f['orientation_error_rad']<.05 and f['linear_speed_m_s']<.005 and f['lower_support_contacts']>0 for f in r['final'])
 b=read(PROJECT/'运行验证/B_第三阶段_2026-11-10/compensation_on/result.json')
 fields=['mass_kg','com_from_bottom_m','inertia_diagonal_about_com_kg_m2','sources','targets','source_yaws','target_yaws','physics_dt_s','physics_substeps','grasp_offset_compensation']
 def close(a,b):
  if isinstance(a,list):return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
  if isinstance(a,(int,float)):return abs(a-b)<1e-12
  return a==b
 checks['B_settings_match']=all(close(r[k],b[k][:n] if k in ['targets','target_yaws'] else b[k]) for k in fields)
 out={'checks':checks,'passed':all(checks.values()),'rows':count,'inventory_times':len(inventories),'planning_methods':dict(methods),'max_position_mm':max(f['position_error_m'] for f in r['final'])*1000,'max_orientation_deg':max(f['orientation_error_rad'] for f in r['final'])*180/math.pi,'seconds':r['simulated_seconds'],'release_escalations':sum(e['recovered_after_escalation'] for e in release),'torque_equivalent_peak_Nm':peak,'torque_equivalent_RMS_Nm':[math.sqrt(s/count) for s in squares],'scope':'240Hz sampled last internal substep equivalent; not 960Hz extrema'}
 (folder/'C_independent_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(out,ensure_ascii=False));assert out['passed'],checks
if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

