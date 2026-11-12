import type {Result} from '../types/entities';
export default function ConstraintPanel({result:r}:{result:Result}){
 const cs=r.constraint_summary;
 if(!cs?.constrained)return null;
 return <section className="paper constraint-panel">
  <h2>本次复核约束与状态序列核对</h2>
  <p className="method-note">整孔后验与整条MAP在同一组深度允许状态证据下计算：不允许的状态按负无穷处理，模型零概率转移保持有效。约束随研究快照与SHA256永久保留；{cs.constraint_source_run_id?`证据来源运行 ${cs.constraint_source_run_id}。`:'规则由地学编辑直接录入。'}</p>
  <div className="table-scroll"><table><thead><tr><th>深度 m</th><th>允许状态</th><th>状态名称</th><th>点态argmax</th><th>全路径MAP</th><th>点态遵守</th><th>路径遵守</th></tr></thead><tbody>
   {cs.depth_constraints.map((c,i)=>{const row=r.rows[c.depth_index];return <tr key={i}><td>{c.depth_m}</td><td>{c.allowed_state_ids.join('、')}</td><td>{c.allowed_state_names.join('、')}</td><td>{row.point_state}</td><td>{row.path_state}</td><td>{row.point_constraint_satisfied?'✓ 遵守':'✗ 违反'}</td><td>{row.path_constraint_satisfied?'✓ 遵守':'✗ 违反'}</td></tr>})}
  </tbody></table></div>
 </section>;
}
