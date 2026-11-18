"""Bounded opening effort; retain assisted hold until stable contact clearance."""
import numpy as np
import pybullet as p

RELEASE_FORCES_N=(1.,3.)
RELEASE_STAGE_SECONDS=3.
# Bullet's default relative contact cache factor (0.02) retains obsolete
# normals over distances significant for these 50 mm compound parts.
# This is a relative factor, NOT a penetration allowance in metres.
CONTACT_BREAKING_FACTOR=.00001


def open_before_detach(robot,body,constraint,wait,clock,on_sample,on_stall):
    """No object/joint resets, collision exclusions or constraint deletion here."""
    client=robot.client;stable=0;sample_count=0;last=None
    for stage,force in enumerate(RELEASE_FORCES_N):
        for name,target in [('joint7',.018),('joint8',-.018)]:
            joint=robot.joints[name]
            if force>joint['effort']:raise ValueError('Release effort exceeds URDF limit')
            p.setJointMotorControl2(robot.robot,joint['index'],p.POSITION_CONTROL,
                targetPosition=target,force=force,maxVelocity=.01,
                positionGain=.15,velocityGain=1.,physicsClientId=client)
        for tick in range(round(RELEASE_STAGE_SECONDS/.05)):
            wait(.05);sample_count+=1
            states=[p.getJointState(robot.robot,robot.joints[name]['index'],physicsClientId=client)
                    for name in ['joint7','joint8']]
            opening=states[0][0]-states[1][0]
            contacts=p.getContactPoints(robot.robot,body,physicsClientId=client)
            touch=any(pt[9]>1e-4 for pt in contacts)
            linear,angular=p.getBaseVelocity(body,physicsClientId=client)
            clear=(opening>.0355 and not touch and np.linalg.norm(linear)<.002
                   and np.linalg.norm(angular)<.02)
            stable=stable+1 if clear else 0
            last={'time_s':clock(),'stage':stage+1,'stage_tick':tick+1,
                  'target_opening_m':.036,'opening_m':opening,
                  'left_target_m':.018,'right_target_m':-.018,
                  'left_position_m':states[0][0],'right_position_m':states[1][0],
                  'left_velocity_m_s':states[0][1],'right_velocity_m_s':states[1][1],
                  'left_motor_force_N':states[0][3],'right_motor_force_N':states[1][3],
                  'force_limit_N':force,'contacts_present':touch,
                  'linear_speed_m_s':float(np.linalg.norm(linear)),
                  'angular_speed_rad_s':float(np.linalg.norm(angular)),
                  'stable_clear_samples':stable,
                  'constraint_wrench':list(p.getConstraintState(constraint,physicsClientId=client)),
                  'contacts':[{'body_a':pt[1],'body_b':pt[2],'link_a':pt[3],'link_b':pt[4],
                               'distance_m':pt[8],'normal_force_N':pt[9],
                               'normal_on_b_world':list(pt[7]),
                               'position_on_b_m':list(pt[6])}
                              for pt in p.getContactPoints(robot.robot,physicsClientId=client)
                              if pt[9]>1e-6]}
            on_sample(last)
            if stable>=5:
                return {**last,'sample_count':sample_count,'recovered_after_escalation':stage>0}
        on_stall(last)
    raise RuntimeError('Gripper release did not clear safely after bounded effort stages: '
                       f'opening={last["opening_m"]}, touch={last["contacts_present"]}, '
                       f'force_limit_N={last["force_limit_N"]}')
