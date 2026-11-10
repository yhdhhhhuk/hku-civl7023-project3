"""Inspect actual loaded PiPER dynamic properties with the frozen loading flags."""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np
import pybullet as p
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'B_关节与夹爪')]
from C_仿真与装配.local_paths import bullet_path
import piper_robot
piper_robot.URDF=Path(bullet_path(piper_robot.URDF));from piper_robot import Piper
c=p.connect(p.DIRECT);robot=Piper(c,self_collision=True)
xml=ET.parse(piper_robot.URDF).getroot();bylink={x.get('name'):x for x in xml.findall('link')}
rows=[]
for index in range(-1,p.getNumJoints(robot.robot,physicsClientId=c)):
 name=p.getBodyInfo(robot.robot,physicsClientId=c)[0].decode() if index==-1 else p.getJointInfo(robot.robot,index,physicsClientId=c)[12].decode()
 d=p.getDynamicsInfo(robot.robot,index,physicsClientId=c);link=bylink.get(name);inertial=link.find('inertial') if link is not None else None
 supplied={}
 if inertial is not None:
  supplied={x.tag:dict(x.attrib) for x in inertial}
 rows.append(dict(link_index=index,link_name=name,loaded_mass_kg=d[0],loaded_principal_inertia_diagonal_kg_m2=list(d[2]),local_inertial_position_m=list(d[3]),local_inertial_orientation_xyzw=list(d[4]),lateral_friction=d[1],restitution=d[5],collision_margin_m=d[-1],supplied_URDF_inertial=supplied))
p.disconnect(c)
out=ROOT/'运行验证/B_第三阶段_2026-11-10/robot_loaded_dynamics.json'
out.write_text(json.dumps(dict(api_version=p.getAPIVersion(),URDF_sha256=hashlib.sha256(piper_robot.URDF.read_bytes()).hexdigest(),loader='Piper(client,self_collision=True)',flags=int(p.URDF_USE_SELF_COLLISION),uses_URDF_USE_INERTIA_FROM_FILE_flag=False,interpretation='Robot uses the existing Bullet importer inertia treatment; record actual dynamics instead of assuming URDF tensor is retained. Components separately use URDF_USE_INERTIA_FROM_FILE with verified candidate COM inertia.',links=rows),ensure_ascii=False,indent=2),encoding='utf8')
print('Robot dynamic properties recorded for',len(rows),'links')
