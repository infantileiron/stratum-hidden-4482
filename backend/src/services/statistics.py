import math
from src.services.forward_backward import forward_backward
from src.services.viterbi import viterbi
from src.services.constraints import constraint_conflicts,raise_if_conflict
def analyze(snapshot,checksum):
 rows=snapshot['rows'];model=snapshot['model'];c=model['config'];states=c['states'];values=[r['value'] for r in rows]
 constraints=snapshot.get('depth_constraints',[]);pi=c['initial'];A=c['transition'];means=[s['mean'] for s in states];variances=[s['variance'] for s in states]
 diag=constraint_conflicts(pi,A,rows,states,constraints) if constraints else None
 raise_if_conflict(diag)
 masks=[[True]*len(states) for _ in rows]
 if diag is not None:masks=diag['mask_allowed']
 fb=forward_backward(values,pi,A,means,variances,masks if constraints else None);vi=viterbi(values,pi,A,means,variances,masks if constraints else None);out=[]
 constraint_by_index={item['depth_index']:item for item in (diag['constraints'] if diag else [])}
 for i,row in enumerate(rows):
  posterior=fb['posterior'][i];point=fb['point_map'][i];path=vi['path'][i];rule=constraint_by_index.get(i)
  out.append({**row,'posterior':posterior,'point_state_index':point,'point_state':states[point]['id'],'path_state_index':path,'path_state':states[path]['id'],'max_posterior':max(posterior),'entropy_bits':-math.fsum(p*math.log2(p) for p in posterior if p>0),'different':point!=path,'backpointers':vi['backpointers'][i],'constraint_applied':rule is not None,'allowed_state_ids':rule['allowed_state_ids'] if rule else [],'point_constraint_satisfied':states[point]['id'] in rule['allowed_state_ids'] if rule else True,'path_constraint_satisfied':states[path]['id'] in rule['allowed_state_ids'] if rule else True})
 counts={s['id']:sum(r['path_state']==s['id'] for r in out) for s in states}
 result={'rows':out,'point_count':len(rows),'borehole':snapshot['borehole'],'depth_start':rows[0]['depth_m'],'depth_end':rows[-1]['depth_m'],'depth_step_m':1.,'model':model,'forward_backward':fb,'viterbi':vi,'path_log_posterior':vi['relative_log_joint_density']-fb['relative_log_likelihood'],'path_counts':counts,'point_path_disagreements':sum(r['different'] for r in out),'mean_max_posterior':math.fsum(r['max_posterior'] for r in out)/len(out),'path_changes':sum(a['path_state']!=b['path_state'] for a,b in zip(out,out[1:])),'checksum':checksum,'source':snapshot['source'],'constraint_summary':{'constrained':bool(constraints),'depth_constraint_count':len(constraints),'constraint_source_run_id':snapshot.get('constraint_source_run_id',''),'depth_constraints':constraints},'limitations':['高斯HMM为已配置模型，不从truth学习；标签是隐状态，不是真实地层','后验使用整段未来观测，属于离线平滑；Viterbi是整条路径MAP','固定完整1米孔段，不跨缺采样串链；模拟参考列不参与推断','后验是给定模型下概率，不是岩性确认或地质安全判断','复核深度允许状态是证据约束，不改变模型参数；约束与零转移冲突时运行失败并标出无法连通孔段']}
 if diag is not None:
  result['constraint_summary']['feasible']=diag['feasible'];result['constraint_summary']['reachable_depth_indices']=diag['reachable_depth_indices'];result['constraint_summary']['blocked_segments']=diag['blocked_segments']
 return result
