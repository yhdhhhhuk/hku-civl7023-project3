"""Freeze runtime evidence, then run the sole compensation switch serially."""
from pathlib import Path
import subprocess,sys,json,hashlib,platform,datetime,shutil,time
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT/'05_Project3_月面机器人装配'
OUT=PROJECT/'运行验证/B_第三阶段_2026-11-10';OUT.mkdir(parents=True,exist_ok=True)
CODE=PROJECT/'B_第三阶段正式评价';STAMP=lambda:datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(m):(OUT/'experiment_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
if (OUT/'experiment_manifest.json').exists():raise SystemExit('Refusing to overwrite existing experiment manifest')
folders=['B_关节与夹爪','B_基础控制与雅可比','B_第二阶段控制与评价','C_仿真与装配']
source_files=[f for d in folders for f in (PROJECT/d).glob('*.py')]
resources=[f for d in ['PiPER_Load_URDF','B_工作空间与设计约束/构件模型'] for f in (PROJECT/d).rglob('*') if f.is_file() and f.name!='.DS_Store' and '__pycache__' not in f.parts]
candidate=PROJECT/'A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json'
resources+=[candidate,PROJECT/'C_仿真与装配/交接资料/16件初始与目标位姿.csv']
for f in source_files:
 dest=OUT/'frozen_source'/f.relative_to(PROJECT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
shutil.copyfile(candidate,OUT/'candidate_payload.json')
deps=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True);(OUT/'dependencies.txt').write_text(deps)
m={'schema_version':1,'created_HK':STAMP(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'git_status_at_start':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'dependencies_path':'dependencies.txt','source_hashes':{f.relative_to(PROJECT).as_posix():sha(f) for f in source_files},'resource_hashes':{f.relative_to(PROJECT).as_posix():sha(f) for f in resources},'payload':json.loads(candidate.read_text()),'frozen_settings':{'gravity_m_s2':[0,0,-1.62],'external_dt_s':1/240,'num_substeps':4,'control_hz':60,'closing_force_API_N':1,'release_force_API_N':[1,3],'assisted_fixed_constraint_maxForce_API':30,'contactBreakingThreshold_relative':1e-5,'release_opening_gt_m':.0355,'release_linear_speed_lt_m_s':.002,'release_angular_speed_lt_rad_s':.02,'release_consecutive_clear_samples':5,'release_sample_period_s':.05,'robot_penetration_tolerance_m':.0001,'allowed_finger_penetration_m':.0005,'payload_execution_penetration_tolerance_m':.0002,'planned_payload_penetration_allowed_m':0,'final_position_lt_m':.003,'final_orientation_lt_rad':.05,'final_linear_speed_lt_m_s':.005,'compensation_max_xy_m':.002,'all16_preloaded':True,'nominal_targets_unchanged':True,'video_fps':5},'only_condition_difference':'--compensate-grasp-offset','conditions':[],'status':'running'}
save(m)
for condition,comp in [('compensation_off',False),('compensation_on',True)]:
 for rel,h in {**m['source_hashes'],**m['resource_hashes']}.items():assert sha(PROJECT/rel)==h,rel
 dest=OUT/condition
 command=[str(Path(sys.executable).relative_to(ROOT)),str((PROJECT/'C_仿真与装配/run_preloaded_tray_assembly_fast.py').relative_to(ROOT)),'--payload-config','A-candidate','--telemetry','--limit','16','--video','--output',str(dest.relative_to(ROOT))]
 if comp:command+=['--compensate-grasp-offset']
 entry={'id':condition,'compensation_enabled':comp,'command':command,'cwd':'repository root','result_directory':condition,'started_HK':STAMP(),'status':'running'};m['conditions'].append(entry);save(m)
 print('START',condition,STAMP(),flush=True)
 with (OUT/(condition+'_console.log')).open('w',encoding='utf8') as log:
  completed=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 entry.update(exit_code=completed.returncode,ended_HK=STAMP(),status='finished')
 if (dest/'result.json').exists():
  r=json.loads((dest/'result.json').read_text());entry.update(success=r['success'],placed_items=len(r['placed_items']),simulated_seconds=r['simulated_seconds'],error=r['error'])
 else:entry.update(success=False,error='No result.json; inspect console')
 entry['all_frozen_files_unchanged_after_run']=all(sha(PROJECT/rel)==h for rel,h in {**m['source_hashes'],**m['resource_hashes']}.items())
 save(m);print('END',condition,entry,flush=True)
m.update(status='runs_finished',finished_HK=STAMP());save(m)
