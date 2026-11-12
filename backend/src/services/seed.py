import random
from src.utils import repository as repo
from src.utils.identity import now
from src.utils.security import hash_password
from src.services.statistics import analyze
from src.services.constraints import ConstraintConflict
from src.services.study import lock_snapshot
def demo_config():return {'states':[{'id':'S1','name':'低响应态','mean':45.,'variance':16.},{'id':'S2','name':'中响应态','mean':70.,'variance':25.},{'id':'S3','name':'高响应态','mean':98.,'variance':16.}],'initial':[.6,.3,.1],'transition':[[.94,.05,.01],[.04,.92,.04],[.01,.06,.93]]}
def locked_chain_config():return {'states':[{'id':'S1','name':'低响应态','mean':45.,'variance':16.},{'id':'S2','name':'中响应态','mean':70.,'variance':25.},{'id':'S3','name':'高响应态','mean':98.,'variance':16.}],'initial':[1.,0.,0.],'transition':[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]}
def demo_rows():
 rng=random.Random(2409);c=demo_config();rows=[]
 def choose(weights):
  u=rng.random();total=0
  for i,p in enumerate(weights):
   total+=p
   if u<=total:return i
  return len(weights)-1
 for hole in ['SX-01','SX-02','SX-03']:
  state=choose(c['initial'])
  for i in range(160):
   if i:state=choose(c['transition'][state])
   s=c['states'][state];value=rng.gauss(s['mean'],s['variance']**.5)
   if i in (39,83,121):value+=14 if state<2 else -14
   rows.append({'borehole':hole,'depth_m':100.+i,'value':value,'truth':s['id']})
 return rows
def _failed_run(run_id,study_id,snapshot,checksum):
 try:
  analyze(snapshot,checksum);return {'id':run_id,'study_id':study_id,'status':'completed','result':{},'error':'','created_at':now()}
 except ConstraintConflict as exc:
  return {'id':run_id,'study_id':study_id,'status':'failed','result':{'constraint_conflict':exc.payload},'error':str(exc),'created_at':now()}
def seed():
 repo.init_db()
 for role,name in [('admin','孔段复核地学编辑'),('analyst','测井序列分析员'),('viewer','地研档案阅览员')]:
  email=f'{role}@shenxi.test';repo.put('users',{'id':email,'email':email,'name':name,'role':role,'password_hash':hash_password('Stratum2026!')},insert_only=True)
 d={'id':'ds-boreholes','name':'沉溪三孔 · 1米完整测井','source':'shenxi_logs_202611.csv','rows':demo_rows(),'created_at':now()};repo.put('datasets',d,insert_only=True)
 m={'id':'model-gaussian3','name':'三态高斯响应模型 · 人工命名v1','config':demo_config(),'revision':1,'created_at':now()};repo.put('state_models',m,insert_only=True)
 m2={'id':'model-locked-chain','name':'三态零转移锁定链 · 复核冲突演示','config':locked_chain_config(),'revision':1,'created_at':now()};repo.put('state_models',m2,insert_only=True)
 snapshot,checksum=lock_snapshot(d,m,'SX-01');study={'id':'study-sequence','name':'SX-01完整160米孔段复核','dataset_id':d['id'],'model_id':m['id'],'borehole':'SX-01','snapshot':snapshot,'checksum':checksum,'created_at':now(),'depth_constraint_count':0,'constraint_source_run_id':''};repo.put('studies',study,insert_only=True)
 repo.put('runs',{'id':'run-demo','study_id':study['id'],'status':'completed','result':analyze(snapshot,checksum),'error':'','created_at':now()},insert_only=True)
 repo.put('reviews',{'id':'review-demo','run_id':'run-demo','comment':'完整1米孔段、配置模型版本、点态后验与全路径MAP已分开核查。状态名是模型标签非地层真值。','status':'approved','reviewer':'admin@shenxi.test','created_at':now()},insert_only=True)
 repo.put('reports',{'id':'report-demo','run_id':'run-demo','review_id':'review-demo','title':'沉溪SX-01模型隐状态序列复核册','created_at':now()},insert_only=True)
 evidence_constraints=[{'depth_m':105.,'allowed_state_ids':['S1','S2']},{'depth_m':140.,'allowed_state_ids':['S2','S3']},{'depth_m':230.,'allowed_state_ids':['S1','S2','S3']}]
 snap2,sum2=lock_snapshot(d,m,'SX-01',evidence_constraints,'run-demo');study2={'id':'study-constrained','name':'SX-01复核证据约束重算（多深度允许状态）','dataset_id':d['id'],'model_id':m['id'],'borehole':'SX-01','snapshot':snap2,'checksum':sum2,'created_at':now(),'depth_constraint_count':len(snap2['depth_constraints']),'constraint_source_run_id':'run-demo'};repo.put('studies',study2,insert_only=True)
 repo.put('runs',{'id':'run-constrained','study_id':study2['id'],'status':'completed','result':analyze(snap2,sum2),'error':'','created_at':now()},insert_only=True)
 conflict_constraints=[{'depth_m':100.,'allowed_state_ids':['S1']},{'depth_m':120.,'allowed_state_ids':['S2']}]
 snap3,sum3=lock_snapshot(d,m2,'SX-01',conflict_constraints);study3={'id':'study-conflict','name':'SX-01零转移与复核约束冲突（失败不可提审）','dataset_id':d['id'],'model_id':m2['id'],'borehole':'SX-01','snapshot':snap3,'checksum':sum3,'created_at':now(),'depth_constraint_count':len(snap3['depth_constraints']),'constraint_source_run_id':''};repo.put('studies',study3,insert_only=True)
 repo.put('runs',_failed_run('run-conflict',study3['id'],snap3,sum3),insert_only=True)
 return {t:len(repo.all_rows(t)) for t in ('users','datasets','state_models','studies','runs','reviews','reports')}
