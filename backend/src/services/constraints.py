from src.services.hmm_math import NEG_INF
class ConstraintConflict(ValueError):
 def __init__(self,message,payload):
  super().__init__(message);self.payload=payload
def build_masks(rows,states,constraints):
 n,k=len(rows),len(states);id_to_index={s['id']:j for j,s in enumerate(states)};depth_index={r['depth_m']:t for t,r in enumerate(rows)};seen=set();masks=[[True]*k for _ in range(n)];normalized=[]
 for c in constraints:
  depth=c['depth_m'];allowed=list(c['allowed_state_ids'])
  if depth in seen:raise ValueError(f'深度{depth}m存在重复约束，每个深度至多限定一次允许状态')
  if depth not in depth_index:raise ValueError(f'约束深度{depth}m不在已锁定孔段内，只接受孔段实际1米采样深度')
  if not allowed:raise ValueError(f'深度{depth}m的允许状态不能为空')
  bad=[sid for sid in allowed if sid not in id_to_index]
  if bad:raise ValueError('约束引用了模型不存在的状态ID: '+','.join(bad))
  if len(set(allowed))!=len(allowed):raise ValueError(f'深度{depth}m的允许状态存在重复ID')
  t=depth_index[depth];idx=sorted({id_to_index[sid] for sid in allowed})
  masks[t]=[False]*k
  for j in idx:masks[t][j]=True
  normalized.append({'depth_m':depth,'depth_index':t,'allowed_state_ids':[states[j]['id'] for j in idx],'allowed_state_names':[states[j]['name'] for j in idx]})
  seen.add(depth)
 normalized.sort(key=lambda c:c['depth_index']);return masks,normalized
def constraint_conflicts(pi,A,rows,states,constraints):
 masks,normalized=build_masks(rows,states,constraints)
 if not normalized:return None
 n,k=len(rows),len(states)
 raw_forward=[[False]*k for _ in range(n)]
 raw_forward[0]=[pi[j]>0 for j in range(k)]
 for t in range(1,n):
  for j in range(k):
   raw_forward[t][j]=any(raw_forward[t-1][i] and A[i][j]>0 for i in range(k))
 forward=[[False]*k for _ in range(n)]
 forward[0]=[pi[j]>0 and masks[0][j] for j in range(k)]
 for t in range(1,n):
  for j in range(k):
   forward[t][j]=masks[t][j] and any(forward[t-1][i] and A[i][j]>0 for i in range(k))
 backward=[[False]*k for _ in range(n)]
 backward[n-1]=list(masks[n-1])
 for t in range(n-2,-1,-1):
  for i in range(k):
   backward[t][i]=masks[t][i] and any(A[i][j]>0 and backward[t+1][j] for j in range(k))
 reachable=[any(forward[t][j] and backward[t][j] for j in range(k)) for t in range(n)]
 blocked=[];start=None
 for t,ok in enumerate(reachable):
  if ok:
   if start is not None:
    blocked.append({'depth_start_m':rows[start]['depth_m'],'depth_end_m':rows[t-1]['depth_m'],'point_count':t-start});start=None
  elif start is None:start=t
 if start is not None:blocked.append({'depth_start_m':rows[start]['depth_m'],'depth_end_m':rows[-1]['depth_m'],'point_count':n-start})
 feasible=all(reachable)
 for item in normalized:
  t=item['depth_index']
  f_ids=[states[j]['id'] for j in range(k) if forward[t][j]]
  raw_ids=[states[j]['id'] for j in range(k) if raw_forward[t][j]]
  b_ids=[states[j]['id'] for j in range(k) if backward[t][j]]
  item['forward_reachable_state_ids']=f_ids;item['raw_forward_reachable_state_ids']=raw_ids;item['backward_reachable_state_ids']=b_ids
  item['prefix_feasible']=bool(set(f_ids).intersection(item['allowed_state_ids']))
  item['feasible']=any(forward[t][j] and backward[t][j] and masks[t][j] for j in range(k))
 first_failed=None
 for item in normalized:
  f_ids=item['forward_reachable_state_ids']
  if not f_ids:
   reason='zero_initial_probability' if item['depth_index']==0 else 'no_feasible_prefix'
   first_failed={'depth_m':item['depth_m'],'depth_index':item['depth_index'],'allowed_state_ids':item['allowed_state_ids'],'forward_reachable_state_ids':f_ids,'backward_reachable_state_ids':item['backward_reachable_state_ids'],'reason':reason};break
 if first_failed is None and not feasible:
  item=next(c for c in normalized if not c['feasible'])
  prefix_ok=bool(set(item['forward_reachable_state_ids']).intersection(item['allowed_state_ids']))
  reason='no_feasible_prefix' if not prefix_ok else 'no_feasible_continuation'
  first_failed={'depth_m':item['depth_m'],'depth_index':item['depth_index'],'allowed_state_ids':item['allowed_state_ids'],'forward_reachable_state_ids':item['forward_reachable_state_ids'],'backward_reachable_state_ids':item['backward_reachable_state_ids'],'reason':reason}
 return {'feasible':feasible,'reachable_depth_indices':reachable,'blocked_segments':blocked,'constraints':normalized,'first_failed_constraint':first_failed,'mask_allowed':masks,'state_ids':[s['id'] for s in states]}
def raise_if_conflict(diag):
 if diag is None or diag['feasible']:return
 parts='；'.join(f"{b['depth_start_m']}—{b['depth_end_m']}m({b['point_count']}点)" for b in diag['blocked_segments']) or '整孔'
 first=diag['first_failed_constraint'];detail=''
 if first:
  if first['reason']=='no_feasible_prefix':detail=f"；首个断裂点{first['depth_m']}m：零概率转移或前置约束下没有路径能到达允许状态{','.join(first['allowed_state_ids'])}"
  elif first['reason']=='zero_initial_probability':detail=f"；首个断裂点{first['depth_m']}m：初始概率为0的状态被限定为孔口允许状态{','.join(first['allowed_state_ids'])}"
  else:detail=f"；首个断裂点{first['depth_m']}m：允许状态{','.join(first['allowed_state_ids'])}之后不存在贯通孔段末尾的路径"
 message=f"复核约束与零概率转移冲突，无法连通孔段: {parts}{detail}；该运行失败，不能提交复核，请放宽允许状态或新建研究"
 raise ConstraintConflict(message,diag)
def apply_row_mask(log_row,mask):return [v if allowed else NEG_INF for v,allowed in zip(log_row,mask)]
