"""All 16 components preloaded before time zero; no in-run spawning."""
import argparse,csv,hashlib,json,sys,time,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import numpy as np
import pybullet as p
from scipy.spatial.transform import Rotation
from C_仿真与装配.local_paths import PROJECT, bullet_path
from C_仿真与装配.preloaded_planning_fast import move_planned
from C_仿真与装配.collision_broadphase import may_touch,robot_boxes,robot_may_touch
from C_仿真与装配.preloaded_tray_layout import tray_slots
from C_仿真与装配.preloaded_tray_scene import create_surfaces
from C_仿真与装配.gripper_release import open_before_detach, RELEASE_FORCES_N, RELEASE_STAGE_SECONDS, CONTACT_BREAKING_FACTOR
sys.path.insert(0,str(PROJECT/'B_关节与夹爪'))
sys.path.insert(0,str(PROJECT/'B_基础控制与雅可比'))
import piper_robot
piper_robot.URDF=Path(bullet_path(piper_robot.URDF))
from controller import PoseController,collision_pairs,measured_tcp
from piper_robot import Piper,DT
MODEL=PROJECT/'B_工作空间与设计约束/构件模型'
PARAM=json.loads((MODEL/'parameters.json').read_text(encoding='utf8'))
COM=np.array([0.,0.,.011])
MASS=.07
INERTIA=MASS/12*np.array([.030**2+.025**2,.050**2+.025**2,.050**2+.030**2])
CLOSING_FORCE_N=1.
PHYSICS_SUBSTEPS=4
CREATIONS=[]
PHYSICS_STEPS=0

def component(origin,client,visual=True):
    # One rigid base with 34 convex children: base margin reaches every child.
    # Fixed multibody links ignore changeDynamics(collisionMargin) in this build.
    import shutil
    cache=ROOT/'.cache/C_仿真与装配/构件网格'; cache.mkdir(parents=True,exist_ok=True)
    inertia=INERTIA.tolist()
    xml=f'<robot name="groove_key"><link name="body"><inertial><origin xyz="{COM[0]} {COM[1]} {COM[2]}"/><mass value="{MASS}"/>'
    xml+=f'<inertia ixx="{inertia[0]}" iyy="{inertia[1]}" izz="{inertia[2]}" ixy="0" ixz="0" iyz="0"/></inertial>'
    for i,filename in enumerate(PARAM['collision_parts']):
        shutil.copyfile(MODEL/filename,cache/f'part_{i}.stl')
        xml+=f'<collision><geometry><mesh filename="part_{i}.stl"/></geometry></collision>'
    if visual:
        shutil.copyfile(MODEL/'groove_key_block_m.stl',cache/'component.stl')
        xml+='<visual><geometry><mesh filename="component.stl"/></geometry><material name="orange"><color rgba=".9 .5 .15 1"/></material></visual>'
    xml+='</link></robot>'
    path=cache/('dynamic_visual.urdf' if visual else 'dynamic_collision.urdf')
    path.write_text(xml,encoding='utf8')
    body=p.loadURDF(bullet_path(path),basePosition=list(origin),flags=p.URDF_USE_INERTIA_FROM_FILE,physicsClientId=client)
    p.changeDynamics(body,-1,collisionMargin=.00005,lateralFriction=.6,restitution=0,physicsClientId=client)
    CREATIONS.append({'client':client,'body_id':body,'created_at_physics_step':PHYSICS_STEPS})
    return body,inertia

def core_contact(pt, body, client=0):
    bp,bo=p.getBasePositionAndOrientation(body,physicsClientId=client)
    local=Rotation.from_quat(bo).inv().apply(np.array(pt[6])-bp)+COM
    return abs(local[0])<.0191 and abs(abs(local[1])-.011)<.001 and .009<local[2]<.023


def main():
    global MASS,COM,INERTIA
    started=time.time()
    ap=argparse.ArgumentParser(); ap.add_argument("--payload-config",choices=["legacy70g","A-candidate"],default="legacy70g"); ap.add_argument("--telemetry",action="store_true"); ap.add_argument('--limit',type=int,default=16); ap.add_argument('--video',action='store_true'); ap.add_argument('--gui',action='store_true'); ap.add_argument('--output',type=Path,default=ROOT/'运行验证/C_装配运行'/time.strftime('%Y%m%d_%H%M%S')); args=ap.parse_args()
    if not 1 <= args.limit <= 16: ap.error('--limit must be between 1 and 16')
    out=args.output; out.mkdir(parents=True,exist_ok=True)
    candidate_path=ROOT/'A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json'
    if args.payload_config=='A-candidate':
        candidate=json.loads(candidate_path.read_text(encoding='utf8'))
        tensor=np.array(candidate['inertia_about_COM_expressed_in_geometry_axes_kg_m2'])
        if not np.allclose(tensor,np.diag(np.diag(tensor)),atol=1e-15,rtol=0):
            raise ValueError('Non-diagonal tensor requires explicit inertial-frame conversion')
        assert np.linalg.eigvalsh(tensor).min()>0
        MASS=candidate['mass_kg'];COM=np.array(candidate['centre_of_mass_in_geometry_frame_m']);INERTIA=np.diag(tensor)
    provenance={'started_local':time.strftime('%Y-%m-%d %H:%M:%S %z'),'argv':sys.argv,'python':sys.version,'payload_config':args.payload_config,'candidate_sha256':hashlib.sha256(candidate_path.read_bytes()).hexdigest(),'source_hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['B_关节与夹爪','B_基础控制与雅可比','B_第二阶段控制与评价','C_仿真与装配'] for f in (ROOT/folder).glob('*.py')}}
    (out/'run_manifest.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf8')
    import shutil
    for file in [Path(__file__),ROOT/'C_仿真与装配/gripper_release.py',ROOT/'C_仿真与装配/polygon_planning.py',ROOT/'C_仿真与装配/preloaded_planning_fast.py',ROOT/'C_仿真与装配/collision_broadphase.py',ROOT/'C_仿真与装配/motion_planning.py',ROOT/'C_仿真与装配/preloaded_tray_layout.py',ROOT/'C_仿真与装配/preloaded_tray_scene.py',ROOT/'C_仿真与装配/local_paths.py']:
        shutil.copyfile(file,out/file.name)
    cid=p.connect(p.GUI if args.gui else p.DIRECT)
    # Set before contact manifolds are created. Changing this after restoring
    # a Bullet checkpoint does not replace that checkpoint's cached thresholds.
    p.setPhysicsEngineParameter(contactBreakingThreshold=CONTACT_BREAKING_FACTOR,
        numSubSteps=PHYSICS_SUBSTEPS,physicsClientId=cid)
    robot=Piper(cid,self_collision=True); ignored=collision_pairs(robot)
    floor,tray=create_surfaces(cid); p.setGravity(0,0,-1.62)
    p.changeDynamics(floor,-1,lateralFriction=.6)
    robot.reset_demo_pose(); robot.command_gripper(.036)
    for j,q in [(8,.018),(9,-.018)]: p.resetJointState(robot.robot,j,q)
    order=[0,1,7,2,6,3,5,4]
    targets=[];yaws=[]
    for z in [0.,.022]:
        for sector in order:
            theta=sector*math.pi/4
            targets.append([.26+.076*math.cos(theta),.03+.076*math.sin(theta),z])
            yaws.append((theta+math.pi)%math.pi-math.pi/2)
    targets=targets[:args.limit];yaws=yaws[:args.limit];count=len(targets)
    slots=tray_slots();sources=[slot['position'] for slot in slots];source_yaws=[slot['yaw'] for slot in slots]
    bodies=[component(pos,cid)[0] for pos in sources]
    for b,pos,yaw in zip(bodies,sources,source_yaws):
        p.resetBasePositionAndOrientation(b,(np.array(pos)+COM).tolist(),Rotation.from_euler('z',yaw).as_quat())
    initial_inventory=[{'item':i+1,'body_id':b,'position':list(p.getBasePositionAndOrientation(b)[0]),'orientation':list(p.getBasePositionAndOrientation(b)[1])} for i,b in enumerate(bodies)]
    initial_scene_body_count=p.getNumBodies(cid);body_count_min=initial_scene_body_count;body_count_max=initial_scene_body_count
    (out/'initial_inventory.json').write_text(json.dumps(initial_inventory,indent=2),encoding='utf8')
    inventory_rows=[]
    inertia=INERTIA.tolist()
    dynamics=p.getDynamicsInfo(bodies[0],-1,physicsClientId=cid)
    assert abs(dynamics[0]-MASS)<1e-12 and np.allclose(dynamics[2],INERTIA,atol=1e-14,rtol=0) and np.allclose(dynamics[3],COM,atol=1e-14,rtol=0)
    assert np.allclose(dynamics[4],[0,0,0,1],atol=1e-14)
    (out/'loaded_payload.json').write_text(json.dumps({'mass_kg':dynamics[0],'inertia_diagonal_kg_m2':dynamics[2],'inertial_position_m':dynamics[3],'inertial_orientation_xyzw':dynamics[4],'geometry_origin_reconstruction_max_error_m':max(float(np.linalg.norm(np.array(p.getBasePositionAndOrientation(b)[0])-Rotation.from_quat(p.getBasePositionAndOrientation(b)[1]).apply(COM)-pos)) for b,pos in zip(bodies,sources))},indent=2))
    from B_第二阶段控制与评价.telemetry import Telemetry
    telemetry=Telemetry(robot,out/'joint_full_trace.csv') if args.telemetry else None
    body=bodies[0]; active=0; placed=[]; item_results=[]; snapshots=[]
    support=None; support_shadow=None; support_checks=0; payload_checks=0; min_support_distance=1.
    planning_log=[]
    events=[]; rows=[]; release_samples=[]; violations=[]; phase='initialize'; steps=0; constraint=None; relative=None; maxz=0.; success=False; error=None; moves=[]
    writer=None
    if args.video:
        import imageio.v2 as imageio
        writer=imageio.get_writer(str(out/'assembly.mp4'),fps=5,codec='libx264',quality=7)
    view=p.computeViewMatrixFromYawPitchRoll([.09,-.10,.16],1.25,53,-40,0,2); proj=p.computeProjectionMatrixFOV(43,4/3,.01,3)
    p.resetDebugVisualizerCamera(1.25,53,-40,[.09,-.10,.16])
    projection=np.asarray(proj).reshape(4,4).T@np.asarray(view).reshape(4,4).T
    def origin():
        bp,bo=p.getBasePositionAndOrientation(body); return np.array(bp)-Rotation.from_quat(bo).apply(COM),bo
    def contacts():
        return [c for c in p.getContactPoints(robot.robot,body)]
    def observe():
        nonlocal steps,maxz,min_support_distance,body_count_min,body_count_max
        global PHYSICS_STEPS
        steps+=1;PHYSICS_STEPS=steps
        if telemetry:telemetry.sample(steps,DT,active+1,phase,constraint)
        current_body_count=p.getNumBodies(cid);body_count_min=min(body_count_min,current_body_count);body_count_max=max(body_count_max,current_body_count)
        if current_body_count!=initial_scene_body_count:raise RuntimeError('Scene body count changed during assembly')
        op,oq=origin(); maxz=max(maxz,float(op[2]))
        bad=[]
        for pt in p.getContactPoints(robot.robot):
            if pt[8]>=-.0001: continue
            other=pt[2]; link=pt[3]
            if other==floor and link in [-1,0]: continue
            if other==body and link in [8,9] and core_contact(pt,body) and pt[8]>=-.0005 and phase in ['close','lift','transfer','lower','release']: continue
            bad.append([pt[1],other,link,pt[4],pt[8],list(pt[6]), (Rotation.from_quat(oq).inv().apply(np.array(pt[6])-op)).tolist()])
        bodyset=set(bodies)
        for pt in p.getContactPoints():
            if pt[8]>=-.0002: continue
            if pt[1] in bodyset and pt[2] in bodyset: bad.append(['component_pair',pt[1],pt[2],pt[8]])
            if {pt[1],pt[2]}=={body,floor}: bad.append(['payload_floor',pt[8]])
        if bad: violations.append({'step':steps,'phase':phase,'contacts':bad}); raise RuntimeError(f'Unexpected collision {bad[0]}')
        if steps%12==0:
            cs=contacts(); vals=robot.values(); tcp=measured_tcp(robot)[:3,3]
            rows.append({'time_s':steps*DT,'phase':phase,'item':active+1,'scene_body_count':current_body_count,'object_x':op[0],'object_y':op[1],'object_z':op[2],'object_qx':oq[0],'object_qy':oq[1],'object_qz':oq[2],'object_qw':oq[3],'tcp_x':tcp[0],'tcp_y':tcp[1],'tcp_z':tcp[2],'opening_m':vals['joint7']-vals['joint8'],'left_contacts':sum(pt[3]==8 for pt in cs),'right_contacts':sum(pt[3]==9 for pt in cs),'attached':constraint is not None})
        if steps%120==0:
            for idx,o in enumerate(bodies):
                bp,bo=p.getBasePositionAndOrientation(o)
                inventory_rows.append({'time_s':steps*DT,'item':idx+1,'x':bp[0],'y':bp[1],'z':bp[2],'qx':bo[0],'qy':bo[1],'qz':bo[2],'qw':bo[3],'state':'placed' if idx+1 in placed else ('in_progress' if idx==active and phase in ['lift','transfer','lower','release','retreat','settle'] else 'stock')})
        if (writer and steps%48==0) or steps==24:
            from PIL import Image,ImageDraw
            image=p.getCameraImage(640,480,view,proj,renderer=p.ER_TINY_RENDERER)
            canvas=Image.fromarray(np.asarray(image[2],dtype=np.uint8).reshape(480,640,4)); draw=ImageDraw.Draw(canvas)
            draw.text((10,10),f'PRELOADED 16 | placed {len(placed)}/{count} | item {active+1} | {phase} | {steps*DT:.1f}s',fill='black')
            draw.text((10,28),f'34 CONVEX / {args.payload_config} / ASSISTED GRASP',fill='black')
            if steps==24:canvas.save(out/'first_frame.png')
            if writer:writer.append_data(np.asarray(canvas)[:,:,:3])
        if args.gui: time.sleep(DT)
    control=PoseController(robot)
    shadow,_=component([.27,-.07,0],control.guard.client,False)
    shadows=[component(pos,control.guard.client,False)[0] for pos in sources]
    other_pose_cache={}
    original_guard=control.guard.check
    def guard(q,width=.036):
        nonlocal support_checks,payload_checks
        values=robot.values()
        actual_width=values['joint7']-values['joint8']
        hit=original_guard(q,actual_width)
        if hit: return hit
        for name in ['joint7','joint8']:
            p.resetJointState(control.guard.arm.robot,control.guard.arm.joints[name]['index'],values[name],physicsClientId=control.guard.client)
        if relative is None: bp,bo=p.getBasePositionAndOrientation(body)
        else:
            s=p.getLinkState(control.guard.arm.robot,7,computeForwardKinematics=True,physicsClientId=control.guard.client)
            bp,bo=p.multiplyTransforms(s[0],s[1],*relative)
        p.resetBasePositionAndOrientation(shadow,bp,bo,physicsClientId=control.guard.client)
        for pt in p.getClosestPoints(control.guard.arm.robot,shadow,.00005,physicsClientId=control.guard.client):
            if pt[3] in [8,9] and core_contact(pt,shadow,control.guard.client) and pt[8]>=-.0005: continue
            return ['component',pt[3],pt[4],pt[8]]
        p.getLinkState(control.guard.arm.robot,9,computeForwardKinematics=True,physicsClientId=control.guard.client)
        boxes=robot_boxes(control.guard.arm.robot,control.guard.client)
        payload_box=p.getAABB(shadow,physicsClientId=control.guard.client)
        for idx,other in enumerate(bodies):
            if other==body: continue
            sp,so=p.getBasePositionAndOrientation(other)
            if other_pose_cache.get(idx)!=(sp,so):
                p.resetBasePositionAndOrientation(shadows[idx],sp,so,physicsClientId=control.guard.client);other_pose_cache[idx]=(sp,so)
            other_box=p.getAABB(shadows[idx],physicsClientId=control.guard.client)
            support_checks+=1
            if robot_may_touch(boxes,other_box,.00005):
                for pt in p.getClosestPoints(control.guard.arm.robot,shadows[idx],.00005,physicsClientId=control.guard.client):
                    return ['robot_environment',idx+1,pt[3],pt[8]]
            if relative is not None and may_touch(payload_box,other_box):
                payload_checks+=1
                for pt in p.getClosestPoints(shadow,shadows[idx],0,physicsClientId=control.guard.client):
                    if pt[8]<getattr(control.guard,'payload_limit',-.0002): return ['payload_environment',idx+1,pt[8]]
        # Carried geometry must not penetrate the ground; initial support allowed.
        if relative is not None:
            for pt in p.getClosestPoints(shadow,control.guard.floor,0,physicsClientId=control.guard.client):
                if pt[8]<-.0002: return ['payload_floor',pt[8]]
        return None
    control.guard.check=guard
    def advance():
        for _ in range(4): p.stepSimulation(); control.time+=DT; observe()
    control.advance=advance
    def wait(seconds):
        for _ in range(round(seconds/DT)): p.stepSimulation(); control.time+=DT; observe()
    def move(label,pos,yaw=0.):
        nonlocal phase
        phase=label
        snapshots.append({'item':active+1,'phase':label,'placed_items':placed.copy(),'obstacle_count':len(bodies)-1,'poses':[list(p.getBasePositionAndOrientation(o)[0]) for o in bodies],'orientations':[list(p.getBasePositionAndOrientation(o)[1]) for o in bodies]})
        r=move_planned(control,pos,label,planning_log,active+1,yaw); moves.append(r)
        events.append({'phase':phase,'time_s':steps*DT,'position_error_m':r['final_position_error_m']})
        print(active+1,label,'reached',flush=True)
    def release_sample(data):
        release_samples.append({'item':active+1,**data})
    def release_stall(data):
        name=f'release_stall_item{active+1:02}_force{data["force_limit_N"]:g}N'
        p.saveBullet(str(out/(name+'.bullet')))
        (out/(name+'.json')).write_text(json.dumps({'item':active+1,'phase':phase,
            'assisted_constraint_active':constraint is not None,'sample':data,
            'object_origin_m':origin()[0].tolist(),'object_quaternion_xyzw':list(origin()[1]),
            'tcp_world':measured_tcp(robot).tolist(),
            'closest_geometry_within_1mm':[{'link':pt[3],'distance_m':pt[8],
                'normal_on_b_world':list(pt[7])} for pt in p.getClosestPoints(robot.robot,body,.001)]},ensure_ascii=False,indent=2),encoding='utf8')
        events.append({'phase':'release_effort_stage_stalled','item':active+1,
                       'time_s':steps*DT,'force_limit_N':data['force_limit_N'],
                       'opening_m':data['opening_m'],'contacts_present':data['contacts_present']})
        print(active+1,'release stalled at',data['opening_m'],'m with',data['force_limit_N'],'N',flush=True)
    try:
        wait(2.)
        for active,(source,target) in enumerate(zip(sources,targets)):
            body=bodies[active]
            print('ITEM',active+1,flush=True)
            move('approach',[source[0],source[1],.082],source_yaws[active]); move('descend',[source[0],source[1],.014],source_yaws[active])
            phase='close';control.width=.022;robot.command_gripper(.022)
            # Gentle closing for the small 70g scene; require bilateral contact.
            for name,value in [('joint7',.011),('joint8',-.011)]:
                p.setJointMotorControl2(robot.robot,robot.joints[name]['index'],p.POSITION_CONTROL,targetPosition=value,force=CLOSING_FORCE_N,maxVelocity=.02,positionGain=.15,velocityGain=1.)
            wait(1)
            cs=contacts();both=[any(pt[3]==j and core_contact(pt,body) and pt[9]>0 for pt in cs) for j in [8,9]]
            if not all(both): raise RuntimeError(f'Bilateral core contact required: {both}')
            bp,bo=p.getBasePositionAndOrientation(body);ls=p.getLinkState(robot.robot,7)
            relative=p.multiplyTransforms(*p.invertTransform(ls[0],ls[1]),bp,bo)
            constraint=p.createConstraint(robot.robot,7,body,-1,p.JOINT_FIXED,[0,0,0],relative[0],[0,0,0],parentFrameOrientation=relative[1]);p.changeConstraint(constraint,maxForce=30)
            events.append({'phase':'attach','item':active+1,'time_s':steps*DT,'bilateral_contacts':both,'instantaneous_displacement_m':float(np.linalg.norm(np.array(p.getBasePositionAndOrientation(body)[0])-bp))})
            move('lift',[source[0],source[1],.082],source_yaws[active]);move('transfer',[target[0],target[1],.082],yaws[active])
            move('lower',[target[0],target[1],target[2]+(.0145 if active>=8 else .016)],yaws[active])
            phase='release';control.width=.036;robot.command_gripper(.036)
            release=open_before_detach(robot,body,constraint,wait,lambda:steps*DT,release_sample,release_stall)
            events.append({'phase':'opened_before_detach','item':active+1,'time_s':steps*DT,
                'opening_m':release['opening_m'],'contacts_present':release['contacts_present'],
                'linear_speed_m_s':release['linear_speed_m_s'],'force_limit_N':release['force_limit_N'],
                'stable_clear_samples':release['stable_clear_samples'],
                'recovered_after_escalation':release['recovered_after_escalation']})
            p.removeConstraint(constraint);constraint=None;relative=None
            events.append({'phase':'release','item':active+1,'time_s':steps*DT});wait(1)
            move('retreat',[target[0],target[1],.082],yaws[active]);phase='settle';wait(1)
            placed.append(active+1)
            op,oq=origin();item_results.append({'item':active+1,'origin':op.tolist(),'target':target,'position_error_m':float(np.linalg.norm(op-target))})
            if item_results[-1]['position_error_m']>.003:raise RuntimeError(f'Placement {active+1} exceeded 3mm internal position tolerance')
            p.saveBullet(str(out/'checkpoint.bullet'))
            checkpoint={'layout':'preloaded16_tray','sources':sources,'source_yaws':source_yaws,'initial_inventory':initial_inventory,'initial_scene_body_count':initial_scene_body_count,'creation_audit':CREATIONS,'inventory_rows':inventory_rows,'completed_items':placed.copy(),'steps':steps,'control_time':control.time,'width':control.width,'bodies':[{'position':list(p.getBasePositionAndOrientation(o)[0]),'orientation':list(p.getBasePositionAndOrientation(o)[1]),'velocity':list(p.getBaseVelocity(o)[0]),'angular_velocity':list(p.getBaseVelocity(o)[1])} for o in bodies],'joint_states':p.getJointStates(robot.robot,list(range(p.getNumJoints(robot.robot)))),'last_command':[control.trace[-1][f'q{i}_command_rad'] for i in range(1,7)],'rows':rows,'trace':control.trace,'events':events,'moves':moves,'planning_log':planning_log,'snapshots':snapshots,'item_results':item_results}
            (out/'checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False),encoding='utf8')
        phase='final_settle';wait(3)
        final=[]
        for idx,(o,target) in enumerate(zip(bodies,targets)):
            bp,bo=p.getBasePositionAndOrientation(o);op=np.array(bp)-Rotation.from_quat(bo).apply(COM)
            final.append({'item':idx+1,'origin':op.tolist(),'target':target,'position_error_m':float(np.linalg.norm(op-target)),'orientation_error_rad':float((Rotation.from_euler('z',yaws[idx]).inv()*Rotation.from_quat(bo)).magnitude()),'linear_speed_m_s':float(np.linalg.norm(p.getBaseVelocity(o)[0])),'lower_support_contacts':len(p.getContactPoints(o,bodies[idx-8])) if idx>=8 else len(p.getContactPoints(o,floor))})
        success=not violations and len(placed)==count and all(r['position_error_m']<.003 and r['orientation_error_rad']<.05 and r['linear_speed_m_s']<.005 and r['lower_support_contacts']>0 for r in final)
    except Exception as exc:
        error=str(exc); final={}; print(error,flush=True)
        p.saveBullet(str(out/'failure.bullet'))
    finally:
        if telemetry:telemetry.close()
        if writer: writer.close()
        (out/'release_diagnostics.json').write_text(json.dumps(release_samples,ensure_ascii=False,indent=2),encoding='utf8')
        if release_samples:
            scalar=[{k:v for k,v in sample.items() if k not in ['contacts','constraint_wrench']} for sample in release_samples]
            with (out/'release_trace.csv').open('w',newline='',encoding='utf-8-sig') as f:
                w=csv.DictWriter(f,list(scalar[0]));w.writeheader();w.writerows(scalar)
        for name,data in [('trajectory.csv',rows),('b_control_trace.csv',control.trace),('inventory_trace.csv',inventory_rows)]:
            if data:
                with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
                    w=csv.DictWriter(f,list(data[0]));w.writeheader();w.writerows(data)
        report={'contact_breaking_relative_factor':CONTACT_BREAKING_FACTOR,'release_policy':'relative contact cache factor0.00001; open1N then bounded3N retry; detach only after clear stable0.25s','release_force_stages_N':list(RELEASE_FORCES_N),'release_stage_seconds':RELEASE_STAGE_SECONDS,'release_helper_sha256':hashlib.sha256((ROOT/'C_仿真与装配/gripper_release.py').read_bytes()).hexdigest(),'initial_inventory':initial_inventory,'initial_scene_body_count':initial_scene_body_count,'body_count_min':body_count_min,'body_count_max':body_count_max,'creation_audit':CREATIONS,'preloaded_count':len(bodies),'source_yaws':source_yaws,'planning_log':planning_log,'layout_note':'Octagonal segmented enclosure; original rectangular geometry; no side connectors; center (.26,.03), centerline radius .076m' ,'sources':sources,'targets':targets,'placed_items':placed,'item_results':item_results,'scene_snapshots':snapshots,'layout':'octagon_8_per_layer','target_yaws':yaws,'requested_count':count,'feed_mode':'all16 preloaded before step zero on coplanar flat arc tray; no in-run component creation','payload_support_penetration_limit_m':.0002,'planned_payload_distance_limit_m':0.,'dense_edge_resolution_rad':.001,'exact_command_grid_preflight':False,'trajectory_validation':'quintic command-grid preflight; vertical sampled IK plus every-command guard','conservative_aabb_rejection':True,'grip_contact_position_tolerance_m':.001,'all_components_dynamic':True,'support_guard_checks':support_checks,'payload_support_guard_checks':payload_checks,'minimum_payload_support_contact_distance_m':min_support_distance if min_support_distance<1 else None,'success':success,'error':error,'source':'B handoff 2026-10-30','simulated_seconds':steps*DT,'max_bottom_height_m':maxz,'final':final,'events':events,'moves':moves,'collisions':violations,'mass_kg':MASS,'temporary_com_from_bottom_m':COM.tolist(),'temporary_bounding_box_inertia_kg_m2':inertia,'convex_parts':34,'collision_representation':'single rigid base / 34 convex children','base_collision_margin':p.getDynamicsInfo(body,-1)[-1],'gripper_force_limit_N_per_finger':CLOSING_FORCE_N,'physics_substeps':PHYSICS_SUBSTEPS,'physics_dt_s':DT,'internal_physics_dt_s':DT/PHYSICS_SUBSTEPS,'assisted_grasp':True,'self_collision_ignored_pairs':sorted(ignored),'source_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        report.update(payload_config=args.payload_config,com_from_bottom_m=COM.tolist(),inertia_diagonal_about_com_kg_m2=INERTIA.tolist(),wall_seconds=time.time()-started,telemetry_rows=telemetry.count if telemetry else 0,exit_code=0 if success else 1)
        if args.payload_config!='legacy70g':
            del report['temporary_com_from_bottom_m'];del report['temporary_bounding_box_inertia_kg_m2']
        (out/'result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
        control.close();p.disconnect(cid)
    return 0 if success else 1
if __name__=='__main__':raise SystemExit(main())



