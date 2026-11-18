"""Static workspace and actual notched/keyed-component checks; not a planner.

All lengths are metres. Resets evaluate geometry, not simulated motor motion.
The nominal TCP convention is shared with B_关节与夹爪/piper_robot.py.
"""
from pathlib import Path
import sys
import csv
import json
import math
import hashlib
import itertools
from collections import Counter

import numpy as np
import pybullet as p

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "B_关节与夹爪"))
from piper_robot import Piper, ARM_NAMES, TCP_OFFSET, URDF
from component_model import load_component, grip_contact_allowed, MODEL, MARGIN
from build_component import VERSION

OUT = PROJECT / "运行验证/工作空间"
ROT = np.diag([-1., 1., -1.])
QUAT = [0., 1., 0., 0.]
POS_TOL = 0.0005
ANG_TOL = math.radians(0.5)
JOINT_MARGIN = math.radians(2)
CLEARANCE = 0.002
BLOCK = np.array([0.05, 0.03, 0.025])
DEPTH = 0.008
OPENING = 0.036
CARRY_OPENING = 0.02412  # Geometry fit, NOT a force-controlled grasp command.
TRANSFER_Z = 0.082
TCP_FROM_ORIGIN = np.array([0., 0., .014])
STACK_PITCH = .022
SKIN_TOL = .00011  # Two 0.05 mm skins at intended support contact + rounding.


class Analysis:
    def __init__(self):
        self.client = p.connect(p.DIRECT)
        self.arm = Piper(self.client, self_collision=True)
        self.r = self.arm.robot
        self.lo = np.array([self.arm.joints[n]["lower"] for n in ARM_NAMES])
        self.hi = np.array([self.arm.joints[n]["upper"] for n in ARM_NAMES])
        self.names = {-1: "dummy_link", **{v: k for k, v in self.arm.links.items()}}
        # Collapse fixed joints. Connected rigid groups / directly joined moving
        # groups overlap at their manufactured connections by design.
        group = {-1: 0, 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 6, 8: 7, 9: 8}
        edges = {(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (6, 8)}
        self.ignored_pairs = set()
        for i, j in itertools.combinations(range(-1, 10), 2):
            if group[i] == group[j] or tuple(sorted((group[i], group[j]))) in edges:
                self.ignored_pairs.add((i, j))
        plane = p.createCollisionShape(p.GEOM_PLANE)
        self.floor = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=plane)
        self.obstacles = []
        self.active_grip = None
        self.reset([0, 1.6, -1.2, 0, 1.1, 0])

    def reset(self, q, width=OPENING):
        for name, value in zip(ARM_NAMES, q):
            p.resetJointState(self.r, self.arm.joints[name]["index"], float(value))
        for name, value in zip(("joint7", "joint8"), (width / 2, -width / 2)):
            p.resetJointState(self.r, self.arm.joints[name]["index"], float(value))

    def collisions(self):
        bad = []
        for pt in p.getClosestPoints(self.r, self.r, CLEARANCE):
            a, b = sorted((pt[3], pt[4]))
            if a == b or (a, b) in self.ignored_pairs:
                continue
            bad.append(["self", self.names[a], self.names[b], pt[8]])
        for pt in p.getClosestPoints(self.r, self.floor, CLEARANCE):
            if pt[3] not in (-1, 0):
                bad.append(["floor", self.names[pt[3]], "ground", pt[8]])
        for label, body in self.obstacles:
            for piece,pt in body.robot_points(self.r,CLEARANCE):
                if body is self.active_grip and grip_contact_allowed(pt,self.arm,body.origin,piece):
                    continue
                bad.append(["obstacle", self.names[pt[3]], label, pt[8]])
        return bad

    def solve(self, xyz, previous=None, collision=True, width=OPENING):
        xyz = np.asarray(xyz, dtype=float)
        flange = xyz - ROT @ TCP_OFFSET
        seeds = [] if previous is None else [previous]
        yaw = math.atan2(xyz[1], xyz[0])
        seeds += [[yaw, 1.6, -1.2, 0, 1.1, 0],
                  [yaw, 1.0, -1.8, 0, 0.6, 0],
                  [yaw, 2.3, -0.7, 0, 1.0, 0]]
        failures = []
        for seed in seeds:
            self.reset(seed, width)
            q = np.asarray(p.calculateInverseKinematics(
                self.r, self.arm.links["gripper_base"], flange.tolist(), QUAT,
                maxNumIterations=350, residualThreshold=1e-9))[:6]
            # Equivalent revolute angles, chosen near the middle of each range.
            q += 2 * math.pi * np.round(((self.lo + self.hi) / 2 - q) / (2 * math.pi))
            self.reset(q, width)
            tcp = self.arm.tcp_frame()
            pe = float(np.linalg.norm(tcp[:3, 3] - xyz))
            ae = math.acos(float(np.clip((np.trace(ROT.T @ tcp[:3, :3]) - 1) / 2, -1, 1)))
            margin = float(np.min(np.minimum(q - self.lo, self.hi - q)))
            record = {"q_rad": q.tolist(), "position_error_m": pe,
                      "orientation_error_rad": ae, "joint_margin_rad": margin}
            if pe > POS_TOL or ae > ANG_TOL:
                record["status"] = "ik_not_converged"
            elif margin < JOINT_MARGIN:
                record["status"] = "joint_limit_or_margin"
            else:
                contacts = self.collisions() if collision else []
                record["contacts"] = contacts
                record["status"] = "clearance_rejected" if contacts else "pass"
            if record["status"] == "pass":
                return record
            failures.append(record)
        # Return the most informative failed attempt (accurate pose before IK failure).
        return min(failures, key=lambda r: (r["status"] == "ik_not_converged",
                                           max(0, JOINT_MARGIN - r["joint_margin_rad"]),
                                           r["position_error_m"]))

    def box(self, center, size=BLOCK, color=(0.7, 0.6, 0.35, 1)):
        shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=(np.asarray(size) / 2).tolist())
        visual = p.createVisualShape(p.GEOM_BOX, halfExtents=(np.asarray(size) / 2).tolist(), rgbaColor=color)
        return p.createMultiBody(baseMass=0, baseCollisionShapeIndex=shape,
                                 baseVisualShapeIndex=visual, basePosition=center)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=Analysis()
    grid=[]
    for z in (.014,.036,.082,.122):
        prev=None
        for x in np.arange(.20,.4501,.025):
            for y in np.arange(-.175,.1751,.025):
                sol=a.solve([x,y,z],prev)
                grid.append({'x_m':round(float(x),6),'y_m':round(float(y),6),'z_m':z,**sol})
                if sol['status']=='pass':prev=sol['q_rad']
        print('grid',z,dict(Counter(r['status'] for r in grid if r['z_m']==z)),flush=True)
    with (OUT/'俯抓工作空间采样.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['x_m','y_m','z_m','status','position_error_m','orientation_error_rad','joint_margin_rad','q_rad','contacts']
        w=csv.DictWriter(f,fields);w.writeheader()
        for row in grid:w.writerow({**row,'q_rad':json.dumps(row['q_rad']),'contacts':json.dumps(row.get('contacts',[]))})
    def spec(name,origin):
        tcp=np.array(origin)+TCP_FROM_ORIGIN
        above=np.array([*tcp[:2],TRANSFER_Z])
        return {'id':name,'origin_m':list(origin),
                'bbox_center_m':(np.array(origin)+[0,0,.0125]).tolist(),
                'tcp_m':tcp.tolist(),'approach_tcp_m':above.tolist(),
                'grasp_pose':a.solve(tcp),'approach_pose':a.solve(above)}
    goals=[spec(f'L{layer+1}_{col+1}',[x,.08,layer*STACK_PITCH])
           for layer in range(2) for col,x in enumerate((.24,.29,.34))]
    sources=[spec(f'S{i+1}',[x,y,0.]) for i,(y,x) in
             enumerate(itertools.product((-.07,-.13),(.21,.27,.33)))]
    def points(start,end,step=.005):
        n=max(1,math.ceil(float(np.linalg.norm(np.array(end)-start))/step))
        return [np.array(start)*(1-t)+np.array(end)*t for t in np.linspace(0,1,n+1)]
    # Probe the actual notched model, including non-contacting shoulder/end lands.
    probe=load_component([.27,-.08,0])
    grip_probe=[]
    for width in (.05,.036,.03,.026,.0242,.02412,.0241,.024,.022):
        sol=a.solve([.27,-.08,.014],width=width)
        pts=probe.robot_points(a.r,.03)
        per_link={}
        unintended=[]
        for piece,pt in pts:
            name=a.names[pt[3]]
            per_link[name]=min(per_link.get(name,1.),pt[8])
            if pt[8]<CLEARANCE and not grip_contact_allowed(pt,a.arm,probe.origin,piece):
                unintended.append([name,piece,pt[8]])
        grip_probe.append({'nominal_opening_m':width,'pose_status':sol['status'],
                           'mesh_distance_by_link_m':per_link,'unintended_contacts':unintended})
    a.solve([.27,-.08,.014],width=CARRY_OPENING)
    probe_noncontact=min(pt[8] for piece,pt in probe.robot_points(a.r,.03)
                         if not grip_contact_allowed(pt,a.arm,probe.origin,piece))
    # Negative control: identical-size solid box would block the selected closure.
    old=a.box([.27,-.08,.0125])
    negative_solid=min(pt[8] for pt in p.getClosestPoints(a.r,old,.01))
    p.removeBody(old)
    # Interface alignment checks: straight insertion and side-offset failures.
    base=load_component([.27,-.08,0])
    upper=load_component([.27,-.08,STACK_PITCH])
    mating=[]
    for dx,dy in ((0,0),(.0005,0),(0,.0005),(.0005,.0005),(.002,0),(0,.002)):
        upper.set_origin([.27+dx,-.08+dy,STACK_PITCH])
        pts=base.other_points(upper,.002)
        distance=min(pt[8] for _,_,pt in pts)
        mating.append({'offset_xy_m':[dx,dy],'minimum_distance_m':distance,
                       'status':'pass' if distance>=-SKIN_TOL else 'interference'})
    upper.remove();base.remove();probe.remove()
    for source in sources:
        a.obstacles.append((source['id'],load_component(source['origin_m'],(.18,.48,.78,1))))
    carried=load_component([0,0,-10])
    routes=[]
    for index,(goal,source) in enumerate(zip(goals,sources)):
        source_pair=next(pair for pair in a.obstacles if pair[0]==source['id'])
        src_body=source_pair[1]
        records=[];previous=None
        def sample(xyz,width,phase,body=None):
            nonlocal previous
            sol=a.solve(xyz,previous,width=width)
            if sol['status']=='pass':previous=sol['q_rad']
            row={'phase':phase,'tcp_m':np.asarray(xyz).tolist(),'opening_m':float(width),**sol}
            if body is not None:
                extra=[]
                for piece,pt in body.robot_points(a.r,CLEARANCE):
                    if not grip_contact_allowed(pt,a.arm,body.origin,piece):
                        extra.append(['carried_robot',a.names[pt[3]],piece,pt[8]])
                for _,pt in body.floor_points(a.floor,CLEARANCE):
                    supported=(phase=='lift' or (phase=='lower' and goal['origin_m'][2]==0))
                    if not (supported and pt[8]>=-SKIN_TOL):extra.append(['carried_floor',pt[8]])
                for label,obstacle in a.obstacles:
                    # Adjacent end faces and the block directly underneath are
                    # intended mating neighbors only during final descent.
                    matched=any(g['id']==label and
                               np.all(np.abs(np.array(goal['origin_m'])-g['origin_m'])<=[.050001,.000001,.022001])
                               for g in goals[:index])
                    for i,j,pt in body.other_points(obstacle,CLEARANCE):
                        if phase=='lower' and matched and pt[8]>=-SKIN_TOL:continue
                        extra.append(['carried_obstacle',label,i,j,pt[8]])
                row['carry_contacts']=extra
                if extra:row['status']='carry_clearance_rejected'
            records.append(row)
        for xyz in points(source['approach_tcp_m'],source['tcp_m']):sample(xyz,OPENING,'approach')
        a.active_grip=src_body
        for width in np.linspace(OPENING,CARRY_OPENING,25):sample(source['tcp_m'],width,'close')
        a.active_grip=None
        a.obstacles.remove(source_pair);src_body.remove()
        nodes=[source['tcp_m'],source['approach_tcp_m'],goal['approach_tcp_m'],goal['tcp_m']]
        for phase,(start,end) in zip(('lift','transfer','lower'),zip(nodes,nodes[1:])):
            for xyz in points(start,end,.0005 if phase=='lower' else .005):
                carried.set_origin(xyz-TCP_FROM_ORIGIN)
                sample(xyz,CARRY_OPENING,phase,carried)
        carried.set_origin([0,0,-10])
        placed=load_component(goal['origin_m'])
        a.obstacles.append((goal['id'],placed));a.active_grip=placed
        for width in np.linspace(CARRY_OPENING,OPENING,25):sample(goal['tcp_m'],width,'release')
        a.active_grip=None
        for xyz in points(goal['tcp_m'],goal['approach_tcp_m']):sample(xyz,OPENING,'retreat')
        if index+1<len(sources):
            for xyz in points(goal['approach_tcp_m'],sources[index+1]['approach_tcp_m']):sample(xyz,OPENING,'empty_return')
        jump=max(float(np.max(np.abs(np.array(s2['q_rad'])-s1['q_rad']))) for s1,s2 in zip(records,records[1:]))
        route={'source_id':source['id'],'goal_id':goal['id'],'states':records,
               'max_joint_step_rad':jump,
               'status':'pass' if all(s['status']=='pass' for s in records) and jump<math.radians(10) else 'failed'}
        routes.append(route)
        print('route',goal['id'],route['status'],dict(Counter(s['status'] for s in records)),flush=True)
    states=[s for r in routes for s in r['states']]
    summary={
        'date':'2026-10-29','component_version':VERSION,
        'urdf_sha256':hashlib.sha256(URDF.read_bytes()).hexdigest(),
        'component_parameters':json.loads((MODEL/'parameters.json').read_text()),
        'method':'static IK and convex-part closest-point checks; no motor or frictional grasp simulation',
        'thresholds':{'position_m':POS_TOL,'orientation_rad':ANG_TOL,'joint_margin_rad':JOINT_MARGIN,
                      'noncontact_clearance_m':CLEARANCE,'component_collision_margin_m':MARGIN,
                      'support_skin_tolerance_m':SKIN_TOL,'path_step_m':.005,'final_descent_step_m':.0005,
                      'jaw_sweep_steps_each':25},
        'tcp_offset_in_gripper_m':TCP_OFFSET.tolist(),'top_down_quaternion_xyzw':QUAT,
        'tcp_from_component_origin_m':TCP_FROM_ORIGIN.tolist(),
        'ignored_self_pairs':[[a.names[i],a.names[j]] for i,j in sorted(a.ignored_pairs)],
        'grid_count':len(grid),'grid_status':dict(Counter(r['status'] for r in grid)),
        'grid_by_height':[{'tcp_z_m':z,'status':dict(Counter(r['status'] for r in grid if r['z_m']==z))} for z in (.014,.036,.082,.122)],
        'block_dimensions_m':BLOCK.tolist(),'stack_pitch_m':STACK_PITCH,'assembled_height_m':.047,
        'open_approach_m':OPENING,'carry_proxy_opening_m':CARRY_OPENING,
        'route_sample_count':len(states),'phase_counts':dict(Counter(s['phase'] for s in states)),
        'minimum_joint_margin_deg':min(math.degrees(s['joint_margin_rad']) for s in states),
        'max_position_error_m':max(s['position_error_m'] for s in states),
        'max_orientation_error_deg':max(math.degrees(s['orientation_error_rad']) for s in states),
        'sources':sources,'goals':goals,'finger_groove_probe':grip_probe,
        'non_grip_surface_minimum_gap_at_reference_m':probe_noncontact,
        'negative_control_solid_box_minimum_gap_m':negative_solid,
        'mating_offset_checks':mating,'routes':routes,
        'limitations':['geometry-only, fixed base, flat ground','static component pieces move together by code, not by a grasp constraint',
                      'no continuous collision certificate, motor tracking, frictional grasp, payload, structural strength, or dynamics',
                      'guide features are loose locating features, not a verified locking connection',
                      'no proof that chamfers passively correct positioning errors','finite IK failures are not a proof of unreachability']}
    (OUT/'工作空间验证结果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'建议抓放位置.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['id','origin_x_m','origin_y_m','origin_z_m','bbox_center_z_m','tcp_z_m','approach_tcp_z_m','pose_status','approach_status',*[f'q{i}_rad' for i in range(1,7)]])
        for g in sources+goals:w.writerow([g['id'],*g['origin_m'],g['bbox_center_m'][2],g['tcp_m'][2],TRANSFER_Z,g['grasp_pose']['status'],g['approach_pose']['status'],*g['grasp_pose']['q_rad']])
    p.disconnect(a.client)
    print('samples',len(states),'phase counts',summary['phase_counts'],flush=True)
    if any(r['status']!='pass' for r in routes):raise SystemExit('Geometry checks failed; see JSON.')
    assert negative_solid<-.003,'Negative control did not block the narrow grasp'
    assert all(t['status']=='pass' for t in mating[:4]) and all(t['status']=='interference' for t in mating[4:])


if __name__=='__main__':
    main()
