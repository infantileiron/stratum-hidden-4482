import math
from src.services.hmm_math import validate,logsumexp,safelog,NEG_INF,json_logs,relative_emissions
from src.services.constraints import apply_row_mask
def forward_backward(values,initial,transition,means,variances,masks=None):
 pi,A,E=validate(values,initial,transition,means,variances);E,emission_offsets=relative_emissions(E);n=len(values);k=len(pi)
 if masks is not None:E=[apply_row_mask(row,mask) for row,mask in zip(E,masks)]
 logA=[[safelog(x) for x in row] for row in A];first=[safelog(pi[j])+E[0][j] for j in range(k)];c=logsumexp(first)
 if c==NEG_INF:raise ValueError('观测在配置模型与复核约束下无可行路径')
 alpha=[[x-c for x in first]];scales=[c]
 for t in range(1,n):
  raw=[E[t][j]+logsumexp(alpha[-1][i]+logA[i][j] for i in range(k)) for j in range(k)];c=logsumexp(raw)
  if c==NEG_INF:raise ValueError('配置零转移或复核约束导致该完整孔段无可行路径')
  alpha.append([x-c for x in raw]);scales.append(c)
 beta=[[0.]*k for _ in values]
 for t in range(n-2,-1,-1):beta[t]=[logsumexp(logA[i][j]+E[t+1][j]+beta[t+1][j] for j in range(k))-scales[t+1] for i in range(k)]
 posterior=[]
 for t in range(n):
  raw=[alpha[t][j]+beta[t][j] for j in range(k)];z=logsumexp(raw);row=[0. if p==NEG_INF else math.exp(p-z) for p in raw];s=math.fsum(row);posterior.append([p/s for p in row])
 return {'posterior':posterior,'point_map':[max(range(k),key=lambda j:row[j]) for row in posterior],'log_likelihood':math.fsum(emission_offsets+scales),'relative_log_likelihood':math.fsum(scales),'emission_log_offsets':emission_offsets,'log_alpha':json_logs(alpha),'log_beta':json_logs(beta),'log_scales':scales,'point_count':n,'state_count':k,'constrained':masks is not None,'note':'每步logsumexp缩放；每个深度后验单独稳定归一；null日志项表示负无穷不可达；复核约束将不允许状态按负无穷证据处理'}
