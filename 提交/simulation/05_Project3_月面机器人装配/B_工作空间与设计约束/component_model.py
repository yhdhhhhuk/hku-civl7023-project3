"""Load the concave component as 34 convex parts moved together geometrically.

This static loader is for geometry checks. It does not certify mass/inertia.
Do not load the complete STL as one convex collision mesh: cavities disappear.
"""
import json
from pathlib import Path
import numpy as np
import pybullet as p

MODEL = Path(__file__).resolve().parent / "构件模型"
MARGIN = 0.00005


def load_component(origin, color=(.82,.55,.18,1)):
    params=json.loads((MODEL/"parameters.json").read_text())
    shapes=[]
    for filename in params['collision_parts']:
        raw=(MODEL/filename).read_bytes()
        triangles=np.frombuffer(raw,dtype=np.dtype([
            ('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')]),offset=84)
        vertices=np.unique(triangles['vertices'].reshape(-1,3),axis=0)
        # vertices creates one direct hull; filename imports may add another
        # compound wrapper, preventing the margin from reaching its children.
        shapes.append(p.createCollisionShape(p.GEOM_MESH,vertices=vertices.tolist()))
    visual=p.createVisualShape(p.GEOM_MESH,fileName=str(MODEL/"groove_key_block_m.stl"),rgbaColor=color)
    # This Bullet build applies collisionMargin to base shapes only. Represent
    # the static partition by base bodies, moved together by Component.set_origin.
    bodies=[]
    for i,shape in enumerate(shapes):
        body=p.createMultiBody(0,shape,visual if i==0 else -1,basePosition=origin)
        p.changeDynamics(body,-1,collisionMargin=MARGIN)
        assert abs(p.getDynamicsInfo(body,-1)[-1]-MARGIN)<1e-9
        bodies.append(body)
    return Component(bodies,origin)


class Component:
    def __init__(self,bodies,origin):
        self.bodies=bodies
        self.origin=np.array(origin,dtype=float)
        self.local_bounds=np.asarray([p.getAABB(b) for b in bodies])-self.origin

    def set_origin(self,origin):
        self.origin=np.array(origin,dtype=float)
        for b in self.bodies:
            p.resetBasePositionAndOrientation(b,self.origin,[0,0,0,1])

    def remove(self):
        for b in self.bodies:p.removeBody(b)

    def robot_points(self,robot,distance):
        return [(i,pt) for i,b in enumerate(self.bodies)
                for pt in p.getClosestPoints(robot,b,distance)]

    def other_points(self,other,distance):
        first=self.local_bounds+self.origin
        second=other.local_bounds+other.origin
        # AABB pruning only discards pairs that are already farther apart than
        # the distance query. Exact convex queries decide all remaining pairs.
        gap=np.maximum(second[None,:,0,:]-first[:,None,1,:],
                       first[:,None,0,:]-second[None,:,1,:])
        pairs=np.argwhere(np.all(gap<=distance,axis=2))
        return [(int(i),int(j),pt) for i,j in pairs
                for pt in p.getClosestPoints(self.bodies[i],other.bodies[j],distance)]

    def floor_points(self,floor,distance):
        return [(i,pt) for i,b in enumerate(self.bodies)
                if self.local_bounds[i,0,2]+self.origin[2]<=distance
                for pt in p.getClosestPoints(b,floor,distance)]


def grip_contact_allowed(pt, arm, origin, piece):
    # getClosestPoints(robot, part): only the two inner vertical grip faces
    # on convex piece 27 are intended to contact fingers. No end-post exemption.
    local=[pt[6][i]-origin[i] for i in range(3)]
    return (pt[3] in (arm.links['link7'],arm.links['link8']) and piece==27
            and abs(local[0]) <= .0191 and .010-1e-4 <= local[2] <= .0221
            and abs(abs(local[1])-.011) <= .0002
            and abs(pt[7][1])>.95 and pt[8]>=-.0001)
