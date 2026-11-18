"""Conservative AABB rejection only; near pairs still use exact Bullet queries."""
import math
import pybullet as p

def may_touch(a,b,distance=0.):
    if not all(math.isfinite(v) for box in [a,b] for end in box for v in end):return True
    return all(a[0][i]<=b[1][i]+distance and b[0][i]<=a[1][i]+distance for i in range(3))

def robot_boxes(robot,client):
    return [p.getAABB(robot,j,physicsClientId=client) for j in range(-1,p.getNumJoints(robot,physicsClientId=client))]

def robot_may_touch(boxes,other,distance=0.):
    return any(may_touch(box,other,distance) for box in boxes)
