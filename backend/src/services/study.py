import json,hashlib,math
from src.models.entities import SequenceStudy
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_studies():return [{k:v for k,v in s.items() if k!='snapshot'} for s in repo.all_rows('studies')]
def lock_snapshot(dataset,model,borehole):
 rows=[r for r in dataset['rows'] if r['borehole']==borehole]
 if len(rows)<3 or any(not math.isclose(b['depth_m']-a['depth_m'],1.,rel_tol=0,abs_tol=1e-9) for a,b in zip(rows,rows[1:])):raise ValueError('需选择存在且完整的1米等距孔段，不跨缺层')
 snapshot={'rows':rows,'model':{k:model[k] for k in ('id','name','revision','config')},'borehole':borehole,'depth_step_m':1.,'dataset_name':dataset['name'],'source':dataset['source']};checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest();return snapshot,checksum
def create(data):
 d=repo.get('datasets',data.dataset_id);m=repo.get('state_models',data.model_id);snapshot,checksum=lock_snapshot(d,m,data.borehole)
 return repo.put('studies',SequenceStudy(new_id('study'),data.name,data.dataset_id,data.model_id,data.borehole,snapshot,checksum,now()))
