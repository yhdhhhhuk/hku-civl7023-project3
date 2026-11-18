"""Motor-driven unloaded TCP control. No live joint resets after initialization."""
import math
import time
import numpy as np
import pybullet as p
from kinematics import Kinematics, pose, pose_error
from piper_robot import Piper, ARM_NAMES, DT

CONTROL_STEPS=4
CONTROL_DT=CONTROL_STEPS*DT


def measured_tcp(robot):
    """Recover URDF link from the double-precision COM pose, then offset to TCP."""
    s=p.getLinkState(robot.robot,robot.links['gripper_base'],computeForwardKinematics=True,
                     physicsClientId=robot.client)
    world_com=pose(s[0],s[1]);link_com=pose(s[2],s[3])
    world_link=world_com@np.linalg.inv(link_com)
    from piper_robot import TCP_OFFSET
    world_link[:3,3]+=world_link[:3,:3]@TCP_OFFSET
    return world_link


def collision_pairs(robot):
    groups={-1:0,0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:6,8:7,9:8}
    edges={(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(6,8)}
    ignored=set()
    for i in range(-1,10):
        for j in range(i+1,10):
            if groups[i]==groups[j] or tuple(sorted((groups[i],groups[j]))) in edges:
                ignored.add((i,j))
                p.setCollisionFilterPair(robot.robot,robot.robot,i,j,0,physicsClientId=robot.client)
    return ignored


class Guard:
    def __init__(self,base):
        self.client=p.connect(p.DIRECT)
        # Same fixed base as the controlled model; support arbitrary rotations.
        from matrix_helpers import matrix_quaternion
        self.arm=Piper(self.client,base[:3,3],matrix_quaternion(base[:3,:3]),self_collision=True)
        self.ignored=collision_pairs(self.arm)
        self.floor=p.createMultiBody(0,p.createCollisionShape(p.GEOM_PLANE,physicsClientId=self.client),physicsClientId=self.client)

    def check(self,q,width=.036):
        for name,value in zip(ARM_NAMES,q):
            p.resetJointState(self.arm.robot,self.arm.joints[name]['index'],float(value),physicsClientId=self.client)
        for name,value in zip(('joint7','joint8'),(width/2,-width/2)):
            p.resetJointState(self.arm.robot,self.arm.joints[name]['index'],float(value),physicsClientId=self.client)
        for pt in p.getClosestPoints(self.arm.robot,self.arm.robot,.002,physicsClientId=self.client):
            i,j=sorted((pt[3],pt[4]))
            if i!=j and (i,j) not in self.ignored:return ['self',i,j,pt[8]]
        for pt in p.getClosestPoints(self.arm.robot,self.floor,.002,physicsClientId=self.client):
            if pt[3] not in (-1,0):return ['floor',pt[3],pt[8]]
        return None

    def close(self):p.disconnect(self.client)


class PoseController:
    def __init__(self,robot,realtime=False,on_tick=None):
        self.robot=robot;self.kin=Kinematics(robot.world_from_root)
        self.guard=Guard(robot.world_from_root)
        self.realtime=realtime;self.on_tick=on_tick
        self.trace=[];self.time=0.;self.width=.036
        self.view_ticks=0
        self.lower=self.kin.lower+math.radians(2);self.upper=self.kin.upper-math.radians(2)
        self.robot.command_gripper(self.width)

    def q(self):
        values=self.robot.values()
        return np.array([values[n] for n in ARM_NAMES])

    def advance(self):
        for _ in range(CONTROL_STEPS):
            p.stepSimulation(physicsClientId=self.robot.client)
            self.time+=DT
            if self.realtime:time.sleep(DT)
        if self.on_tick:self.on_tick(self.robot)

    def record(self,label,phase,target,qcmd,requested_rate):
        q=self.q();actual=measured_tcp(self.robot);e=pose_error(target,actual)
        states=[p.getJointState(self.robot.robot,self.robot.joints[n]['index'],physicsClientId=self.robot.client) for n in ARM_NAMES]
        J=self.kin.jacobian(q);diag=self.kin.diagnostics(J)
        row={'time_s':self.time,'target_id':label,'phase':phase,
             'position_error_m':float(np.linalg.norm(e[:3])),
             'orientation_error_deg':math.degrees(float(np.linalg.norm(e[3:]))),
             'scaled_sigma_min':diag['scaled_sigma_min'],'scaled_condition':diag['scaled_condition'],
             'joint_margin_deg':math.degrees(float(np.min(np.minimum(q-self.kin.lower,self.kin.upper-q)))),
             'max_joint_velocity_rad_s':max(abs(s[1]) for s in states),
             'max_commanded_rate_rad_s':float(np.max(np.abs(requested_rate)))}
        for i,axis in enumerate('xyz'):
            row[f'target_{axis}_m']=float(target[i,3]);row[f'actual_{axis}_m']=float(actual[i,3])
            row[f'error_{axis}_m']=float(e[i]);row[f'orientation_error_{axis}_rad']=float(e[i+3])
        for i in range(6):
            row[f'q{i+1}_rad']=float(q[i]);row[f'q{i+1}_command_rad']=float(qcmd[i])
            row[f'q{i+1}_velocity_rad_s']=float(states[i][1])
        from matrix_helpers import matrix_quaternion
        for prefix,R in (('target',target[:3,:3]),('actual',actual[:3,:3])):
            for axis,value in zip('xyzw',matrix_quaternion(R)):row[f'{prefix}_quat_{axis}']=float(value)
        self.trace.append(row)
        contact=self.guard.check(q,self.width)
        if contact:raise RuntimeError(f'Actual sampled state violates clearance: {contact}')
        if np.any(q<self.kin.lower-1e-4) or np.any(q>self.kin.upper+1e-4):raise RuntimeError('Actual joint limit violation')
        if self.realtime:
            self.view_ticks+=1
            if self.view_ticks%3==0:
                # macOS processes a render during many synchronous API calls.
                # Batch those calls and expose only 20 frames per simulated sec.
                p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,1,physicsClientId=self.robot.client)
                p.configureDebugVisualizer(p.COV_ENABLE_RENDERING,0,physicsClientId=self.robot.client)
        return row

    def move_to_pose(self,position,quaternion,label='target',strategy='auto',timeout=20.):
        if strategy not in ('auto','cartesian','joint'):raise ValueError('Unknown control strategy')
        target=pose(position,quaternion);start_q=self.q();start_error=pose_error(target,measured_tcp(self.robot))
        ik=self.kin.inverse(target,start_q)
        goal=np.array(ik['q_rad'])
        # A second physics client checks geometry. It never resets the live robot.
        for t in np.linspace(0,1,max(20,math.ceil(float(np.max(np.abs(goal-start_q)))/.02))+1):
            hit=self.guard.check(start_q*(1-t)+goal*t,self.width)
            if hit:raise ValueError(f'Joint connection rejected by clearance guard: {hit}')
        self.robot.display_target=target
        use_joint=(strategy=='joint' or (strategy=='auto' and
                   (np.linalg.norm(start_error[:3])>.035 or np.linalg.norm(start_error[3:])>.25)))
        first=len(self.trace);started=self.time
        if use_joint:
            delta=goal-start_q
            duration=max(1.,1.875*float(np.max(np.abs(delta)))/.35,
                         math.sqrt(5.8*float(np.max(np.abs(delta)))/.6))
            steps=math.ceil(duration/CONTROL_DT)
            for tick in range(steps):
                s=(tick+1)/steps;h=10*s**3-15*s**4+6*s**5
                rate=delta*(30*s*s-60*s**3+30*s**4)/(steps*CONTROL_DT)
                command=start_q+h*delta
                self.robot.command_arm(command);self.advance()
                self.record(label,'quintic_joint_transfer',target,command,rate)
        stable=0;reached=False
        reference=self.q()
        for _ in range(math.ceil(timeout/CONTROL_DT)):
            q=self.q();actual=measured_tcp(self.robot);e=pose_error(target,actual)
            velocity=np.r_[3*e[:3],3*e[3:]]
            velocity[:3]*=min(1.,.04/max(np.linalg.norm(velocity[:3]),1e-12))
            velocity[3:]*=min(1.,.3/max(np.linalg.norm(velocity[3:]),1e-12))
            rate=self.kin.damped_velocity(self.kin.jacobian(q),velocity,damping=.02,max_speed=.35)
            # Integrate the reference, rather than discarding it each cycle.
            # This retains the small position offset needed by the inner servo
            # to oppose gravity; q+dt*rate alone leaves a static tracking bias.
            reference=np.clip(reference+CONTROL_DT*rate,self.lower,self.upper)
            reference=np.clip(reference,q-.03,q+.03)
            command=reference.copy()
            hit=self.guard.check(command,self.width)
            if hit:raise RuntimeError(f'Next control state rejected: {hit}')
            self.robot.command_arm(command);self.advance()
            row=self.record(label,'cartesian_dls_feedback',target,command,rate)
            good=(row['position_error_m']<.0001 and row['orientation_error_deg']<.1
                  and row['max_joint_velocity_rad_s']<.02)
            stable=stable+1 if good else 0
            if stable>=15:reached=True;break
        segment=self.trace[first:]
        result={'target_id':label,'status':'reached' if reached else 'timeout',
                'strategy':'joint_transfer_then_cartesian' if use_joint else 'cartesian_dls',
                'target_position_m':target[:3,3].tolist(),
                'target_rotation_matrix':target[:3,:3].tolist(),'ik':ik,
                'duration_s':self.time-started,'trace_rows':len(segment),
                'initial_position_error_m':float(np.linalg.norm(start_error[:3])),
                'initial_orientation_error_deg':math.degrees(float(np.linalg.norm(start_error[3:]))),
                'final_position_error_m':segment[-1]['position_error_m'],
                'final_orientation_error_deg':segment[-1]['orientation_error_deg'],
                'steady_position_rms_m':float(np.sqrt(np.mean([r['position_error_m']**2 for r in segment[-15:]]))),
                'steady_orientation_rms_deg':float(np.sqrt(np.mean([r['orientation_error_deg']**2 for r in segment[-15:]]))),
                'maximum_position_error_m':max(r['position_error_m'] for r in segment),
                'minimum_joint_margin_deg':min(r['joint_margin_deg'] for r in segment)}
        if not reached:raise RuntimeError(f'Controller timeout: {result}')
        return result

    def close(self):self.guard.close()
