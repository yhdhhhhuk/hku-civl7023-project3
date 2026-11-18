"""Independent Bullet, finite-difference and instantaneous velocity checks."""
import csv
import hashlib
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import numpy as np
import pybullet as p
from kinematics import Kinematics, pose, so3_log
from controller import measured_tcp
from matrix_helpers import matrix_quaternion
from piper_robot import Piper, ARM_NAMES, TCP_OFFSET, URDF, PROJECT

OUT=PROJECT/'运行验证/基础控制与雅可比'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(702304);records=[];client=p.connect(p.DIRECT)
    try:
        for base_index,(position,angles) in enumerate([([0,0,0],[0,0,0]),([.1,-.12,.04],[.2,-.15,.3])]):
            robot=Piper(client,position,p.getQuaternionFromEuler(angles));kin=Kinematics(robot.world_from_root)
            def reset(q,qd=None):
                if qd is None:qd=np.zeros(6)
                for name,value,velocity in zip(ARM_NAMES,q,qd):
                    p.resetJointState(robot.robot,robot.joints[name]['index'],float(value),float(velocity),physicsClientId=client)
            for sample in range(30):
                q=rng.uniform(kin.lower+.05,kin.upper-.05);reset(q)
                own,J=kin.evaluate(q);actual=measured_tcp(robot)
                allq=q.tolist()+[.018,-.018]
                raw=p.calculateJacobian(robot.robot,robot.links['gripper_base'],TCP_OFFSET.tolist(),allq,[0]*8,[0]*8,physicsClientId=client)
                # Bullet's fixed-base Jacobian is base-frame expressed.
                R=robot.world_from_root[:3,:3]
                bullet=np.vstack((R@np.asarray(raw[0]),R@np.asarray(raw[1])))
                finite=np.zeros((6,6));h=1e-6
                for i in range(6):
                    delta=np.eye(6)[i]*h
                    reset(q+delta);plus=measured_tcp(robot)
                    reset(q-delta);minus=measured_tcp(robot)
                    finite[:3,i]=(plus[:3,3]-minus[:3,3])/(2*h)
                    finite[3:,i]=so3_log(plus[:3,:3]@minus[:3,:3].T)/(2*h)
                velocity=rng.uniform(-.25,.25,6);reset(q,velocity)
                state=p.getLinkState(robot.robot,robot.links['gripper_base'],computeLinkVelocity=True,
                                     computeForwardKinematics=True,physicsClientId=client)
                tcp=measured_tcp(robot)
                measured_v=np.array(state[6])+np.cross(state[7],tcp[:3,3]-state[0])
                predicted=J@velocity
                row={'base_case':base_index,'sample':sample,
                     'fk_position_difference_m':float(np.linalg.norm(own[:3,3]-actual[:3,3])),
                     'fk_orientation_difference_rad':float(np.linalg.norm(so3_log(own[:3,:3]@actual[:3,:3].T))),
                     'analytic_vs_bullet_J_max_abs':float(np.max(np.abs(J-bullet[:,:6]))),
                     'analytic_vs_finite_J_max_abs':float(np.max(np.abs(J-finite))),
                     'finger_J_columns_max_abs':float(np.max(np.abs(bullet[:,6:]))),
                     'linear_velocity_difference_m_s':float(np.max(np.abs(predicted[:3]-measured_v))),
                     'angular_velocity_difference_rad_s':float(np.max(np.abs(predicted[3:]-state[7])))}
                records.append(row)
            # Wrong-point negative control: subtracting COM translation changes
            # the queried point and must not silently pass as the TCP Jacobian.
            reset(q)
            inertial=p.getLinkState(robot.robot,robot.links['gripper_base'],physicsClientId=client)
            wrong=p.calculateJacobian(robot.robot,robot.links['gripper_base'],
                (TCP_OFFSET-np.array(inertial[2])).tolist(),allq,[0]*8,[0]*8,physicsClientId=client)
            wrong_J=np.vstack((R@np.array(wrong[0]),R@np.array(wrong[1])))[:,:6]
            negative=float(np.max(np.abs(J-wrong_J)))
            assert negative>.01
            p.removeBody(robot.robot,physicsClientId=client)
        kin=Kinematics();singular_J=kin.jacobian(np.zeros(6));diag=kin.diagnostics(singular_J)
        rate=kin.damped_velocity(singular_J,np.array([.02,.01,.01,.1,0,.1]))
        assert np.isfinite(rate).all() and np.max(np.abs(rate))<=.35+1e-12
        maxima={k:max(r[k] for r in records) for k in records[0] if k not in ('base_case','sample')}
        limits={'fk_position_difference_m':1e-10,'fk_orientation_difference_rad':1e-10,
                'analytic_vs_bullet_J_max_abs':1e-10,'analytic_vs_finite_J_max_abs':1e-7,
                'finger_J_columns_max_abs':1e-12,'linear_velocity_difference_m_s':1e-10,
                'angular_velocity_difference_rad_s':1e-10}
        assert all(maxima[k]<limits[k] for k in limits),(maxima,limits)
        # Small offsets in this URDF leave zero pose full rank but poorly
        # conditioned. Do not call it an exact physical singularity.
        assert diag['scaled_condition']>1000
        artificial=singular_J.copy();artificial[:,5]=artificial[:,3]
        artificial_diag=kin.diagnostics(artificial)
        artificial_rate=kin.damped_velocity(artificial,np.ones(6)*.1)
        assert artificial_diag['rank']<6 and np.isfinite(artificial_rate).all()
        rotation_cases=[p.getQuaternionFromEuler([0,math.pi,0]),[0,0,0,1]]
        rotation_cases += [p.getQuaternionFromEuler(rng.uniform(-math.pi,math.pi,3)) for _ in range(20)]
        worst_roundtrip=0.
        for quat in rotation_cases:
            T=pose([0,0,0],quat);back=pose([0,0,0],matrix_quaternion(T[:3,:3]))
            flipped=pose([0,0,0],-np.array(quat))
            worst_roundtrip=max(worst_roundtrip,float(np.max(np.abs(T-back))),float(np.max(np.abs(T-flipped))))
        assert worst_roundtrip<1e-12
        now=datetime.now(ZoneInfo('Asia/Hong_Kong'))
        result={'status':'PASS','date':now.date().isoformat(),'recorded_at_hkt':now.isoformat(),'configurations':60,'base_poses':2,
                'finite_difference_step_rad':1e-6,'convention':'world-frame TCP geometric Jacobian [v; omega], 6x6',
                'urdf_sha256':hashlib.sha256(URDF.read_bytes()).hexdigest(),
                'maxima':maxima,'verification_limits':limits,
                'wrong_COM_point_negative_control_J_difference':negative,
                'quaternion_roundtrip_and_sign_checks':{'cases':len(rotation_cases),'maximum_matrix_difference':worst_roundtrip},
                'near_singular_zero_pose':{**diag,'damped_rate_rad_s':rate.tolist()},
                'synthetic_rank_deficient_matrix':{**artificial_diag,'damped_rate_rad_s':artificial_rate.tolist(),
                    'meaning':'numerical robustness test, not a claimed robot configuration'},
                'scope':'static FK, Jacobian derivative and instantaneous velocity consistency; not collision or dynamics validation'}
        (OUT/'运动学与雅可比验证结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        with (OUT/'雅可比交叉核对.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,list(records[0]));w.writeheader();w.writerows(records)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:p.disconnect(client)


if __name__=='__main__':main()
