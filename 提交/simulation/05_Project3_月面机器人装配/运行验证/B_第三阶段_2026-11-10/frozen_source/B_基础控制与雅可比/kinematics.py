"""URDF FK, world-frame geometric TCP Jacobian [linear; angular], and DLS IK."""
from pathlib import Path
import sys
import math
import xml.etree.ElementTree as ET
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'B_关节与夹爪'))
from piper_robot import ARM_NAMES, TCP_OFFSET, URDF, origin_transform, rotation


def so3_log(R):
    """Axis-angle vector of a proper rotation, robust at zero and pi."""
    R=np.asarray(R,dtype=float)
    c=float(np.clip((np.trace(R)-1)/2,-1,1))
    theta=math.acos(c)
    skew=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])
    if theta<1e-6:return .5*skew
    if math.pi-theta<1e-5:
        vals,vecs=np.linalg.eigh((R+R.T+2*np.eye(3))/4)
        axis=vecs[:,np.argmax(vals)]
        if np.linalg.norm(skew)>1e-10 and np.dot(axis,skew)<0:axis=-axis
        return theta*axis
    return theta/(2*math.sin(theta))*skew


def pose(position,quaternion):
    import pybullet as p
    position=np.asarray(position,dtype=float);q=np.asarray(quaternion,dtype=float)
    if position.shape!=(3,) or q.shape!=(4,) or not np.isfinite(position).all() or not np.isfinite(q).all():
        raise ValueError('Position needs 3 and xyzw quaternion needs 4 finite numbers')
    if np.linalg.norm(q)<1e-10:raise ValueError('Zero quaternion is invalid')
    q=q/np.linalg.norm(q)
    T=np.eye(4);T[:3,3]=position;T[:3,:3]=np.asarray(p.getMatrixFromQuaternion(q)).reshape(3,3)
    return T


def pose_error(target,actual):
    return np.r_[target[:3,3]-actual[:3,3],so3_log(target[:3,:3]@actual[:3,:3].T)]


class Kinematics:
    def __init__(self,world_from_root=None):
        self.base=np.eye(4) if world_from_root is None else np.array(world_from_root,dtype=float)
        root=ET.parse(URDF).getroot()
        by_child={j.find('child').get('link'):j for j in root.findall('joint')}
        joints=[];child='gripper_base'
        while child in by_child:
            j=by_child[child];joints.append(j);child=j.find('parent').get('link')
        self.chain=[];self.lower=[];self.upper=[]
        for j in reversed(joints):
            name=j.get('name');axis=None
            if j.get('type')!='fixed':
                assert name==ARM_NAMES[len(self.lower)]
                axis=np.fromstring(j.find('axis').get('xyz'),sep=' ')
                limits=j.find('limit');self.lower.append(float(limits.get('lower')));self.upper.append(float(limits.get('upper')))
            self.chain.append((origin_transform(j.find('origin')),axis))
        self.lower=np.asarray(self.lower);self.upper=np.asarray(self.upper)
        self.length_scale=.3
        self.W=np.diag([1/self.length_scale]*3+[1]*3)

    def evaluate(self,q):
        q=np.asarray(q,dtype=float)
        if q.shape!=(6,) or not np.isfinite(q).all():raise ValueError('Six finite joint angles required')
        T=self.base.copy();axes=[];origins=[];i=0
        for origin,axis in self.chain:
            T=T@origin
            if axis is not None:
                axes.append(T[:3,:3]@axis);origins.append(T[:3,3].copy())
                M=np.eye(4);M[:3,:3]=rotation(axis,q[i]);T=T@M;i+=1
        T[:3,3]+=T[:3,:3]@TCP_OFFSET
        J=np.column_stack([np.r_[np.cross(a,T[:3,3]-o),a] for a,o in zip(axes,origins)])
        return T,J

    def fk(self,q):return self.evaluate(q)[0]
    def jacobian(self,q):return self.evaluate(q)[1]

    def diagnostics(self,J):
        s=np.linalg.svd(self.W@J,compute_uv=False)
        return {'scaled_singular_values':s.tolist(),'scaled_sigma_min':float(s[-1]),
                'scaled_condition':float(s[0]/s[-1]) if s[-1]>1e-12 else None,
                'rank':int(np.count_nonzero(s>1e-8))}

    def damped_velocity(self,J,velocity,damping=.02,max_speed=.35):
        A=self.W@J;b=self.W@velocity
        dq=A.T@np.linalg.solve(A@A.T+damping*damping*np.eye(6),b)
        factor=min(1.,max_speed/max(np.max(np.abs(dq)),1e-12))
        return dq*factor

    def inverse(self,target,seed,margin=math.radians(2)):
        """Projected DLS iterations; accept only independently evaluated pose residuals."""
        if target.shape!=(4,4) or not np.isfinite(target).all():raise ValueError('Invalid target transform')
        current=np.asarray(seed,dtype=float)
        if current.shape!=(6,) or not np.isfinite(current).all():raise ValueError('Invalid IK seed')
        local=np.linalg.inv(self.base)@target
        yaw=math.atan2(local[1,3],local[0,3])
        seeds=[current,[yaw,1.6,-1.2,0,1.1,yaw],[yaw,1.0,-1.8,0,.6,yaw],
               [yaw,2.3,-.7,0,1.,yaw]]
        lo=self.lower+margin;hi=self.upper-margin;best=None
        for seed_index,start in enumerate(seeds):
            q=np.clip(start,lo,hi)
            for iteration in range(250):
                actual,J=self.evaluate(q);e=pose_error(target,actual)
                cost=float(np.linalg.norm(self.W@e))
                record={'q_rad':q.tolist(),'position_residual_m':float(np.linalg.norm(e[:3])),
                        'orientation_residual_rad':float(np.linalg.norm(e[3:])),
                        'iterations':iteration+1,'seed_index':seed_index}
                if best is None or cost<best[0]:best=(cost,record)
                if record['position_residual_m']<1e-5 and record['orientation_residual_rad']<1e-4:return record
                dq=self.damped_velocity(J,e,damping=.015,max_speed=.15)
                improved=False
                for alpha in (1.,.5,.25,.1):
                    candidate=np.clip(q+alpha*dq,lo,hi)
                    if np.linalg.norm(self.W@pose_error(target,self.fk(candidate)))<cost-1e-12:
                        q=candidate;improved=True;break
                if not improved:break
        raise ValueError(f'No acceptable IK solution; best residuals: {best[1]}')
