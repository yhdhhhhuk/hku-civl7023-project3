"""Wait for serial formal runs, then analyze/audit/compare without load imbalance."""
from pathlib import Path
import json,sys,time,subprocess,os
CODE=Path(__file__).resolve().parent;ROOT=CODE.parent;OUT=ROOT/'运行验证/B_第三阶段_2026-11-10'
while True:
 try:m=json.loads((OUT/'experiment_manifest.json').read_text())
 except (OSError,json.JSONDecodeError):m={}
 if m.get('status')=='runs_finished':break
 time.sleep(5)
for script,args,logname in [('analyze_experiments.py',['compensation_off'],'analysis_off_console.log'),('analyze_experiments.py',['compensation_on'],'analysis_on_console.log'),('audit_evidence.py',['compensation_off'],'audit_off_console.log'),('audit_evidence.py',['compensation_on'],'audit_on_console.log'),('compare_experiments.py',[],'comparison_console.log')]:
 print('BEGIN',script,args,flush=True)
 with (OUT/logname).open('w',encoding='utf8') as log:
  c=subprocess.run([sys.executable,str(CODE/script),*args],stdout=log,stderr=subprocess.STDOUT)
 if c.returncode:raise SystemExit(f'{script} failed; inspect {logname}')
 print('DONE',script,args,flush=True)
# Keep this writer stdout outside the evidence scope: its final SHA must not
# include an active log that changes after hashing.
c=subprocess.run([sys.executable,str(CODE/'write_results.py')])
if c.returncode:raise SystemExit(c.returncode)
print('ALL_COMPLETE',flush=True)
