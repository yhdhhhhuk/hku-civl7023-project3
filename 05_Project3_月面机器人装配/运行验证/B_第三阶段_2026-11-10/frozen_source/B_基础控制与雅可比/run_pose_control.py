"""CLI/GUI pose control; --full runs motor-driven unloaded acceptance checks."""
import argparse
import csv
import json
import hashlib
import math
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import numpy as np
import pybullet as p
from kinematics import Kinematics, pose
from matrix_helpers import matrix_quaternion
from controller import PoseController, collision_pairs, measured_tcp, CONTROL_DT
from piper_robot import Piper, PROJECT, URDF, DT, ARM_NAMES, render_frame

OUT=PROJECT/'运行验证/基础控制与雅可比'


def targets(full):
    source=json.loads((PROJECT/'运行验证/工作空间/工作空间验证结果.json').read_text())
    assert source['component_version']=='P3-GrooveKey-v2'
    waypoint=source['sources'][1]
    kin=Kinematics();base_q=np.array(waypoint['approach_pose']['q_rad'])
    def item(name,xyz,quat=(0,1,0,0),strategy='auto'):
        return {'id':name,'position':list(xyz),'quaternion':list(quat),'strategy':strategy}
    cases=[]
    if full:
        for entry in source['sources']+source['goals']:
            cases.extend([item(entry['id']+'_above',entry['approach_tcp_m']),
                          item(entry['id']+'_grasp',entry['tcp_m'])])
        cases.append(item('orientation_ready',waypoint['approach_tcp_m']))
        cases.append(item('position_nudge',np.array(waypoint['approach_tcp_m'])+[.008,.006,-.003],strategy='cartesian'))
        variations=[('orientation_tilt',[0,0,0,.06,0,0]),
                    ('orientation_roll',[0,0,0,0,0,.12]),
                    ('orientation_combined',[0,0,0,-.05,-.04,-.10])]
    else:
        cases=[item('S2_above',waypoint['approach_tcp_m']),item('S2_grasp',waypoint['tcp_m']),
               item('S2_retreat',waypoint['approach_tcp_m'])]
        variations=[('orientation_tilt',[0,0,0,.06,0,0])]
    for name,delta in variations:
        T=kin.fk(base_q+delta)
        cases.append(item(name,T[:3,3],matrix_quaternion(T[:3,:3]),'cartesian'))
    return cases


def draw(robot):
    frame=measured_tcp(robot);start=frame[:3,3]
    for i,color in enumerate([(1,0,0),(0,.7,0),(0,.2,1)]):
        p.addUserDebugLine(start,start+.04*frame[:3,i],color,2,lifeTime=.08,physicsClientId=robot.client)
    if hasattr(robot,'display_target'):
        target=robot.display_target
        for i,color in enumerate([(1,.55,.55),(.55,.9,.55),(.55,.65,1)]):
            p.addUserDebugLine(target[:3,3],target[:3,3]+.05*target[:3,i],color,2,lifeTime=.08,physicsClientId=robot.client)


def save(output,controller,results,rejections,status,error=None,gui=False):
    output.mkdir(parents=True,exist_ok=True)
    if controller.trace:
        with (output/'位姿误差轨迹.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,list(controller.trace[0]));w.writeheader();w.writerows(controller.trace)
    if results:
        keys=['target_id','status','strategy','duration_s','initial_position_error_m','initial_orientation_error_deg',
              'final_position_error_m','final_orientation_error_deg','steady_position_rms_m','steady_orientation_rms_deg','minimum_joint_margin_deg']
        with (output/'目标定位误差汇总.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,keys,extrasaction='ignore');w.writeheader();w.writerows(results)
    now=datetime.now(ZoneInfo('Asia/Hong_Kong'))
    summary={'status':status,'date':now.date().isoformat(),'recorded_at_hkt':now.isoformat(),'gui':gui,'error':error,
             'urdf_sha256':hashlib.sha256(URDF.read_bytes()).hexdigest(),
             'conditions':{'gravity_m_s2':[0,0,-1.62],'fixed_base':True,'payload':'none; no blocks',
                           'simulation_dt_s':DT,'control_dt_s':CONTROL_DT,'max_joint_command_speed_rad_s':.35,
                           'position_gain_per_s':3,'orientation_gain_per_s':3,'characteristic_length_m':.3,
                           'damping':.02,'nominal_gripper_opening_m':.036,'position_inner_gain':.15,'velocity_inner_gain':1,
                           'motor_force_limits':'URDF effort, not verified hardware ratings',
                           'geometry_monitor':'self and horizontal ground, 2 mm clearance; sampled, no scene blocks'},
             'acceptance':{'position_m':.0001,'orientation_deg':.1,'max_speed_for_settle_rad_s':.02,
                           'consecutive_control_ticks':15,'meaning':'internal unloaded simulation thresholds, not course grading limits'},
             'live_joint_resets_after_initialization':0,
             'target_count':len(results),'trace_rows':len(controller.trace),'simulated_duration_s':controller.time,
             'worst_final_position_error_m':max((r['final_position_error_m'] for r in results),default=None),
             'worst_final_orientation_error_deg':max((r['final_orientation_error_deg'] for r in results),default=None),
             'minimum_joint_margin_deg':min((r['joint_margin_deg'] for r in controller.trace),default=None),
             'maximum_actual_joint_speed_rad_s':max((r['max_joint_velocity_rad_s'] for r in controller.trace),default=None),
             'targets':results,'rejected_inputs':rejections,
             'scope':'motor-driven unloaded positioning and orientation; not frictional grasp, CAD contact, full scene planning or load torque validation'}
    (output/'位姿控制验证结果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gui',action='store_true');parser.add_argument('--hold',action='store_true')
    parser.add_argument('--full',action='store_true',help='29 named targets and invalid-input checks')
    parser.add_argument('--position',nargs=3,type=float,help='Nominal TCP x y z in metres')
    parser.add_argument('--quaternion',nargs=4,type=float,help='Target orientation x y z w')
    parser.add_argument('--strategy',choices=['auto','joint','cartesian'],default='auto')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if (args.position is None)!=(args.quaternion is None):parser.error('Supply both --position and --quaternion')
    if args.position is not None and args.full:parser.error('Custom target and --full are mutually exclusive')
    output=args.output or (OUT if args.full else OUT/('GUI演示' if args.gui else '单目标或演示'))
    output.mkdir(parents=True,exist_ok=True)
    client=p.connect(p.GUI if args.gui else p.DIRECT)
    if client<0:raise RuntimeError('Cannot connect to PyBullet')
    if args.gui:
        p.configureDebugVisualizer(p.COV_ENABLE_GUI,0,physicsClientId=client)
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,0,physicsClientId=client)
    robot=Piper(client,self_collision=True);collision_pairs(robot)
    p.createMultiBody(0,p.createCollisionShape(p.GEOM_PLANE,physicsClientId=client),physicsClientId=client)
    p.setGravity(0,0,-1.62,physicsClientId=client)
    robot.reset_demo_pose();robot.command_gripper(.036);robot.step(.25)
    if args.gui:
        p.resetDebugVisualizerCamera(.9,50,-25,[.12,0,.24],physicsClientId=client)
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,1,physicsClientId=client)
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,0,physicsClientId=client)
    controller=PoseController(robot,realtime=args.gui,on_tick=draw if args.gui else None)
    results=[];rejections=[];cases=[]
    print('Pose controller ready; fixed stepping 240 Hz, control 60 Hz.',flush=True)
    try:
        if args.full:
            for name,xyz,quat in [('far_unreachable',[2,0,.3],[0,1,0,0]),
                                  ('zero_quaternion',[.27,-.07,.082],[0,0,0,0]),
                                  ('nonfinite_position',[float('nan'),0,.1],[0,1,0,0]),
                                  ('wrong_position_dimension',[.2,.1],[0,1,0,0])]:
                before=controller.q().copy();clock_before=controller.time
                try:controller.move_to_pose(xyz,quat,name)
                except ValueError as exc:
                    assert np.array_equal(before,controller.q()) and controller.time==clock_before
                    rejections.append({'input':name,'status':'rejected_without_motion','reason':str(exc)})
                else:raise AssertionError(f'Invalid input accepted: {name}')
        cases=targets(args.full) if args.position is None else [
            {'id':'custom_target','position':args.position,'quaternion':args.quaternion,'strategy':args.strategy}]
        for case in cases:
            result=controller.move_to_pose(case['position'],case['quaternion'],case['id'],case['strategy'])
            results.append(result)
            print(json.dumps({'target':case['id'],'status':result['status'],
                'position_error_mm':result['final_position_error_m']*1000,
                'orientation_error_deg':result['final_orientation_error_deg']},ensure_ascii=False),flush=True)
        render_frame(robot,output/'目标位姿_最终预览.png')
        if args.gui:
            from 验证环境 import save_png
            p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,1,physicsClientId=client)
            view=p.computeViewMatrixFromYawPitchRoll([.12,0,.24],.9,50,-25,0,2)
            projection=p.computeProjectionMatrixFOV(45,1200/800,.01,5)
            pixels=p.getCameraImage(1200,800,view,projection,renderer=p.ER_BULLET_HARDWARE_OPENGL,physicsClientId=client)
            save_png(output/'GUI_OpenGL渲染.png',np.asarray(pixels[2],dtype=np.uint8).reshape(800,1200,4)[:,:,:3])
        summary=save(output,controller,results,rejections,'PASS',gui=args.gui)
        print(json.dumps({k:summary[k] for k in ('status','target_count','trace_rows','worst_final_position_error_m','worst_final_orientation_error_deg')},indent=2),flush=True)
        if args.gui and args.hold:
            print('Targets reached. Close the simulation window to exit.',flush=True)
            while p.isConnected(client):
                p.stepSimulation(physicsClientId=client);time.sleep(DT)
    except Exception as exc:
        if args.gui and not p.isConnected(client):
            print('GUI window closed.',flush=True)
            if not cases or len(results)<len(cases):save(output,controller,results,rejections,'INTERRUPTED','Window closed',gui=True)
            return
        save(output,controller,results,rejections,'FAIL',str(exc),gui=args.gui)
        raise
    finally:
        controller.close()
        if p.isConnected(client):p.disconnect(client)


if __name__=='__main__':main()
