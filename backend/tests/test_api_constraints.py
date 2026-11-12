import os,unittest
os.environ['DATABASE_URL']='sqlite:////tmp/stratum-api-smoke.sqlite'
os.environ['SEED_DEMO']='false';os.environ['TASK_MODE']='inline'
from fastapi.testclient import TestClient
from src.main import app
from src.services.seed import seed
from src.utils import repository as repo
class ApiSmokeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if os.path.exists('/tmp/stratum-api-smoke.sqlite'):os.remove('/tmp/stratum-api-smoke.sqlite')
  seed();cls.client=TestClient(app)
 def _token(self,email):
  r=self.client.post('/auth/login',json={'email':email,'password':'Stratum2026!'});self.assertEqual(r.status_code,200,r.text);return r.json()['access_token']
 def _auth(self,email):return {'Authorization':'Bearer '+self._token(email)}
 def test_studies_expose_constraint_fields(self):
  r=self.client.get('/studies',headers=self._auth('viewer@shenxi.test'));self.assertEqual(r.status_code,200)
  by_id={s['id']:s for s in r.json()}
  self.assertEqual(by_id['study-sequence']['depth_constraint_count'],0)
  self.assertEqual(by_id['study-constrained']['depth_constraint_count'],3)
  self.assertEqual(by_id['study-constrained']['constraint_source_run_id'],'run-demo')
 def test_constrained_study_create_and_run(self):
  h=self._auth('analyst@shenxi.test')
  body={'name':'API约束研究','dataset_id':'ds-boreholes','model_id':'model-gaussian3','borehole':'SX-02','depth_constraints':[{'depth_m':110.,'allowed_state_ids':['S1']},{'depth_m':150.,'allowed_state_ids':['S2','S3']}]}
  r=self.client.post('/studies',json=body,headers=h);self.assertEqual(r.status_code,201,r.text);study=r.json()
  self.assertEqual(study['depth_constraint_count'],2)
  r=self.client.post('/runs',json={'study_id':study['id']},headers=h);self.assertEqual(r.status_code,201,r.text);run=r.json();self.assertEqual(run['status'],'completed')
  res=run['result'];self.assertTrue(res['constraint_summary']['constrained'])
  flagged=[row for row in res['rows'] if row['constraint_applied']];self.assertEqual(len(flagged),2)
  self.assertTrue(all(row['point_constraint_satisfied'] and row['path_constraint_satisfied'] for row in flagged))
 def test_conflict_run_failed_and_cannot_be_reviewed(self):
  r=self.client.get('/runs',headers=self._auth('analyst@shenxi.test'));conflict=next(x for x in r.json() if x['id']=='run-conflict')
  self.assertEqual(conflict['status'],'failed');self.assertTrue(conflict['result']['constraint_conflict']['blocked_segments'])
  h=self._auth('analyst@shenxi.test')
  r=self.client.post('/reviews',json={'run_id':'run-conflict','comment':'失败结果不应被允许提审的说明文字'},headers=h)
  self.assertIn(r.status_code,(400,422));self.assertIn('不能提交复核',r.json()['detail'])
 def test_constraint_validation_errors(self):
  h=self._auth('analyst@shenxi.test')
  base={'name':'非法约束研究','dataset_id':'ds-boreholes','model_id':'model-gaussian3','borehole':'SX-02'}
  r=self.client.post('/studies',json={**base,'depth_constraints':[{'depth_m':999.,'allowed_state_ids':['S1']}]},headers=h)
  self.assertEqual(r.status_code,422);self.assertIn('孔段',r.json()['detail'])
  r=self.client.post('/studies',json={**base,'depth_constraints':[{'depth_m':100.,'allowed_state_ids':['NOPE']}]},headers=h)
  self.assertEqual(r.status_code,422);self.assertIn('不存在',r.json()['detail'])
 def test_viewer_cannot_create_study(self):
  r=self.client.post('/studies',json={'name':'越权研究','dataset_id':'ds-boreholes','model_id':'model-gaussian3','borehole':'SX-02'},headers=self._auth('viewer@shenxi.test'))
  self.assertEqual(r.status_code,403)
 def test_snapshot_holds_constraints_and_checksum_changes(self):
  studies={s['id']:s for s in repo.all_rows('studies')}
  snap=studies['study-constrained']['snapshot']
  self.assertEqual([c['depth_m'] for c in snap['depth_constraints']],[105.,140.,230.])
  self.assertEqual(snap['constraint_source_run_id'],'run-demo')
  self.assertNotEqual(studies['study-sequence']['checksum'],studies['study-constrained']['checksum'])
if __name__=='__main__':unittest.main()
