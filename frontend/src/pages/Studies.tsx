import {useEffect,useMemo,useState} from 'react';import * as api from '../api/studies';import * as models from '../api/models';import * as datasets from '../api/datasets';import * as runs from '../api/runs';import {useResource} from '../hooks/useResource';import {refreshResources} from '../stores/resources';import PageTitle from '../components/common/PageTitle';import Notice from '../components/common/Notice';import ConstraintEditor from '../components/ConstraintEditor';import {shortHash} from '../utils/format';import type {DepthConstraintInput,Study,User} from '../types/entities';
export default function Studies({user}:{user:User}){
 const{data,error}=useResource(api.list,[]),{data:ds}=useResource(datasets.list,[]),{data:ms}=useResource(models.list,[]),{data:allRuns}=useResource(runs.list,[]);
 const[name,setName]=useState('完整孔段隐状态复核'),[dataset,setDataset]=useState('ds-boreholes'),[model,setModel]=useState('model-gaussian3'),[hole,setHole]=useState('SX-01'),[constraints,setConstraints]=useState<DepthConstraintInput[]>([]),[sourceRun,setSourceRun]=useState(''),[message,setMessage]=useState('');
 const selectedDataset=ds.find(d=>d.id===dataset);const selectedModel=ms.find(m=>m.id===model);
 const [detail,setDetail]=useState<datasets.DatasetDetail|null>(null);
 useEffect(()=>{let alive=true;datasets.detail(dataset).then(d=>{if(alive)setDetail(d)}).catch(()=>{if(alive)setDetail(null)});return()=>{alive=false}},[dataset]);
 const depths=useMemo(()=>(detail?.rows??[]).filter(r=>r.borehole===hole).map(r=>r.depth_m),[detail,hole]);
 const depthKey=depths.join(',');
 useEffect(()=>{setConstraints(prev=>prev.filter(c=>depthKey.split(',').map(Number).includes(c.depth_m)))},[depthKey]);
 const sourceRuns=allRuns.filter(r=>r.status==='completed');
 return <><PageTitle chapter="04 / SNAPSHOT & DECODE" title="完整孔段、模型版本与复核证据，一起锁定" description="选择整个等距孔段，并可为多个已复核深度限定允许状态。约束进入研究快照与SHA256，整孔后验与整条MAP共同遵守；规则更新即新建研究，旧批准结果和报告保留。"/>
 <Notice error={error||message}/>
 {user.role!=='viewer'&&<form className="paper form-grid" onSubmit={async e=>{e.preventDefault();try{await api.create({name,dataset_id:dataset,model_id:model,borehole:hole,depth_constraints:constraints,constraint_source_run_id:sourceRun});setMessage('');setConstraints([]);refreshResources()}catch(e:any){setMessage(e.message)}}}>
  <label>研究名称<input aria-label="研究名称" value={name} onChange={e=>setName(e.target.value)}/></label>
  <label>测井数据<select aria-label="测井数据" value={dataset} onChange={e=>{const id=e.target.value;setDataset(id);setHole(ds.find(d=>d.id===id)?.boreholes[0]||'');setConstraints([])}}>{ds.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
  <label>完整孔段<select aria-label="完整孔段" value={hole} onChange={e=>{setHole(e.target.value);setConstraints([])}}>{selectedDataset?.boreholes.map(h=><option key={h}>{h}</option>)}</select></label>
  <label>配置状态模型<select aria-label="配置状态模型" value={model} onChange={e=>{setModel(e.target.value);setConstraints([])}}>{ms.map(m=><option key={m.id} value={m.id}>{m.name} / v{m.revision}</option>)}</select></label>
  <label className="wide">约束证据来源运行（可选，仅记录溯源，不复制规则）<select aria-label="约束证据来源运行" value={sourceRun} onChange={e=>setSourceRun(e.target.value)}><option value="">无（直接录入复核规则）</option>{sourceRuns.map(r=><option key={r.id} value={r.id}>{r.id} · {r.study_id}</option>)}</select></label>
  {selectedModel&&<ConstraintEditor states={selectedModel.config.states} depths={depths} constraints={constraints} onChange={setConstraints}/>}
  <button className="primary">锁定序列研究（含约束快照）</button>
 </form>}
 <section className="paper"><h2>锁定的研究</h2>{data.map((s:Study)=><article className="record study-record" key={s.id}><div><b>{s.name}</b><small>{s.borehole} / {s.model_id}<br/>SHA256 {shortHash(s.checksum)}</small>{s.depth_constraint_count>0?<p className="constraint-badge">复核约束 {s.depth_constraint_count} 个深度{s.constraint_source_run_id?` · 证据来源 ${s.constraint_source_run_id}`:''}</p>:<p className="constraint-badge muted">无深度约束 · 整孔自由推断</p>}</div>{user.role!=='viewer'&&<button onClick={async()=>{try{const r=await runs.create({study_id:s.id});sessionStorage.setItem('stratum-selected-run',r.id);location.hash='results';refreshResources()}catch(e:any){setMessage(e.message)}}}>提交Redis解码 ↗</button>}</article>)}</section></>}
