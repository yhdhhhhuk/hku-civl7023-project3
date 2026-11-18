"""Task-aligned vertical moves with dense IK checks and guarded B DLS feedback."""
import math
import numpy as np
from scipy.spatial.transform import Rotation
from C_仿真与装配.polygon_planning import move_planned as joint_move,GuardWorld

def move_planned(control,position,label,planning_log,item,yaw=0.):
    if label not in ['lower','descend']:return joint_move(control,position,label,planning_log,item,yaw)
    from kinematics import pose,pose_error
    from controller import measured_tcp
    quat=Rotation.from_matrix(Rotation.from_euler('z',yaw).as_matrix()@np.diag([-1.,1.,-1.])).as_quat().tolist()
    target=pose(position,quat);actual=measured_tcp(control.robot);start=control.q();world=GuardWorld(control,.001)
    entry={'item':item,'phase':label,'target':position,'yaw':yaw,'start_q':start.tolist(),'status':'planning','method':'cartesian_vertical_checked','command_preflight':False,'online_command_checks':True,'edge_resolution_rad':.001,'cartesian_resolution_m':.002,'planned_payload_distance_limit_m':0.,'route_trials':[]}
    planning_log.append(entry);began=control.time
    try:
        path=[start];count=max(1,math.ceil(float(np.linalg.norm(target[:3,3]-actual[:3,3]))/.002))
        for k in range(1,count+1):
            T=target.copy();T[:3,3]=actual[:3,3]+(target[:3,3]-actual[:3,3])*k/count
            goal=np.array(control.kin.inverse(T,path[-1])['q_rad'])
            if not world.edge(path[-1],goal):raise RuntimeError(f'Vertical path blocked: {world.last_reason}')
            path.append(goal)
        entry.update(path=[q.tolist() for q in path],goal_q=path[-1].tolist(),cartesian_samples_valid=True)
        reference=control.q();stable=0;first=len(control.trace);row=None
        for _ in range(math.ceil(20/(4/240))):
            q=control.q();actual=measured_tcp(control.robot);e=pose_error(target,actual);velocity=np.r_[3*e[:3],3*e[3:]]
            velocity[:3]*=min(1.,.04/max(np.linalg.norm(velocity[:3]),1e-12));velocity[3:]*=min(1.,.3/max(np.linalg.norm(velocity[3:]),1e-12))
            rate=control.kin.damped_velocity(control.kin.jacobian(q),velocity,damping=.02,max_speed=.35)
            reference=np.clip(reference+(4/240)*rate,control.lower,control.upper);reference=np.clip(reference,q-.03,q+.03)
            hit=control.guard.check(reference,control.width)
            if hit:raise RuntimeError(f'Vertical command blocked: {hit}')
            control.robot.command_arm(reference);control.advance();row=control.record(label,'guarded_vertical_dls',target,reference,rate)
            good=row['position_error_m']<.0001 and row['orientation_error_deg']<.1 and row['max_joint_velocity_rad_s']<.02
            stable=stable+1 if good else 0
            if stable>=15:break
        else:raise RuntimeError('Vertical feedback timeout')
        entry.update(status='executed',checks=world.checks,duration_s=control.time-began)
        return {'target_id':label,'status':'reached','strategy':'sampled_vertical_then_guarded_DLS','duration_s':control.time-began,'trace_rows':len(control.trace)-first,'final_position_error_m':row['position_error_m'],'final_orientation_error_deg':row['orientation_error_deg']}
    except Exception as exc:
        entry.update(status='failed',checks=world.checks,error=str(exc),last_reason=world.last_reason);raise
