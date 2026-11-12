import type {ConstraintConflict} from '../types/entities';
import {conflictReasonLabels} from '../constants/enums';
export default function ConflictNotice({conflict}:{conflict:ConstraintConflict}){
 const first=conflict.first_failed_constraint;
 return <section className="paper conflict-panel" role="alert">
  <h2>复核约束冲突 · 无法连通的孔段</h2>
  <p className="conflict-lead">约束与模型零概率转移不存在共同可行的完整状态序列，本次运行标记为<b>失败</b>，不能提交复核、不能生成报告。请放宽某深度允许状态或新建研究后重算。</p>
  <div className="blocked-segments">{conflict.blocked_segments.length===0?<span>整孔无可行路径</span>:conflict.blocked_segments.map((b,i)=><span key={i} className="blocked-chip">{b.depth_start_m}—{b.depth_end_m} m · {b.point_count} 点不可连通</span>)}</div>
  {first&&<dl className="first-failure">
   <div><dt>首个断裂深度</dt><dd>{first.depth_m} m</dd></div>
   <div><dt>该深度允许状态</dt><dd>{first.allowed_state_ids.join('、')||'（空）'}</dd></div>
   <div><dt>约束下前向可达状态</dt><dd>{first.forward_reachable_state_ids.join('、')||'无（−∞）'}</dd></div>
   <div><dt>约束下后向可达状态</dt><dd>{first.backward_reachable_state_ids.join('、')||'无（−∞）'}</dd></div>
   <div className="wide"><dt>断裂原因</dt><dd>{conflictReasonLabels[first.reason]??first.reason}</dd></div>
  </dl>}
  <h3>逐条约束可达性核查</h3>
  <div className="table-scroll"><table><thead><tr><th>深度 m</th><th>允许状态</th><th>前向可达（约束内）</th><th>无约束前向可达</th><th>后向可达</th><th>结论</th></tr></thead><tbody>
   {conflict.constraints.map((c,i)=><tr key={i} className={c.prefix_feasible?'':'broken'}><td>{c.depth_m}</td><td>{c.allowed_state_ids.join('、')}</td><td>{(c.forward_reachable_state_ids??[]).join('、')||'−∞ 不可达'}</td><td>{(c.raw_forward_reachable_state_ids??[]).join('、')||'−∞'}</td><td>{(c.backward_reachable_state_ids??[]).join('、')||'−∞ 不可达'}</td><td>{c.feasible?'可贯通':'断裂'}</td></tr>)}
  </tbody></table></div>
 </section>;
}
