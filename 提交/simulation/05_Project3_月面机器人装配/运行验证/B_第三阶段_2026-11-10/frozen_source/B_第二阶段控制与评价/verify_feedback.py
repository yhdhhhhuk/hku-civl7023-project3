"""Independent one-link test of tuple[3], sensor wrench and substep semantics."""
import argparse,json
from pathlib import Path
import pybullet as p
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
out=args.output.parent;out.mkdir(parents=True,exist_ok=True)
results=[]
for substeps in [1,4]:
 c=p.connect(p.DIRECT);p.setTimeStep(1/240);p.setPhysicsEngineParameter(numSubSteps=substeps)
 shape=p.createCollisionShape(p.GEOM_BOX,halfExtents=[.1,.02,.02])
 b=p.createMultiBody(baseMass=0,linkMasses=[1],linkCollisionShapeIndices=[shape],linkVisualShapeIndices=[-1],linkPositions=[[0,0,0]],linkOrientations=[[0,0,0,1]],linkInertialFramePositions=[[.1,0,0]],linkInertialFrameOrientations=[[0,0,0,1]],linkParentIndices=[0],linkJointTypes=[p.JOINT_REVOLUTE],linkJointAxis=[[0,1,0]])
 p.enableJointForceTorqueSensor(b,0,1);p.setGravity(0,0,-1.62)
 # Saturated POSITION_CONTROL must return specified signed motor effort.
 p.setJointMotorControl2(b,0,p.POSITION_CONTROL,targetPosition=1,force=.02)
 p.stepSimulation();state=p.getJointState(b,0)
 assert abs(state[3]-.02)<1e-10
 results.append(dict(substeps=substeps,position_control_saturated_state=state,expected_motor_Nm=.02,passed=True))
 # Static compensation for a known COM offset: |tau|=m*g*lever.
 p.resetJointState(b,0,0);p.setJointMotorControl2(b,0,p.POSITION_CONTROL,targetPosition=0,force=10,positionGain=.5)
 for _ in range(2400):p.stepSimulation()
 state=p.getJointState(b,0);expected=.162
 print(substeps,state,expected)

 assert abs(abs(state[3])*substeps-expected)<1e-5
 results[-1].update(static_state=state,expected_static_magnitude_Nm=expected,raw_to_last_substep_effort_factor=substeps)
 p.disconnect()
# Zero-gravity acceleration checks identify the effective saturation scaling.
for kind,unit in [(p.JOINT_REVOLUTE,'Nm'),(p.JOINT_PRISMATIC,'N')]:
 for n in [1,4]:
  c=p.connect(p.DIRECT);p.setTimeStep(1/240);p.setPhysicsEngineParameter(numSubSteps=n)
  shape=p.createCollisionShape(p.GEOM_BOX,halfExtents=[.1,.02,.02])
  b=p.createMultiBody(baseMass=0,linkMasses=[1],linkCollisionShapeIndices=[shape],linkVisualShapeIndices=[-1],linkPositions=[[0,0,0]],linkOrientations=[[0,0,0,1]],linkInertialFramePositions=[[0,0,0]],linkInertialFrameOrientations=[[0,0,0,1]],linkParentIndices=[0],linkJointTypes=[kind],linkJointAxis=[[0,1,0]])
  p.changeDynamics(b,0,localInertiaDiagonal=[.01,.01,.01],linearDamping=0,angularDamping=0)
  p.setJointMotorControl2(b,0,p.POSITION_CONTROL,targetPosition=1,force=.02)
  p.stepSimulation();state=p.getJointState(b,0)
  generalized_mass=p.getDynamicsInfo(b,0)[2][1] if kind==p.JOINT_REVOLUTE else 1.
  effective=state[1]*240*generalized_mass
  print(kind,n,state,effective,p.getDynamicsInfo(b,0))

  assert abs(effective-.02*n)<1e-10
  results.append(dict(test='zero_gravity_acceleration',unit=unit,substeps=n,raw_motor=state[3],inferred_effective_from_acceleration=effective,expected=.02*n,passed=True))
  p.disconnect()
args.output.write_text(json.dumps({'api_version':p.getAPIVersion(),'meaning':'getJointState tuple: q,dq,reaction[6],appliedJointMotorTorque; sampled after external step. This build returns last motor impulse / external dt; multiply by numSubSteps for last-substep equivalent effort, verified by static balance. Substep extrema and mean unavailable. Reaction is a separate sensor wrench.','tests':results},indent=2),encoding='utf8')
print('feedback tests passed')
