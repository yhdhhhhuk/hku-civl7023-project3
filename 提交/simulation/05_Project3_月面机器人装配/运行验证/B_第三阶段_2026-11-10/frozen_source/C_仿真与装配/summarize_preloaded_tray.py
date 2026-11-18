"""Build stage-two review tables/plots from actual logs, without rerunning physics."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.cache/C_仿真与装配/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output
    r=json.loads((out/'result.json').read_text(encoding='utf8'))
    with (out/'b_control_trace.csv').open(encoding='utf-8-sig') as f:trace=list(csv.DictReader(f))
    with (out/'trajectory.csv').open(encoding='utf-8-sig') as f:objects=list(csv.DictReader(f))
    final=r['final'] if isinstance(r['final'],list) else []
    metrics={'success':r['success'],'completed_count':len(r['placed_items']),'simulated_seconds':r['simulated_seconds'],'max_position_error_mm':max((x['position_error_m']*1000 for x in final),default=None),'max_orientation_error_deg':max((np.degrees(x['orientation_error_rad']) for x in final),default=None),'max_linear_speed_m_s':max((x['linear_speed_m_s'] for x in final),default=None),'joint_speed_peak_rad_s':max(float(x['max_joint_velocity_rad_s']) for x in trace),'minimum_joint_margin_deg':min(float(x['joint_margin_deg']) for x in trace),'execution_collision_events':len(r['collisions']),'planned_segments':len(r.get('planning_log',[])),'rrt_segments':sum(x.get('method')=='RRT_Connect' and x.get('status')=='executed' for x in r.get('planning_log',[])),'planned_rrt_segments':sum(x.get('method')=='RRT_Connect' for x in r.get('planning_log',[])),'planning_checks':sum(x.get('checks',0) for x in r.get('planning_log',[])),'scene_updates':len(r['scene_snapshots']),'assist_attach_count':sum(x['phase']=='attach' for x in r['events']),'maximum_attach_displacement_m':max((x.get('instantaneous_displacement_m',0) for x in r['events']),default=0),'temporary_dynamics':True,'assisted_grasp':True}
    if final:
        with (out/'final_errors.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,list(final[0]));w.writeheader();w.writerows(final)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
    fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    t=[float(x['time_s']) for x in trace]
    for j in range(1,7):axs[0,0].plot(t,[float(x[f'q{j}_rad']) for x in trace],label=f'q{j}')
    axs[0,0].set(xlabel='Simulation time (s)',ylabel='Joint angle (rad)');axs[0,0].legend(ncol=3)
    for j in range(1,7):axs[0,1].plot(t,[float(x[f'q{j}_velocity_rad_s']) for x in trace],label=f'q{j}')
    axs[0,1].set(xlabel='Simulation time (s)',ylabel='Joint speed (rad/s)')
    for item in range(1,r.get('requested_count',16)+1):
        rows=[x for x in objects if int(x['item'])==item]
        axs[1,0].plot([float(x['object_x'])*1000 for x in rows],[float(x['object_y'])*1000 for x in rows],label=str(item),linestyle='-' if item<=8 else '--',color=plt.get_cmap('tab10')((item-1)%8))
    axs[1,0].set(xlabel='Object X (mm)',ylabel='Object Y (mm)');axs[1,0].legend(title='Item (upper layer dashed)',ncol=8,fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.22))
    if final:axs[1,1].bar([x['item'] for x in final],[x['position_error_m']*1000 for x in final])
    axs[1,1].set(xlabel='Item',ylabel='Final position error (mm)')
    for ax in axs.flat:ax.grid(alpha=.25)
    fig.suptitle('Preloaded 16-part tray | octagonal assembly | temporary dynamics, assisted grasp')
    fig.savefig(out/'assembly_metrics.png',dpi=160);plt.close(fig)
    print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
