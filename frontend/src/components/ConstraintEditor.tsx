import type {State} from '../types/entities';
import type {DepthConstraintInput} from '../types/entities';
export default function ConstraintEditor({states,depths,constraints,onChange}:{states:State[];depths:number[];constraints:DepthConstraintInput[];onChange:(next:DepthConstraintInput[])=>void}){
 const update=(index:number,patch:Partial<DepthConstraintInput>)=>onChange(constraints.map((c,i)=>i===index?{...c,...patch}:c));
 const toggle=(index:number,stateId:string)=>{const c=constraints[index];const has=c.allowed_state_ids.includes(stateId);const next=has?c.allowed_state_ids.filter(id=>id!==stateId):[...c.allowed_state_ids,stateId];if(next.length===0)return;update(index,{allowed_state_ids:next})};
 return <div className="constraint-editor wide">
  <div className="constraint-head"><b>复核证据 · 多深度允许状态约束</b><span>每个深度限定允许的隐状态集合；不允许的状态在整孔后验与整条MAP中按负无穷证据处理，零概率转移仍然有效。规则更新请新建研究，旧批准结果与报告保留。</span></div>
  {constraints.length===0&&<p className="constraint-empty">暂无约束：本次为无约束整孔推断。可添加已复核深度作为证据。</p>}
  {constraints.map((c,i)=><div className="constraint-row" key={i}>
   <label>深度 m
    <select aria-label={`约束深度${i+1}`} value={c.depth_m} onChange={e=>update(i,{depth_m:+e.target.value})}>{depths.map(d=><option key={d} value={d}>{d}</option>)}</select>
   </label>
   <fieldset className="allowed-states"><legend>允许状态（至少一个）</legend>{states.map(s=><label key={s.id} className="state-check"><input type="checkbox" checked={c.allowed_state_ids.includes(s.id)} onChange={()=>toggle(i,s.id)}/><span>{s.id} · {s.name}</span></label>)}</fieldset>
   <button type="button" className="danger" onClick={()=>onChange(constraints.filter((_,j)=>j!==i))}>删除该深度</button>
  </div>)}
  <button type="button" onClick={()=>onChange([...constraints,{depth_m:depths[0]??0,allowed_state_ids:states.slice(0,1).map(s=>s.id)}])} disabled={depths.length===0}>+ 添加复核深度约束</button>
 </div>;
}
