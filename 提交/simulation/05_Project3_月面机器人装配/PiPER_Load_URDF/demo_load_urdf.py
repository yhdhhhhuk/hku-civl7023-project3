#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
只加载并显示 PiPER URDF。
其它功能全部删除。
"""

import time
from pathlib import Path

import pybullet as p


# 当前 Python 文件所在目录
ROOT = Path(__file__).resolve().parent

# PiPER URDF 路径
URDF_PATH = ROOT / "piper_description" / "piper_description_pybullet.urdf"


def main():
    # 连接 PyBullet GUI
    physics_client = p.connect(p.GUI)
    if physics_client < 0:
        raise RuntimeError("Cannot connect to PyBullet GUI")

    # 检查 URDF 是否存在
    if not URDF_PATH.exists():
        raise FileNotFoundError(f"URDF not found: {URDF_PATH}")

    # 加载 PiPER URDF
    robot_id = p.loadURDF(
        str(URDF_PATH),
        basePosition=[0.0, 0.0, 0.0],
        baseOrientation=[0.0, 0.0, 0.0, 1.0],
        useFixedBase=True,
    )

    print("PiPER URDF loaded successfully.")
    print(f"robot_id = {robot_id}")
    print(f"URDF = {URDF_PATH}")

    # 设置初始观察视角
    p.resetDebugVisualizerCamera(
        cameraDistance=0.78,
        cameraYaw=42.0,
        cameraPitch=-30.0,
        cameraTargetPosition=[0.25, 0.02, 0.10],
    )

    # 保持窗口打开
    try:
        while p.isConnected():
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        if p.isConnected():
            p.disconnect()


if __name__ == "__main__":
    main()