"""C原RRT-Connect算法；检查由当前槽榫模型GuardWorld提供。"""
import math
import numpy as np

def plan_path(start,goal,world,lower,upper,seed=7023,max_iterations=1800):
    start=np.asarray(start); goal=np.asarray(goal)
    begin=world.checks
    if not world.free(start): raise RuntimeError(f'Planning start in collision: {world.last_reason}')
    if not world.free(goal): raise RuntimeError(f'Planning goal in collision: {world.last_reason}')
    if world.edge(start,goal):
        return [start,goal],{'method':'direct_checked','iterations':0,'checks':world.checks-begin,'direct_blocked':False}
    rng=np.random.default_rng(seed)
    trees=[([start],[-1]),([goal],[-1])]
    def extend(tree,target):
        nodes,parents=tree
        nearest=int(np.argmin([np.linalg.norm(n-target) for n in nodes]))
        delta=target-nodes[nearest]; length=np.linalg.norm(delta)
        candidate=target if length<=.18 else nodes[nearest]+delta*.18/length
        if not world.edge(nodes[nearest],candidate): return None,False
        nodes.append(candidate.copy()); parents.append(nearest)
        return len(nodes)-1,length<=.18
    def ancestry(tree,index):
        result=[]
        while index!=-1:
            result.append(tree[0][index]); index=tree[1][index]
        return result[::-1]
    for iteration in range(max_iterations):
        a=iteration%2; b=1-a
        sample=trees[b][0][0] if rng.random()<.15 else rng.uniform(lower,upper)
        ia,_=extend(trees[a],sample)
        if ia is None: continue
        while True:
            ib,reached=extend(trees[b],trees[a][0][ia])
            if ib is None: break
            if reached:
                left=ancestry(trees[a],ia); right=ancestry(trees[b],ib)
                path=left+right[-2::-1] if a==0 else right+left[-2::-1]
                for _ in range(60):
                    if len(path)<=2: break
                    i,j=sorted(rng.choice(len(path),2,replace=False))
                    if j>i+1 and world.edge(path[i],path[j]): path=path[:i+1]+path[j:]
                assert all(world.edge(x,y) for x,y in zip(path,path[1:]))
                return path,{'method':'RRT_Connect','iterations':iteration+1,'checks':world.checks-begin,'direct_blocked':True,'vertices':len(path),'edge_resolution_rad':.02}
    raise RuntimeError(f'RRT exhausted {max_iterations} iterations / {world.checks-begin} checks')
