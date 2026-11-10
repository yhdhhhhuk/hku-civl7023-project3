"""Keyboard controls, or an automatic joint-and-gripper demonstration."""

import argparse
import json
import math
import time

import numpy as np
import pybullet as p

from piper_robot import ARM_NAMES, DEMO_POSE, DT, PROJECT, Piper, render_frame


def draw_frames(robot):
    for name, transform, length in [
        ("Base", robot.link_frame("base_link"), 0.10),
        ("Nominal TCP", robot.tcp_frame(), 0.06),
    ]:
        start = transform[:3, 3]
        for i, color in enumerate([(1, 0, 0), (0, 0.7, 0), (0, 0.2, 1)]):
            end = start + length * transform[:3, i]
            p.addUserDebugLine(start, end, color, 3, lifeTime=0.12, physicsClientId=robot.client)
        p.addUserDebugText(name, start + [0, 0, 0.03], [0.1, 0.1, 0.1],
                           0.9, lifeTime=0.12, physicsClientId=robot.client)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Motor-driven automatic sequence")
    parser.add_argument("--seconds", type=float, default=0, help="0 means keep the window open")
    parser.add_argument("--no-axes", action="store_true", help="Hide debug coordinate overlays")
    args = parser.parse_args()
    client = p.connect(p.GUI)
    if client < 0:
        raise RuntimeError("Cannot open PyBullet GUI")
    robot = Piper(client)
    p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1, physicsClientId=client)
    p.resetDebugVisualizerCamera(0.95, 45, -24, [0.06, 0, 0.32], physicsClientId=client)
    p.setGravity(0, 0, -1.62, physicsClientId=client)
    robot.reset_demo_pose()
    # GUI command/render latency must not slow the physical clock to one
    # simulation step per screen refresh. Headless tests keep fixed stepping.
    p.setRealTimeSimulation(1, physicsClientId=client)
    labels = ["Base", "Shoulder", "Elbow", "Forearm roll", "Wrist pitch", "Tool roll"]
    selected = 0
    manual_target = DEMO_POSE.copy()
    manual_width = 0.0
    if not args.auto:
        p.addUserDebugText("1-6: select joint | [ ]: -/+5 deg | O: open | C: close | 0: home",
                           [-0.30, 0, 0.80], [0.1, 0.1, 0.1], 0.9, physicsClientId=client)
    sequence = [(DEMO_POSE.copy(), 0.0, "Initial")]
    for i in range(6):
        target = DEMO_POSE.copy()
        target[i] += 0.18
        sequence.extend([(target, 0.0, f"joint{i+1} positive"),
                         (DEMO_POSE.copy(), 0.0, "Return")])
    sequence.extend([(DEMO_POSE.copy(), 0.07, "Gripper OPEN 70 mm"),
                     (DEMO_POSE.copy(), 0.0, "Gripper CLOSE 0 mm"),
                     (DEMO_POSE.copy(), 0.04, "Gripper OPEN 40 mm")])
    last_phase = -1
    phase = 0
    phase_started = time.monotonic()
    start = time.monotonic()
    tick = 0
    print("PiPER joint controls ready: six arm joints + two coordinated fingers.", flush=True)
    print("Axes: X red, Y green, Z blue. TCP is declared, not factory-calibrated.", flush=True)
    if not args.auto:
        print("Keyboard ready: 1-6 select; [ ] change angle; O open; C close; 0 demo pose.", flush=True)
    try:
        while p.isConnected(client):
            elapsed = time.monotonic() - start
            if args.seconds > 0 and elapsed >= args.seconds:
                break
            if args.auto:
                if last_phase >= 0 and phase < len(sequence) - 1:
                    current = robot.values()
                    last_target, last_width, _ = sequence[phase]
                    arm_error = max(abs(current[n] - v) for n, v in zip(ARM_NAMES, last_target))
                    opening_error = abs(current["joint7"] - current["joint8"] - last_width)
                    phase_elapsed = time.monotonic() - phase_started
                    if phase_elapsed >= 1.6 and arm_error < 0.01 and opening_error < 0.0005:
                        phase += 1
                    elif phase_elapsed > 15:
                        raise RuntimeError(f"GUI motion did not reach target: arm={arm_error}, opening={opening_error}")
                target, width, label = sequence[phase]
                if phase != last_phase:
                    if last_phase >= 0 and sequence[last_phase][2].startswith("Gripper"):
                        previous = sequence[last_phase][2]
                        print(json.dumps({"finished_phase": previous,
                                          **robot.opening_measurement()}, ensure_ascii=False), flush=True)
                    print(label, flush=True)
                    robot.command_arm(target)
                    robot.command_gripper(width)
                    last_phase = phase
                    phase_started = time.monotonic()
            else:
                events = p.getKeyboardEvents(physicsClientId=client)
                triggered = {key for key, flags in events.items() if flags & p.KEY_WAS_TRIGGERED}
                changed = False
                for i in range(6):
                    if ord(str(i + 1)) in triggered:
                        selected = i
                        print(f"Selected joint{i+1}: {labels[i]}", flush=True)
                if ord("[") in triggered or ord("]") in triggered:
                    delta = math.radians(5) * (1 if ord("]") in triggered else -1)
                    joint = robot.joints[ARM_NAMES[selected]]
                    manual_target[selected] = np.clip(manual_target[selected] + delta,
                                                       joint["lower"], joint["upper"])
                    changed = True
                if ord("o") in triggered or ord("O") in triggered:
                    manual_width = 0.07
                    changed = True
                if ord("c") in triggered or ord("C") in triggered:
                    manual_width = 0.0
                    changed = True
                if ord("0") in triggered:
                    manual_target = DEMO_POSE.copy()
                    manual_width = 0.0
                    changed = True
                if changed:
                    robot.command_arm(manual_target)
                    robot.command_gripper(manual_width)
                    print(json.dumps({"target_angles_deg": np.degrees(manual_target).tolist(),
                                      "target_nominal_opening_mm": manual_width * 1000}), flush=True)
                if tick == 15:
                    print("Keyboard event polling and coordinate overlay running.", flush=True)
            if not args.no_axes and tick % 2 == 0:
                draw_frames(robot)
            tick += 1
            time.sleep(1 / 60)
        print("Demonstration closed.", flush=True)
    except KeyboardInterrupt:
        pass
    except p.error:
        # A window can close between isConnected() and the next GUI command.
        if p.isConnected(client):
            raise
        print("GUI window closed by user.", flush=True)
    finally:
        if p.isConnected(client):
            p.disconnect(client)


if __name__ == "__main__":
    main()
