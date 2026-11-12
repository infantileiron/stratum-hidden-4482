import csv,io
from fastapi import HTTPException
from src.models.entities import Report
from src.config.settings import ARTIFACT_DIR
from src.utils import repository as repo
from src.utils.identity import new_id,now
def safe_cell(v):return "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v
def list_reports():return repo.all_rows('reports')
def create(data):
 run,review=repo.get('runs',data.run_id),repo.get('reviews',data.review_id)
 if review['status']!='approved' or review['run_id']!=run['id'] or run['status']!='completed':raise ValueError('报告必须引用该运行批准复核')
 report=repo.put('reports',Report(new_id('rpt'),data.run_id,data.review_id,data.title,now()));ARTIFACT_DIR.mkdir(parents=True,exist_ok=True);(ARTIFACT_DIR/(report['id']+'.csv')).write_text(download(report['id']),encoding='utf-8');return report
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result'];review=repo.get('reviews',report['review_id'])
 if review['status']!='approved':raise HTTPException(403,'复核未通过')
 cs=r.get('constraint_summary',{});constraints=cs.get('depth_constraints',[])
 out=io.StringIO();w=csv.writer(out);states=r['model']['config']['states'];w.writerow(['report','borehole','model','revision','log_likelihood','path_joint_log_density','path_log_posterior','checksum','depth_constraint_count','constraint_source_run_id']);w.writerow([safe_cell(report['title']),r['borehole'],safe_cell(r['model']['name']),r['model']['revision'],r['forward_backward']['log_likelihood'],r['viterbi']['log_joint_density'],r['path_log_posterior'],r['checksum'],cs.get('depth_constraint_count',0),safe_cell(cs.get('constraint_source_run_id','') or '无')]);w.writerow([])
 w.writerow(['review_depth_constraints_evidence'])
 if constraints:
  w.writerow(['depth_m','allowed_state_ids','allowed_state_names'])
  for c in constraints:w.writerow([c['depth_m'],'|'.join(c['allowed_state_ids']),'|'.join(c['allowed_state_names'])])
 else:w.writerow(['无深度允许状态约束（无约束整孔推断）'])
 w.writerow([]);w.writerow(['model_state_id','human_name','mean','variance','initial_probability'])
 for i,s in enumerate(states):w.writerow([s['id'],safe_cell(s['name']),s['mean'],s['variance'],r['model']['config']['initial'][i]])
 w.writerow(['transition_row_order']+[s['id'] for s in states])
 for s,row in zip(states,r['model']['config']['transition']):w.writerow([s['id']]+row)
 w.writerow([]);w.writerow(['depth_m','measurement','simulation_reference_unused','point_posterior_argmax','whole_path_MAP','max_posterior','entropy_bits','constraint_applied','allowed_states_at_depth','point_satisfies_constraint','path_satisfies_constraint']+['posterior_'+s['id'] for s in states]+['backpointer_'+s['id'] for s in states])
 for p in r['rows']:
  allowed='|'.join(p.get('allowed_state_ids',[]));w.writerow([p['depth_m'],p['value'],safe_cell(p['truth']),p['point_state'],p['path_state'],p['max_posterior'],p['entropy_bits'],'是' if p.get('constraint_applied') else '否',allowed or '不限制','是' if p.get('point_constraint_satisfied',True) else '否','是' if p.get('path_constraint_satisfied',True) else '否']+p['posterior']+[states[j]['id'] if j is not None else '' for j in p['backpointers']])
 return '﻿'+out.getvalue()
