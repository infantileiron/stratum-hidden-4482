import unittest
from src.services.forward_backward import forward_backward
from src.services.viterbi import viterbi
from src.services.constraints import build_masks,constraint_conflicts,ConstraintConflict,raise_if_conflict
from src.services.statistics import analyze
class ConstraintMathTests(unittest.TestCase):
 def setUp(self):
  self.states=[{'id':'S1','name':'低','mean':45.,'variance':16.},{'id':'S2','name':'中','mean':70.,'variance':25.},{'id':'S3','name':'高','mean':98.,'variance':16.}]
  self.rows=[{'borehole':'X','depth_m':100.+t,'value':v,'truth':None} for t,v in enumerate([46.,71.,99.,47.,72.,97.,45.,70.])]
  self.pi=[.6,.3,.1]
  self.A=[[.94,.05,.01],[.04,.92,.04],[.01,.06,.93]]
  self.means=[45.,70.,98.];self.vars=[16.,25.,16.]
 def _masks(self,cs):
  masks,norm=build_masks(self.rows,self.states,cs);return masks
 def test_unconstrained_equivalence(self):
  values=[r['value'] for r in self.rows]
  fb0=forward_backward(values,self.pi,self.A,self.means,self.vars)
  all_true=[[True]*3 for _ in self.rows]
  fb1=forward_backward(values,self.pi,self.A,self.means,self.vars,all_true)
  self.assertFalse(fb0['constrained']);self.assertTrue(fb1['constrained'])
  self.assertEqual(fb0['posterior'],fb1['posterior']);self.assertEqual(fb0['point_map'],fb1['point_map'])
  v0=viterbi(values,self.pi,self.A,self.means,self.vars)
  v1=viterbi(values,self.pi,self.A,self.means,self.vars,all_true)
  self.assertEqual(v0['path'],v1['path'])
 def test_constrained_posterior_and_path(self):
  cs=[{'depth_m':102.,'allowed_state_ids':['S1']},{'depth_m':105.,'allowed_state_ids':['S1','S2']}]
  masks=self._masks(cs);values=[r['value'] for r in self.rows]
  fb=forward_backward(values,self.pi,self.A,self.means,self.vars,masks)
  vi=viterbi(values,self.pi,self.A,self.means,self.vars,masks)
  self.assertEqual(fb['posterior'][2],[1.,0.,0.]);self.assertAlmostEqual(sum(fb['posterior'][2]),1.)
  self.assertEqual(vi['path'][2],0);self.assertIn(vi['path'][5],(0,1))
  for t,allowed in ((2,{0}),(5,{0,1})):
   self.assertIn(vi['path'][t],allowed)
   self.assertTrue(all(fb['posterior'][t][j]==0. for j in range(3) if j not in allowed))
   self.assertAlmostEqual(sum(fb['posterior'][t]),1.)
 def test_zero_transition_still_blocks(self):
  pi=[1.,0.,0.];A=[[.8,.2,0.],[.3,.7,0.],[0.,0.,1.]]
  cs=[{'depth_m':107.,'allowed_state_ids':['S3']}]
  diag=constraint_conflicts(pi,A,self.rows,self.states,cs)
  self.assertFalse(diag['feasible'])
  self.assertEqual(diag['blocked_segments'],[{'depth_start_m':100.,'depth_end_m':107.,'point_count':8}])
  self.assertEqual(diag['reachable_depth_indices'],[False]*8)
  self.assertEqual(diag['first_failed_constraint']['depth_m'],107.)
  self.assertEqual(diag['first_failed_constraint']['reason'],'no_feasible_prefix')
  with self.assertRaises(ConstraintConflict):raise_if_conflict(diag)
 def test_one_way_chain_absorbing_conflict(self):
  states2=self.states[:2];pi=[1.,0.];A=[[.4,.6],[0.,1.]]
  rows=self.rows[:4];cs=[{'depth_m':101.,'allowed_state_ids':['S2']},{'depth_m':103.,'allowed_state_ids':['S1']}]
  diag=constraint_conflicts(pi,A,rows,states2,cs)
  self.assertFalse(diag['feasible'])
  self.assertEqual(diag['blocked_segments'],[{'depth_start_m':100.,'depth_end_m':103.,'point_count':4}])
  self.assertEqual(diag['reachable_depth_indices'],[False]*4)
  self.assertEqual(diag['first_failed_constraint']['depth_m'],103.)
  self.assertEqual(diag['first_failed_constraint']['reason'],'no_feasible_prefix')
  self.assertEqual(diag['constraints'][0]['forward_reachable_state_ids'],['S2'])
  self.assertEqual(diag['constraints'][1]['forward_reachable_state_ids'],[])
 def test_initial_state_zero_probability_conflict(self):
  pi=[0.,1.,0.];A=self.A
  diag=constraint_conflicts(pi,A,self.rows[:3],self.states,[{'depth_m':100.,'allowed_state_ids':['S1']}])
  self.assertFalse(diag['feasible'])
  self.assertEqual(diag['first_failed_constraint']['depth_m'],100.)
  self.assertEqual(diag['first_failed_constraint']['reason'],'zero_initial_probability')
 def test_absorbing_state_prefix_conflict(self):
  states2=self.states[:2];pi=[1.,0.];A=[[.5,.5],[0.,1.]]
  cs=[{'depth_m':101.,'allowed_state_ids':['S2']},{'depth_m':103.,'allowed_state_ids':['S1']}]
  diag=constraint_conflicts(pi,A,self.rows[:4],states2,cs)
  self.assertFalse(diag['feasible'])
  self.assertEqual(diag['first_failed_constraint']['depth_m'],103.)
  self.assertEqual(diag['first_failed_constraint']['reason'],'no_feasible_prefix')
  self.assertEqual(diag['constraints'][0]['prefix_feasible'],True)
  self.assertEqual(diag['constraints'][0]['forward_reachable_state_ids'],['S2'])
  self.assertEqual(diag['constraints'][1]['forward_reachable_state_ids'],[])
  self.assertIn('S2',diag['constraints'][1]['raw_forward_reachable_state_ids'])
 def test_no_feasible_continuation_branch(self):
  states2=self.states[:2];pi=[1.,0.];A=[[.5,.5],[.5,.5]]
  diag=constraint_conflicts(pi,A,self.rows[:4],states2,[{'depth_m':103.,'allowed_state_ids':['S1']}])
  self.assertTrue(diag['feasible'])
  diag_bad=constraint_conflicts([1.,0.],[[1.,0.],[0.,1.]],self.rows[:4],states2,[{'depth_m':102.,'allowed_state_ids':['S1']},{'depth_m':103.,'allowed_state_ids':['S2']}])
  self.assertFalse(diag_bad['feasible'])
  self.assertEqual(diag_bad['first_failed_constraint']['depth_m'],103.)
  self.assertEqual(diag_bad['first_failed_constraint']['reason'],'no_feasible_prefix')
 def test_feasible_diag_and_analyze(self):
  cs=[{'depth_m':101.,'allowed_state_ids':['S2','S3']}]
  diag=constraint_conflicts(self.pi,self.A,self.rows,self.states,cs)
  self.assertTrue(diag['feasible']);self.assertEqual(diag['blocked_segments'],[]);self.assertIsNone(diag['first_failed_constraint'])
  snapshot={'rows':self.rows,'model':{'id':'m','name':'模型','revision':1,'config':{'states':self.states,'initial':self.pi,'transition':self.A}},'borehole':'X','source':'t.csv','depth_constraints':diag['constraints'],'constraint_source_run_id':''}
  result=analyze(snapshot,'chk')
  row=result['rows'][1]
  self.assertTrue(row['constraint_applied']);self.assertEqual(row['allowed_state_ids'],['S2','S3'])
  self.assertTrue(row['point_constraint_satisfied']);self.assertTrue(row['path_constraint_satisfied'])
  self.assertIn(result['rows'][1]['path_state_index'],(1,2))
  self.assertEqual(result['constraint_summary']['depth_constraint_count'],1)
 def test_mask_validation_errors(self):
  with self.assertRaises(ValueError):build_masks(self.rows,self.states,[{'depth_m':999.,'allowed_state_ids':['S1']}])
  with self.assertRaises(ValueError):build_masks(self.rows,self.states,[{'depth_m':100.,'allowed_state_ids':['S9']}])
  with self.assertRaises(ValueError):build_masks(self.rows,self.states,[{'depth_m':100.,'allowed_state_ids':[]}])
  with self.assertRaises(ValueError):build_masks(self.rows,self.states,[{'depth_m':100.,'allowed_state_ids':['S1','S1']}])
  with self.assertRaises(ValueError):build_masks(self.rows,self.states,[{'depth_m':100.,'allowed_state_ids':['S1']},{'depth_m':100.,'allowed_state_ids':['S2']}])
 def test_analyze_conflict_payload(self):
  pi=[1.,0.,0.];A=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
  cs=[{'depth_m':100.,'allowed_state_ids':['S1']},{'depth_m':102.,'allowed_state_ids':['S2']}]
  _,norm=build_masks(self.rows,self.states,cs)
  snapshot={'rows':self.rows,'model':{'id':'m','name':'锁定','revision':1,'config':{'states':self.states,'initial':pi,'transition':A}},'borehole':'X','source':'t.csv','depth_constraints':norm,'constraint_source_run_id':''}
  try:analyze(snapshot,'chk');self.fail('应抛出约束冲突')
  except ConstraintConflict as exc:
   self.assertIn('无法连通孔段',str(exc));self.assertFalse(exc.payload['feasible'])
   self.assertEqual(exc.payload['first_failed_constraint']['depth_m'],102.)
   self.assertEqual(exc.payload['constraints'][0]['forward_reachable_state_ids'],['S1'])
   self.assertEqual(exc.payload['constraints'][1]['forward_reachable_state_ids'],[])
if __name__=='__main__':unittest.main()
