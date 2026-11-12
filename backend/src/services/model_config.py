import json,re
from src.services.hmm_math import validate
def parse_model(text):
 try:model=json.loads(text)
 except (TypeError,ValueError):raise ValueError('状态模型JSON解析失败')
 if not isinstance(model,dict) or not isinstance(model.get('states'),list):raise ValueError('模型需要states、initial、transition')
 states=model['states'];ids=set();clean=[]
 for state in states:
  if not isinstance(state,dict):raise ValueError('每个状态需为对象')
  id=state.get('id');name=state.get('name');mean=state.get('mean');variance=state.get('variance')
  if not isinstance(id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,20}',id) or id in ids:raise ValueError('状态ID须唯一')
  if not isinstance(name,str) or not name.strip() or len(name)>30:raise ValueError('人工状态名1—30字')
  ids.add(id);clean.append({'id':id,'name':name.strip(),'mean':mean,'variance':variance})
 initial=model.get('initial');transition=model.get('transition')
 if not isinstance(initial,list) or not isinstance(transition,list) or any(not isinstance(r,list) for r in transition):raise ValueError('初始与转移需数组')
 pi,A,_=validate([0.],initial,transition,[s['mean'] for s in clean],[s['variance'] for s in clean])
 return {'states':clean,'initial':pi,'transition':A}
