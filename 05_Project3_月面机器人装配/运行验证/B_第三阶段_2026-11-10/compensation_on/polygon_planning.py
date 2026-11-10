"""Dense joint-edge planning, command-grid preflight and B feedback control."""
import math
import numpy as np
from scipy.spatial.transform import Rotation
from C_仿真与装配.motion_planning import plan_path

class GuardWorld:
    def __init__(self,control,resolution):
        self.control=control;self.resolution=resolution;self.checks=0;self.last_reason=None
    def free(self,q):
        self.checks+=1
        guard=self.control.guard;previous=getattr(guard,'payload_limit',-.0002)
        guard.payload_limit=0.  # Planned payload stays clear; execution retains 0.2mm tolerance.
        try:self.last_reason=guard.check(q,self.control.width)
        finally:guard.payload_limit=previous
        return self.last_reason is None
    def edge(self,a,b,resolution=None):
        n=max(1,math.ceil(float(np.max(np.abs(b-a)))/(resolution or self.resolution)))
        return all(self.free(a+(b-a)*i/n) for i in range(n+1))

def commands(a,b,label):
    delta=b-a;slow=label in ['lower','descend']
    speed=.2 if slow else .35;acceleration=.4 if slow else .6
    duration=max(1.,1.875*float(np.max(np.abs(delta)))/speed,math.sqrt(5.8*float(np.max(np.abs(delta)))/acceleration))
    ticks=math.ceil(duration/(4/240))
    for tick in range(ticks):
        u=(tick+1)/ticks;h=10*u**3-15*u**4+6*u**5
        yield a+h*delta,delta*(30*u*u-60*u**3+30*u**4)/(ticks*4/240)

def move_planned(control,position,label,planning_log,item,yaw=0.):
    orientation=Rotation.from_euler('z',yaw).as_matrix()@np.diag([-1.,1.,-1.])
    quaternion=Rotation.from_matrix(orientation).as_quat().tolist()
    target=np.eye(4);target[:3,:3]=orientation;target[:3,3]=position
    start=control.q();ik=control.kin.inverse(target,start);goal=np.array(ik['q_rad'])
    world=GuardWorld(control,.001 if label in ['lower','descend'] else .005)
    entry={'item':item,'phase':label,'target':position,'yaw':yaw,'start_q':start.tolist(),'goal_q':goal.tolist(),'status':'planning','route_trials':[],'edge_resolution_rad':world.resolution,'planned_payload_distance_limit_m':0.,'command_preflight':True}
    planning_log.append(entry);started=control.time
    try:
        for trial in range(4):
            path,info=plan_path(start,goal,world,control.lower,control.upper,seed=7023+trial)
            # Validate the exact quintic command samples, not only coarse path vertices.
            valid=all(world.free(q) for a,b in zip(path,path[1:]) for q,rate in commands(a,b,label))
            entry['route_trials'].append({**info,'command_grid_valid':valid,'last_reason':world.last_reason})
            if valid:break
            world.resolution/=2
        else:raise RuntimeError(f'No route passed exact command preflight: {world.last_reason}')
        entry.update(info);entry['edge_resolution_rad']=world.resolution;entry['path']=[q.tolist() for q in path]
        control.robot.display_target=target
        for a,b in zip(path,path[1:]):
            for command,rate in commands(a,b,label):
                hit=control.guard.check(command,control.width)
                if hit:raise RuntimeError(f'Checked trajectory execution guard: {hit}')
                control.robot.command_arm(command);control.advance()
                control.record(label,'rrt_quintic_joint' if len(path)>2 else 'checked_quintic_joint',target,command,rate)
        result=control.move_to_pose(position,quaternion,label=label)
        result['strategy']='checked_quintic_then_B_feedback';result['duration_s']=control.time-started
        entry.update(status='executed',checks=world.checks,duration_s=control.time-started)
        return result
    except Exception as exc:
        entry.update(status='failed',error=str(exc),checks=world.checks,last_reason=world.last_reason)
        raise
