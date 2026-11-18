"""Name-based PiPER control and explicit URDF link/TCP coordinate conventions.

All quantities use metres, radians and seconds. This module is a joint-motion
demonstration, not a collision-free planner or a grasp controller.
"""

from pathlib import Path
import math
import time
import xml.etree.ElementTree as ET

import numpy as np
import pybullet as p

PROJECT = Path(__file__).resolve().parents[1]
URDF = PROJECT / "PiPER_Load_URDF/piper_description/piper_description_pybullet.urdf"
ARM_NAMES = tuple(f"joint{i}" for i in range(1, 7))
FINGER_NAMES = ("joint7", "joint8")
# A demonstration pose within the model limits; not a manufacturer home pose.
DEMO_POSE = np.array([0.0, 0.8, -1.2, 0.0, 0.4, 0.0])
# Midpoint of the two finger joint origins, in the gripper_base frame.
# This is a declared nominal tool frame, not a calibrated contact centre.
TCP_OFFSET = np.array([0.0, 0.0, 0.1358])
DT = 1.0 / 240.0


def rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + math.sin(angle) * skew + (1 - math.cos(angle)) * (skew @ skew)


def origin_transform(element):
    transform = np.eye(4)
    if element is None:
        return transform
    xyz = np.fromstring(element.get("xyz", "0 0 0"), sep=" ")
    roll, pitch, yaw = np.fromstring(element.get("rpy", "0 0 0"), sep=" ")
    transform[:3, 3] = xyz
    transform[:3, :3] = (rotation([0, 0, 1], yaw)
                             @ rotation([0, 1, 0], pitch)
                             @ rotation([1, 0, 0], roll))
    return transform


def independent_fk(joint_values, world_from_root=None):
    """URDF forward transforms, independent of Bullet's link-state calculation."""
    root = ET.parse(URDF).getroot()
    transforms = {"dummy_link": np.eye(4) if world_from_root is None else world_from_root.copy()}
    joint_frames = {}
    pending = list(root.findall("joint"))
    while pending:
        progressed = False
        for joint in pending[:]:
            parent = joint.find("parent").get("link")
            if parent not in transforms:
                continue
            child = joint.find("child").get("link")
            name = joint.get("name")
            frame = transforms[parent] @ origin_transform(joint.find("origin"))
            joint_frames[name] = frame
            motion = np.eye(4)
            if joint.get("type") != "fixed":
                axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
                value = joint_values[name]
                if joint.get("type") == "revolute":
                    motion[:3, :3] = rotation(axis, value)
                elif joint.get("type") == "prismatic":
                    motion[:3, 3] = axis * value
                else:
                    raise ValueError(f"Unsupported joint: {name}")
            transforms[child] = frame @ motion
            pending.remove(joint)
            progressed = True
        if not progressed:
            raise ValueError("URDF joint tree has unresolved parents")
    tcp = transforms["gripper_base"].copy()
    tcp[:3, 3] += tcp[:3, :3] @ TCP_OFFSET
    transforms["nominal_tcp"] = tcp
    return transforms, joint_frames


class Piper:
    def __init__(self, client, base_position=(0, 0, 0), base_orientation=(0, 0, 0, 1),
                 self_collision=False):
        self.client = client
        self.robot = p.loadURDF(str(URDF), basePosition=base_position,
                                baseOrientation=base_orientation, useFixedBase=True,
                                flags=p.URDF_USE_SELF_COLLISION if self_collision else 0,
                                physicsClientId=client)
        self.world_from_root = np.eye(4)
        self.world_from_root[:3, :3] = np.asarray(p.getMatrixFromQuaternion(base_orientation)).reshape(3, 3)
        self.world_from_root[:3, 3] = base_position
        self.joints = {}
        self.links = {}
        for index in range(p.getNumJoints(self.robot, physicsClientId=client)):
            info = p.getJointInfo(self.robot, index, physicsClientId=client)
            name = info[1].decode()
            self.joints[name] = {
                "index": index, "type": info[2], "lower": info[8], "upper": info[9],
                "effort": info[10], "velocity": info[11], "link": info[12].decode(),
            }
            self.links[info[12].decode()] = index
        assert all(self.joints[n]["type"] == p.JOINT_REVOLUTE for n in ARM_NAMES)
        assert all(self.joints[n]["type"] == p.JOINT_PRISMATIC for n in FINGER_NAMES)
        p.setTimeStep(DT, physicsClientId=client)
        p.setPhysicsEngineParameter(numSolverIterations=100, physicsClientId=client)

    def reset_demo_pose(self):
        """Initialization only; all subsequent demonstrations use motors."""
        for name, value in zip(ARM_NAMES, DEMO_POSE):
            p.resetJointState(self.robot, self.joints[name]["index"], float(value), physicsClientId=self.client)
        for name in FINGER_NAMES:
            p.resetJointState(self.robot, self.joints[name]["index"], 0.0, physicsClientId=self.client)
        self.command_arm(DEMO_POSE)
        self.command_gripper(0.0)

    def command_arm(self, values):
        values = np.asarray(values, dtype=float)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("Arm target must contain six finite angles in radians")
        # Validate all entries before sending any motor command.
        for name, value in zip(ARM_NAMES, values):
            joint = self.joints[name]
            if not joint["lower"] <= value <= joint["upper"]:
                raise ValueError(f"{name} target outside URDF limits")
        for name, value in zip(ARM_NAMES, values):
            joint = self.joints[name]
            p.setJointMotorControl2(
                self.robot, joint["index"], p.POSITION_CONTROL,
                targetPosition=float(value), force=joint["effort"],
                maxVelocity=min(0.6, joint["velocity"]),
                positionGain=0.15, velocityGain=1.0, physicsClientId=self.client,
            )

    def command_gripper(self, width):
        """Nominal finger-origin separation, 0..0.07 m, not certified clearance."""
        if not math.isfinite(width) or not 0 <= width <= 0.07:
            raise ValueError("Nominal opening must be between 0 and 0.07 metres")
        for name, value in zip(FINGER_NAMES, (width / 2, -width / 2)):
            joint = self.joints[name]
            p.setJointMotorControl2(
                self.robot, joint["index"], p.POSITION_CONTROL,
                targetPosition=value, force=joint["effort"], maxVelocity=0.05,
                positionGain=0.15, velocityGain=1.0, physicsClientId=self.client,
            )

    def values(self):
        return {name: p.getJointState(self.robot, self.joints[name]["index"],
                                      physicsClientId=self.client)[0]
                for name in (*ARM_NAMES, *FINGER_NAMES)}

    def link_frame(self, name):
        state = p.getLinkState(self.robot, self.links[name], computeForwardKinematics=True,
                               physicsClientId=self.client)
        # [4]/[5] are URDF link-frame pose; [0]/[1] are the inertial/COM frame.
        transform = np.eye(4)
        transform[:3, :3] = np.asarray(p.getMatrixFromQuaternion(state[5])).reshape(3, 3)
        transform[:3, 3] = state[4]
        return transform

    def tcp_frame(self):
        transform = self.link_frame("gripper_base")
        transform[:3, 3] += transform[:3, :3] @ TCP_OFFSET
        return transform

    def opening_measurement(self):
        inverse = np.linalg.inv(self.link_frame("gripper_base"))
        first = inverse @ self.link_frame("link7")
        second = inverse @ self.link_frame("link8")
        return {
            "finger7_origin_in_gripper_m": first[:3, 3].tolist(),
            "finger8_origin_in_gripper_m": second[:3, 3].tolist(),
            "measured_separation_m": float(second[1, 3] - first[1, 3]),
            "tcp_midpoint_residual_m": float(np.linalg.norm(
                (first[:3, 3] + second[:3, 3]) / 2 - TCP_OFFSET)),
        }

    def step(self, seconds, realtime=False, on_step=None):
        for i in range(round(seconds / DT)):
            p.stepSimulation(physicsClientId=self.client)
            if on_step is not None:
                on_step(i)
            if realtime:
                time.sleep(DT)


def render_frame(robot, output, closeup=False):
    # Reuse the standard-library PNG writer supplied with step 1.
    import sys
    if str(PROJECT) not in sys.path:
        sys.path.insert(0, str(PROJECT))
    from 验证环境 import save_png

    target = robot.tcp_frame()[:3, 3].tolist() if closeup else [0.04, 0, 0.30]
    distance = 0.29 if closeup else 1.05
    view = p.computeViewMatrixFromYawPitchRoll(target, distance, 100 if closeup else 45, -22, 0, 2)
    projection = p.computeProjectionMatrixFOV(45, 960 / 720, 0.01, 5)
    frame = p.getCameraImage(960, 720, view, projection,
                             renderer=p.ER_TINY_RENDERER, physicsClientId=robot.client)
    rgb = np.asarray(frame[2], dtype=np.uint8).reshape(720, 960, 4)[:, :, :3]
    save_png(Path(output), rgb)
