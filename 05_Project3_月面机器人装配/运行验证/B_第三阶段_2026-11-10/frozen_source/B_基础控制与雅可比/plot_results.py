"""Standalone experiment figures from saved motor-driven traces."""
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'7023_matplotlib'))
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from kinematics import Kinematics, PROJECT

OUT=PROJECT/'运行验证/基础控制与雅可比'


def main():
    candidates=[Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
                Path('C:/Windows/Fonts/msyh.ttc'),
                Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
    for font in candidates:
        if font.exists():
            font_manager.fontManager.addfont(str(font))
            plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
            break
    plt.rcParams.update({'axes.unicode_minus':False,'svg.fonttype':'none','font.size':10})
    result=json.loads((OUT/'位姿控制验证结果.json').read_text())
    rows=list(csv.DictReader((OUT/'位姿误差轨迹.csv').open(encoding='utf-8-sig')))
    targets=result['targets'];y=np.arange(len(targets))
    fig,axes=plt.subplots(1,2,figsize=(12,10),sharey=True,layout='constrained')
    for ax,key,mult,label in [(axes[0],'final_position_error_m',1000,'最终位置误差 / mm'),
                              (axes[1],'final_orientation_error_deg',1,'最终姿态误差 / °')]:
        values=[t[key]*mult for t in targets]
        colors=['#dc863d' if t['strategy']=='cartesian_dls' else '#277cb5' for t in targets]
        ax.barh(y,values,color=colors)
        ax.axvline(.1,color='#b84a4a',linestyle='--',label='内部门槛 0.1')
        ax.set_xlim(0,.112);ax.set_xlabel(label);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
        for yy,value in zip(y,values):ax.text(value+.001,yy,f'{value:.4f}',va='center',fontsize=8)
        ax.legend(loc='lower right')
    axes[0].set_yticks(y,[t['target_id'] for t in targets]);axes[0].invert_yaxis()
    fig.suptitle('29次空载目标定位：最终误差\n蓝色：自动两阶段；橙色：直接雅可比闭环；非实物精度')
    fig.savefig(OUT/'目标定位误差.png',dpi=160);fig.savefig(OUT/'目标定位误差.svg');plt.close(fig)
    t=np.array([float(r['time_s']) for r in rows])
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True,layout='constrained')
    for ax,key,mult,label in [(axes[0],'position_error_m',1000,'到最终目标的位置误差 / mm'),
                              (axes[1],'orientation_error_deg',1,'到最终目标的姿态误差 / °')]:
        values=np.maximum([float(r[key])*mult for r in rows],1e-7)
        ax.semilogy(t,values,color='#277cb5',linewidth=1)
        ax.axhline(.1,color='#b84a4a',linestyle='--',label='内部门槛 0.1')
        ax.grid(alpha=.2);ax.set_ylabel(label);ax.legend(loc='upper right')
    axes[-1].set_xlabel('仿真时间 / s')
    fig.suptitle('电机驱动误差记录：目标切换时误差会跳变\n此图不是沿规划轨迹的参考跟踪误差')
    fig.savefig(OUT/'误差随时间.png',dpi=160);fig.savefig(OUT/'误差随时间.svg');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    for ax,name in zip(axes.flat,['position_nudge','orientation_tilt','orientation_roll','orientation_combined']):
        part=[r for r in rows if r['target_id']==name]
        tt=np.array([float(r['time_s']) for r in part]);tt-=tt[0]
        ax.semilogy(tt,[float(r['position_error_m'])*1000 for r in part],label='位置误差 / mm')
        ax.semilogy(tt,[max(1e-7,float(r['orientation_error_deg'])) for r in part],label='姿态误差 / °')
        ax.axhline(.1,color='#b84a4a',linestyle='--',label='各自内部门槛 0.1')
        ax.set_title(name);ax.set_xlabel('本次运动时间 / s');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('直接雅可比闭环：位置扰动及三种姿态变化\n两条曲线单位不同；共用对数刻度只用于观察收敛')
    fig.savefig(OUT/'雅可比闭环收敛.png',dpi=160);fig.savefig(OUT/'雅可比闭环收敛.svg');plt.close(fig)
    sample=next(r for r in reversed(rows) if r['target_id']=='S2_above')
    q=[float(sample[f'q{i}_rad']) for i in range(1,7)]
    k=Kinematics();T,J=k.evaluate(q)
    example={'target_id':'S2_above','q_rad':q,'actual_TCP_matrix':T.tolist(),
             'jacobian_world_linear_first':J.tolist(),'linear_row_units':'m/rad',
             'angular_rows':'world angular velocity, rad/s per rad/s; not Euler-angle derivatives',
             'weight_matrix':k.W.tolist(),**k.diagnostics(J)}
    (OUT/'雅可比数值示例.json').write_text(json.dumps(example,ensure_ascii=False,indent=2)+'\n')
    print('Saved 3 PNG/SVG figure pairs and a measured-state Jacobian example.')


if __name__=='__main__':main()
