import math
from src.services.hmm_math import validate,safelog,NEG_INF,json_logs,relative_emissions
from src.services.constraints import apply_row_mask
def viterbi(values,initial,transition,means,variances,masks=None):
 pi,A,E=validate(values,initial,transition,means,variances);E,emission_offsets=relative_emissions(E);k=len(pi)
 if masks is not None:E=[apply_row_mask(row,mask) for row,mask in zip(E,masks)]
 logA=[[safelog(p) for p in row] for row in A];first=[safelog(pi[j])+E[0][j] for j in range(k)];offset=max(first)
 if offset==NEG_INF:raise ValueError('Viterbi无可行初始路径')
 delta=[[v-offset for v in first]];offsets=[offset];back=[[None]*k]
 for t in range(1,len(values)):
  raw=[];pointers=[]
  for j in range(k):
   candidates=[delta[-1][i]+logA[i][j] for i in range(k)];i=max(range(k),key=lambda s:candidates[s]);best=candidates[i];raw.append(best+E[t][j]);pointers.append(None if best==NEG_INF else i)
  offset=max(raw)
  if offset==NEG_INF:raise ValueError('Viterbi无可行完整路径')
  delta.append([v-offset for v in raw]);offsets.append(offset);back.append(pointers)
 last=max(range(k),key=lambda j:delta[-1][j]);path=[last]
 for t in range(len(values)-1,0,-1):
  last=back[t][last]
  if last is None:raise ValueError('Viterbi回溯遇不可达状态')
  path.append(last)
 path.reverse()
 return {'path':path,'log_probability':math.fsum(emission_offsets+offsets)+max(delta[-1]),'log_joint_density':math.fsum(emission_offsets+offsets)+max(delta[-1]),'relative_log_joint_density':math.fsum(offsets)+max(delta[-1]),'emission_log_offsets':emission_offsets,'backpointers':back,'log_scores_relative':json_logs(delta),'log_offsets':offsets,'point_count':len(values),'state_count':k,'constrained':masks is not None,'note':'整条路径MAP；逐步回溯，不是逐点后验argmax；精确同分取配置状态顺序优先；复核约束下只在允许状态集合内回溯'}
