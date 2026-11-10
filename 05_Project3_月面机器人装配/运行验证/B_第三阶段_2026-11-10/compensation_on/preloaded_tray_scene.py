"""A coplanar flat stock plate; one uniform physical floor supports all parts."""
import pybullet as p

def create_surfaces(client=0):
    collision=p.createCollisionShape(p.GEOM_PLANE,physicsClientId=client)
    ground=p.createVisualShape(p.GEOM_BOX,halfExtents=[1,1,.003],visualFramePosition=[0,0,-.0032],rgbaColor=[.75,.78,.80,1],physicsClientId=client)
    floor=p.createMultiBody(0,collision,ground,physicsClientId=client)
    p.changeDynamics(floor,-1,lateralFriction=.6,physicsClientId=client)
    plate=p.createVisualShape(p.GEOM_BOX,halfExtents=[.24,.1525,.001],rgbaColor=[.17,.23,.28,1],physicsClientId=client)
    tray=p.createMultiBody(0,baseVisualShapeIndex=plate,basePosition=[.085,-.2175,-.001],physicsClientId=client)
    return floor,tray
