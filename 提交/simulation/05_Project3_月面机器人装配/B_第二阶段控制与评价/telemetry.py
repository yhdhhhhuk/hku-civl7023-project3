"""One sample after every external Bullet step; stream even on failure."""
import csv
import pybullet as p
class Telemetry:
    def __init__(self,robot,path):
        self.robot=robot
        self.names=[f'joint{i}' for i in range(1,9)]
        self.indices=[robot.joints[n]['index'] for n in self.names]
        for j in self.indices:p.enableJointForceTorqueSensor(robot.robot,j,1,physicsClientId=robot.client)
        self.file=path.open('w',newline='',encoding='utf-8-sig');self.writer=None;self.count=0
    def sample(self,step,dt,item,phase,constraint):
        states=p.getJointStates(self.robot.robot,self.indices,physicsClientId=self.robot.client)
        row=dict(step=step,time_s=step*dt,item=item,phase=phase,attached=constraint is not None)
        for i,s in enumerate(states,1):
            unit='rad' if i<=6 else 'm'; effort='Nm' if i<=6 else 'N'
            row.update({f'q{i}_{unit}':s[0],f'dq{i}_{unit}_s':s[1],f'motor{i}_{effort}':s[3]})
            for axis,v in zip(('Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm'),s[2]):row[f'reaction{i}_{axis}']=v
        wrench=p.getConstraintState(constraint,physicsClientId=self.robot.client) if constraint is not None else [0.]*6
        for axis,v in zip(('Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm'),wrench):row['constraint_'+axis]=v
        if self.writer is None:self.writer=csv.DictWriter(self.file,list(row));self.writer.writeheader()
        self.writer.writerow(row);self.count+=1
    def close(self):self.file.close()
