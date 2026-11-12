import json,hashlib,math
from src.models.entities import SequenceStudy
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services.constraints import build_masks
def list_studies():return [{k:v for k,v in s.items() if k!='snapshot'} for s in repo.all_rows('studies')]
def lock_snapshot(dataset,model,borehole,constraints=None,constraint_source_run_id=''):
 rows=[r for r in dataset['rows'] if r['borehole']==borehole]
 if len(rows)<3 or any(not math.isclose(b['depth_m']-a['depth_m'],1.,rel_tol=0,abs_tol=1e-9) for a,b in zip(rows,rows[1:])):raise ValueError('需选择存在且完整的1米等距孔段，不跨缺层')
 constraint_payload=[c.model_dump() if hasattr(c,'model_dump') else dict(c) for c in (constraints or [])]
 _,normalized=build_masks(rows,model['config']['states'],constraint_payload)
 snapshot={'rows':rows,'model':{k:model[k] for k in ('id','name','revision','config')},'borehole':borehole,'depth_step_m':1.,'dataset_name':dataset['name'],'source':dataset['source'],'depth_constraints':normalized,'constraint_source_run_id':constraint_source_run_id}
 checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest();return snapshot,checksum
def create(data):
 d=repo.get('datasets',data.dataset_id);m=repo.get('state_models',data.model_id)
 source_run_id=''
 if data.constraint_source_run_id:
  source=repo.get('runs',data.constraint_source_run_id)
  if source['status']!='completed':raise ValueError('仅可引用已完成运行的复核证据作为约束来源')
  source_study=repo.get('studies',source['study_id'])
  if source_study['borehole']!=data.borehole:raise ValueError('约束来源运行的孔段与新研究孔段不一致')
  if source_study['dataset_id']!=data.dataset_id:raise ValueError('约束来源运行的测井数据集与新研究不一致')
  source_run_id=source['id']
 snapshot,checksum=lock_snapshot(d,m,data.borehole,data.depth_constraints,source_run_id)
 return repo.put('studies',SequenceStudy(new_id('study'),data.name,data.dataset_id,data.model_id,data.borehole,snapshot,checksum,now(),len(snapshot['depth_constraints']),source_run_id))
