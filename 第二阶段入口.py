"""Portable explicit stage-2 runs; never silently select legacy70g or old results."""
from pathlib import Path
import argparse
import datetime
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT/'05_Project3_月面机器人装配'
RESULTS = ROOT/'runs/C_stage2' if os.name == 'nt' else PROJECT/'运行验证/C_第二阶段复现'


def environment():
    return {'python': platform.python_version(), 'system': platform.system(),
            'machine': platform.machine(),
            'pybullet': importlib.metadata.version('pybullet')}


def run_logged(command, output):
    output.mkdir(parents=True, exist_ok=True)
    record = {'command': command, 'runtime_env': environment(),
              'started': datetime.datetime.now().astimezone().isoformat()}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env.setdefault('MPLCONFIGDIR', str(PROJECT/'.cache/matplotlib'))
    with (output/'console.log').open('w', encoding='utf8') as log:
        process = subprocess.Popen(command, cwd=PROJECT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf8', errors='replace')
        for line in process.stdout:
            print(line, end='', flush=True)
            log.write(line)
        rc = process.wait()
    record['exit_code'] = rc
    (output/'执行命令与环境.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return rc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for kind in ['calibrate', 'single', 'full']:
        child = sub.add_parser(kind)
        child.add_argument('--output', type=Path)
        if kind != 'calibrate':
            child.add_argument('--gui', action='store_true')
            child.add_argument('--compensate-grasp-offset', action='store_true')
    child = sub.add_parser('analyze')
    child.add_argument('--input', type=Path, required=True)
    child.add_argument('--calibration', type=Path, required=True)
    child = sub.add_parser('prepare')
    child.add_argument('--role', choices=['A', 'C'], required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        target = ROOT/'AC回传'/args.role
        if target.exists():
            parser.error('回传目录已存在，未覆盖：'+str(target))
        shutil.copytree(ROOT/'AC回传模板'/args.role, target)
        print('回传目录已准备：'+str(target))
        return 0
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if args.action == 'analyze':
        folder = args.input.resolve()
        frozen = PROJECT/'运行验证/B_第二阶段_2026-11-04'
        if folder.is_relative_to(frozen):
            parser.error('不覆盖B封存结果；请选择自己的新运行目录')
        result = json.loads((folder/'result.json').read_text(encoding='utf8'))
        if result.get('payload_config') != 'A-candidate' or result.get('telemetry_rows', 0) <= 0:
            parser.error('不是候选参数+全程采集的运行，不能作为第二阶段结果分析')
        calibration = json.loads(args.calibration.resolve().read_text(encoding='utf8'))
        if len(calibration.get('tests', [])) != 6 or not all(x.get('passed') for x in calibration['tests']):
            parser.error('反馈校准未完整通过，停止使用乘4评价；回传校准日志给B')
        if calibration.get('runtime_env') != environment():
            parser.error('必须提供本机当前环境重新校准的JSON，不能直接使用B旧校准文件')
        if result.get('physics_substeps') != 4:
            parser.error('此分析器只适用于已校准的4子步配置；改变子步后须先调整并复核分析')
        command = [sys.executable, str(PROJECT/'B_第二阶段控制与评价/evaluate.py'), str(folder)]
        rc = run_logged(command, folder/'分析执行记录')
        if rc == 0 and (folder/'assembly.mp4').exists():
            rc = run_logged([sys.executable, str(PROJECT/'B_第二阶段控制与评价/audit_video.py'), str(folder)], folder/'视频执行记录')
        return rc
    output = (args.output or RESULTS/(stamp+'_'+args.action)).resolve()
    if os.name == 'nt' and args.action != 'calibrate' and not str(output).isascii():
        parser.error('Windows Bullet checkpoint output requires an ASCII path; use runs/C_stage2/<run_name>')
    if output.exists():
        parser.error('输出目录已存在，停止以免覆盖；请选择新目录：'+str(output))
    if args.action == 'calibrate':
        command = [sys.executable, str(PROJECT/'B_第二阶段控制与评价/verify_feedback.py'), '--output', str(output/'反馈字段独立核对.json')]
        rc = run_logged(command, output)
        if rc == 0:
            file = output/'反馈字段独立核对.json'
            data = json.loads(file.read_text(encoding='utf8'))
            data['runtime_env'] = environment()
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        return rc
    command = [sys.executable, str(PROJECT/'C_仿真与装配/run_preloaded_tray_assembly_fast.py'),
               '--payload-config', 'A-candidate', '--telemetry', '--limit',
               '1' if args.action == 'single' else '16', '--video', '--output', str(output)]
    if args.compensate_grasp_offset:
        command.append('--compensate-grasp-offset')
    if args.gui:
        command.append('--gui')
    return run_logged(command, output)


if __name__ == '__main__':
    sys.exit(main())
