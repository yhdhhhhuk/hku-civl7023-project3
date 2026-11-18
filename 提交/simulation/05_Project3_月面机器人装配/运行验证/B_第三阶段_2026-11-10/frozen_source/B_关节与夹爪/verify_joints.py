"""Check independent frames, individual motor motion and symmetric gripper cycles."""

import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pybullet as p

from piper_robot import (ARM_NAMES, DEMO_POSE, DT, FINGER_NAMES, PROJECT, TCP_OFFSET,
                         URDF, Piper, independent_fk, render_frame)

OUTPUT = PROJECT / "运行验证/关节与夹爪"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    client = p.connect(p.DIRECT)
    try:
        base_position = [0.1, -0.2, 0.05]
        base_orientation = p.getQuaternionFromEuler([0.1, -0.2, 0.3])
        robot = Piper(client, base_position, base_orientation)
        rng = np.random.default_rng(7023)
        worst_position = 0.0
        worst_rotation = 0.0
        # A non-identity base also detects accidental world/base-frame mixing.
        for _ in range(25):
            for name in (*ARM_NAMES, *FINGER_NAMES):
                joint = robot.joints[name]
                value = rng.uniform(joint["lower"], joint["upper"])
                p.resetJointState(robot.robot, joint["index"], value, physicsClientId=client)
            expected, _ = independent_fk(robot.values(), robot.world_from_root)
            for name in robot.links:
                actual = robot.link_frame(name)
                worst_position = max(worst_position, float(np.linalg.norm(actual[:3, 3] - expected[name][:3, 3])))
                worst_rotation = max(worst_rotation, float(np.linalg.norm(actual[:3, :3] - expected[name][:3, :3])))
            tcp = robot.tcp_frame()
            worst_position = max(worst_position, float(np.linalg.norm(tcp[:3, 3] - expected["nominal_tcp"][:3, 3])))
        assert worst_position < 2e-6, worst_position
        assert worst_rotation < 2e-6, worst_rotation
        p.removeBody(robot.robot, physicsClientId=client)

        robot = Piper(client)
        robot.reset_demo_pose()
        p.setGravity(0, 0, -1.62, physicsClientId=client)
        robot.step(1.5)
        motion = []
        for index, name in enumerate(ARM_NAMES):
            for delta in [0.15, -0.15]:
                target = DEMO_POSE.copy()
                target[index] += delta
                before = robot.values()[name]
                robot.command_arm(target)
                robot.step(1.5)
                after = robot.values()[name]
                error = abs(after - target[index])
                assert (after - before) * delta > 0
                assert error < 0.002, (name, delta, error)
                motion.append({"joint": name, "target_rad": float(target[index]),
                               "actual_rad": after, "direction": "positive" if delta > 0 else "negative",
                               "error_rad": error})
                robot.command_arm(DEMO_POSE)
                robot.step(1.0)

        trace = []
        cycles = []
        for repetition in range(2):
            for width in [0.0, 0.02, 0.07, 0.0]:
                robot.command_gripper(width)

                def capture(_):
                    q = robot.values()
                    trace.append({"time_s": len(trace) * DT, "target_width_m": width,
                                  "q7_m": q["joint7"], "q8_m": q["joint8"]})

                robot.step(1.6, on_step=capture)
                q = robot.values()
                measured = robot.opening_measurement()
                error = abs(measured["measured_separation_m"] - width)
                symmetry = abs(q["joint7"] + q["joint8"])
                assert error < 5e-5, (width, error)
                assert symmetry < 5e-5, symmetry
                assert measured["tcp_midpoint_residual_m"] < 5e-5
                cycles.append({"cycle": repetition + 1, "target_nominal_width_m": width,
                               "q7_m": q["joint7"], "q8_m": q["joint8"],
                               "opening_error_m": error, "symmetry_error_m": symmetry, **measured})
                if repetition == 0 and width in (0, 0.07):
                    label = "张开70mm" if width else "闭合0mm"
                    render_frame(robot, OUTPUT / f"夹爪_{label}.png", closeup=True)

        # Range checks must reject bad commands before they reach the motors.
        rejected = 0
        for bad in [-0.01, 0.071, float("nan")]:
            try:
                robot.command_gripper(bad)
            except ValueError:
                rejected += 1
        for bad in [[0] * 5, [float("nan")] * 6, [100] * 6]:
            try:
                robot.command_arm(bad)
            except ValueError:
                rejected += 1
        assert rejected == 6

        robot.command_gripper(0.04)
        robot.step(1.6)
        render_frame(robot, OUTPUT / "PiPER_演示姿态.png")
        frames = {name: robot.link_frame(name).tolist()
                  for name in ["base_link", "link6", "gripper_base", "link7", "link8"]}
        frames["nominal_tcp"] = robot.tcp_frame().tolist()
        _, zero_joint_frames = independent_fk({name: 0.0 for name in (*ARM_NAMES, *FINGER_NAMES)})
        descriptions = []
        for joint in ET.parse(URDF).getroot().findall("joint"):
            name = joint.get("name")
            entry = {"name": name, "type": joint.get("type"),
                     "parent": joint.find("parent").get("link"),
                     "child": joint.find("child").get("link"), **robot.joints[name]}
            if joint.find("axis") is not None:
                axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
                entry["urdf_joint_local_axis"] = axis.tolist()
                entry["axis_in_base_at_all_zero"] = (zero_joint_frames[name][:3, :3] @ axis).tolist()
            descriptions.append(entry)
        result = {
            "status": "PASS", "checked_at_hkt": datetime.now().astimezone().isoformat(),
            "model": str(URDF.relative_to(PROJECT)), "model_sha256": hashlib.sha256(URDF.read_bytes()).hexdigest(),
            "test_conditions": {"gravity_m_s2": [0, 0, -1.62], "time_step_s": DT,
                                "base_fixed": True, "payload": "none", "self_collision_enabled": False,
                                "force_limits_source": "URDF effort fields; not validated hardware ratings"},
            "joints": descriptions,
            "coordinate_check": {"random_configurations": 25,
                                 "base_pose_non_identity": True,
                                 "max_position_difference_m": worst_position,
                                 "max_rotation_matrix_frobenius_difference": worst_rotation},
            "motor_motion_checks": motion, "gripper_cycles": cycles,
            "invalid_commands_rejected": rejected,
            "nominal_tcp": {"parent_frame": "gripper_base", "translation_m": TCP_OFFSET.tolist(),
                            "orientation_relative_to_parent": "identity",
                            "meaning": "midpoint of finger joint origins, not calibrated contact centre"},
            "example_frames_world": frames,
            "example_actual_joint_values": robot.values(),
            "scope": "Frame conventions, six individual joint motors and unloaded gripper open/close. No IK, grasp, collision-free planning or torque validation.",
        }
        (OUTPUT / "关节与夹爪验证结果.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        with (OUTPUT / "夹爪开闭轨迹.csv").open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(trace[0]))
            writer.writeheader()
            writer.writerows(trace)
        print(json.dumps({"status": "PASS", "motor_direction_checks": len(motion),
                          "gripper_stops_checked": len(cycles),
                          "max_arm_error_rad": max(x["error_rad"] for x in motion),
                          "max_gripper_opening_error_m": max(x["opening_error_m"] for x in cycles),
                          "coordinate_check": result["coordinate_check"], "output": str(OUTPUT)},
                         ensure_ascii=False, indent=2))
    finally:
        p.disconnect(client)


if __name__ == "__main__":
    main()
