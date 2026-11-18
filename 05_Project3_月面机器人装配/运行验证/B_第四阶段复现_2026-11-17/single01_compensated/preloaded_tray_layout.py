"""Screen all preloaded fan-tray pickup poses using B kinematics."""
from pathlib import Path
import sys,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from C_仿真与装配.local_paths import PROJECT as ROOT
import numpy as np
import pybullet as p
from scipy.spatial.transform import Rotation
from piper_robot import Piper
from kinematics import Kinematics

def tray_slots():
 slots=[]
 for radius,angles in [(.20,[-110,-90,-70,-50,-30]),(.265,[-110,-90,-70,-50,-30]),(.33,[-110,-94,-78,-62,-46,-30])]:
  for degrees in angles:
   theta=math.radians(degrees);slots.append({'position':[radius*math.cos(theta),radius*math.sin(theta),0.],'yaw':theta+math.pi/2,'radius':radius,'angle_deg':degrees})
 return slots

def main():
 out=ROOT/'运行验证/C_装配运行/料盘预检';out.mkdir(parents=True,exist_ok=True)
 c=p.connect(p.DIRECT);robot=Piper(c,self_collision=True);kin=Kinematics(robot.world_from_root);seed=[0,.8,-1.2,0,.4,0];records=[]
 for i,s in enumerate(tray_slots()):
  for height in [.014,.05,.082]:
   T=np.eye(4);T[:3,:3]=Rotation.from_euler('z',s['yaw']).as_matrix()@np.diag([-1.,1.,-1.]);T[:3,3]=[*s['position'][:2],height]
   try:ik=kin.inverse(T,seed);records.append({'slot':i+1,'height':height,'ok':True,'ik':ik})
   except ValueError as e:records.append({'slot':i+1,'height':height,'ok':False,'error':str(e)})
 print('IK:',sum(x['ok'] for x in records),'/',len(records));print([(x['slot'],x['height']) for x in records if not x['ok']])
 (out/'ik_screen.json').write_text(json.dumps({'slots':tray_slots(),'records':records},indent=2),encoding='utf8');p.disconnect()
if __name__=='__main__':main()
