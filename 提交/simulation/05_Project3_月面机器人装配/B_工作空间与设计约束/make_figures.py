"""Draw workspace/layout artifacts from the recorded numeric results."""
from pathlib import Path
import sys
import csv
import json

import numpy as np
import pybullet as p

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_workspace import Analysis, OUT, PROJECT, BLOCK
from component_model import load_component
sys.path.insert(0, str(PROJECT))
from 验证环境 import save_png


def main():
    d = json.loads((OUT / "工作空间验证结果.json").read_text())
    grid = list(csv.DictReader((OUT / "俯抓工作空间采样.csv").open(encoding="utf-8-sig")))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="940" viewBox="0 0 1100 940">',
             '<rect width="1100" height="940" fill="#f6f8fb"/>',
             '<g font-family="Arial,PingFang SC,sans-serif" fill="#17283b">',
             '<text x="40" y="38" font-size="24" font-weight="bold">PiPER 俯抓工作空间：可达点随高度变化</text>',
             '<text x="40" y="66" font-size="16">基座原点固定；工具朝下 Ry(180°)；单位毫米；仅表示有限采样结果</text>']
    colors = {"pass": "#138b79", "joint_limit_or_margin": "#dc8738", "ik_not_converged": "#abb4c0", "clearance_rejected": "#c84557"}
    for i, z in enumerate((.014, .036, .082, .122)):
        left, top = 60 + (i % 2) * 535, 112 + (i // 2) * 360
        parts += [f'<rect x="{left-22}" y="{top-25}" width="495" height="334" rx="12" fill="white"/>',
                  f'<text x="{left}" y="{top}" font-size="19" font-weight="bold">名义 TCP 高度 {z*1000:.0f} mm</text>']
        for x in range(200, 451, 50):
            sx = left + 25 + (x - 200) * 1.45
            parts.append(f'<text x="{sx-12}" y="{top+291}" font-size="12">{x}</text>')
        for y in (-175, -100, 0, 100, 175):
            sy = top + 142 - y * .65
            parts.append(f'<text x="{left-17}" y="{sy+4}" font-size="12">{y}</text>')
        for row in grid:
            if float(row["z_m"]) != z:
                continue
            x = left + 25 + (float(row["x_m"]) * 1000 - 200) * 1.45
            y = top + 142 - float(row["y_m"]) * 1000 * .65
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.3" fill="{colors[row["status"]]}"/>')
        count = sum(r["status"] == "pass" and float(r["z_m"]) == z for r in grid)
        parts.append(f'<text x="{left+278}" y="{top}" font-size="14">通过 {count}/165 点</text>')
        parts.append(f'<text x="{left+425}" y="{top+291}" font-size="14">X</text>')
    parts += ['<text x="50" y="850" font-size="16" fill="#138b79">● 满足本次限位／姿态／碰撞筛查</text>',
              '<text x="520" y="850" font-size="16" fill="#dc8738">● 超出关节限位或2°余量</text>',
              '<text x="50" y="881" font-size="16" fill="#778595">● 求解未收敛（不能据此断言不可达）</text>',
              '<text x="50" y="914" font-size="15">25 mm 网格；非连续工作区边界。122 mm 高度未找到合格解仅适用于本图朝向及扫描区域。</text>', '</g></svg>']
    (OUT / "俯抓工作空间图.svg").write_text("\n".join(parts))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="850" viewBox="0 0 1000 850">',
             '<rect width="1000" height="850" fill="#f6f8fb"/><g font-family="Arial,PingFang SC,sans-serif" fill="#17283b">',
             '<text x="40" y="44" font-size="26" font-weight="bold">给 A 的布局基线：六块、两层</text>',
             '<text x="40" y="78" font-size="17">俯视图 · 坐标单位 mm · 长边沿 X，夹持宽度沿 Y · 原点为机器人基座</text>']
    def xy(x, y):
        return 140 + x * 1600, 360 - y * 1600
    for x in range(0, 401, 50):
        xx, _ = xy(x / 1000, 0)
        parts.append(f'<path d="M{xx} 140V650" stroke="#dce3eb"/><text x="{xx-12}" y="678" font-size="14">{x}</text>')
    for y in range(-150, 101, 50):
        _, yy = xy(0, y / 1000)
        parts.append(f'<path d="M140 {yy}H800" stroke="#dce3eb"/><text x="87" y="{yy+5}" font-size="14">{y}</text>')
    bx, by = xy(0, 0)
    parts += [f'<circle cx="{bx}" cy="{by}" r="40" fill="#566478"/>',
              f'<text x="{bx-45}" y="{by-54}" font-size="16">PiPER 基座</text>',
              '<text x="818" y="678" font-size="18">X →</text><text x="65" y="130" font-size="18">Y ↑</text>']
    for source in d["sources"]:
        x, y = xy(*source["origin_m"][:2])
        parts.append(f'<rect x="{x-40}" y="{y-24}" width="80" height="48" rx="3" fill="#327fc2"/>')
        parts.append(f'<text x="{x-11}" y="{y+6}" font-size="16" fill="white">{source["id"]}</text>')
    for goal in d["goals"][:3]:
        x, y = xy(*goal["origin_m"][:2])
        column = goal["id"][-1]
        parts.append(f'<rect x="{x-40}" y="{y-24}" width="80" height="48" fill="#d99532" stroke="#724700"/>')
        parts.append(f'<text x="{x-25}" y="{y+5}" font-size="15">第{column}列</text>')
    parts += ['<text x="40" y="726" font-size="18">蓝色：六个取料位；橙色：装配区，两层底面原点高度 0 / 22</text>',
              '<text x="40" y="758" font-size="18">槽榫构件总包络 50×30×25；两层结构 150×30×47；搬运 TCP 高度 82</text>',
              '<text x="40" y="790" font-size="16">顺序 S1→L1_1、S2→L1_2、S3→L1_3、S4→L2_1、S5→L2_2、S6→L2_3</text>',
              '<text x="40" y="822" font-size="15">本图为设计约束基线；连接接口、承载、真实夹取和连续避碰仍须后续验证。</text>', '</g></svg>']
    (OUT / "给A的推荐布局.svg").write_text("\n".join(parts))
    a = Analysis()
    for s in d["sources"]:
        load_component(s["origin_m"], color=(.18, .48, .78, 1))
    for g in d["goals"]:
        load_component(g["origin_m"], color=(.84, .57, .19, 1))
    a.reset(d["goals"][-1]["approach_pose"]["q_rad"])
    view = p.computeViewMatrix([.8, -.8, .65], [.20, 0, .10], [0, 0, 1])
    projection = p.computeProjectionMatrixFOV(42, 1200 / 800, .01, 5)
    frame = p.getCameraImage(1200, 800, view, projection, renderer=p.ER_TINY_RENDERER)
    save_png(OUT / "推荐布局_三维预览.png", np.asarray(frame[2], dtype=np.uint8).reshape(800, 1200, 4)[:, :, :3])
    p.disconnect(a.client)
    # Show the actual surface mesh at useful angles, without the robot hiding it.
    p.connect(p.DIRECT)
    part=load_component([0,0,0])
    projection=p.computeProjectionMatrixFOV(32,1.5,.001,1)
    for name,eye,target in (("新构件_顶部与夹持槽.png",[.065,-.090,.065],[0,0,.013]),
                            ("新构件_底部定位凹口.png",[.06,-.085,-.065],[0,0,.008])):
        view=p.computeViewMatrix(eye,target,[0,0,1])
        frame=p.getCameraImage(1200,800,view,projection,renderer=p.ER_TINY_RENDERER)
        save_png(OUT/name,np.asarray(frame[2],dtype=np.uint8).reshape(800,1200,4)[:,:,:3])
    load_component([0,0,.022],color=(.24,.54,.75,1))
    view=p.computeViewMatrix([.08,-.12,.07],[0,0,.023],[0,0,1])
    frame=p.getCameraImage(1200,800,view,projection,renderer=p.ER_TINY_RENDERER)
    save_png(OUT/'新构件_两层插合预览.png',np.asarray(frame[2],dtype=np.uint8).reshape(800,1200,4)[:,:,:3])
    p.disconnect()


if __name__ == "__main__":
    main()
