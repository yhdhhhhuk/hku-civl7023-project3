"""Stage3 handoff: verified download and explicit accepted candidate compensation."""
from pathlib import Path
import argparse,datetime,subprocess,sys
ROOT=Path(__file__).resolve().parent
PREFIX='05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10'
def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
 s.add_parser('verify');s.add_parser('restore')
 for action in ['calibrate','single','full']:
  a=s.add_parser(action);a.add_argument('--output',type=Path)
  if action!='calibrate':a.add_argument('--gui',action='store_true');a.add_argument('--without-compensation',action='store_true')
 a=s.add_parser('analyze');a.add_argument('--input',type=Path,required=True);a.add_argument('--calibration',type=Path,required=True)
 args=p.parse_args()
 if args.action=='verify':cmd=[sys.executable,str(ROOT/'scripts/verify_stage3_package.py')]
 elif args.action=='restore':cmd=[sys.executable,str(ROOT/'restore_evidence.py'),'--prefix',PREFIX]
 elif args.action=='analyze':
  archived=(ROOT/PREFIX).resolve();requested=args.input.resolve()
  if requested.is_relative_to(archived):p.error('Archived evidence is read-only; analyze your own new run directory')
  cmd=[sys.executable,str(ROOT/'第二阶段入口.py'),'analyze','--input',str(requested),'--calibration',str(args.calibration.resolve())]
 else:
  output=args.output or Path('runs/local')/('stage3_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+args.action)
  cmd=[sys.executable,str(ROOT/'第二阶段入口.py'),args.action,'--output',str(output)]
  if args.action!='calibrate':
   if not args.without_compensation:cmd+=['--compensate-grasp-offset']
   if args.gui:cmd+=['--gui']
 return subprocess.run(cmd,cwd=ROOT).returncode
if __name__=='__main__':raise SystemExit(main())
