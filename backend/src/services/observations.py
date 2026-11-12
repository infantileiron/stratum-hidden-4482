import csv,io,re,math
from src.constants.domain import MAX_ROWS,MAX_HOLES
def parse_observations(text):
 reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
 if not reader.fieldnames or not {'borehole','depth_m','value'}<=set(reader.fieldnames):raise ValueError('CSV需要borehole,depth_m,value；truth仅可选模拟参考')
 rows=[];last={};counts={}
 for raw in reader:
  hole=(raw.get('borehole') or '').strip()
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,30}',hole):raise ValueError('孔ID需1—30位字母数字下划线连字符')
  try:depth=float(raw.get('depth_m') or '');value=float(raw.get('value') or '')
  except ValueError:raise ValueError('每行深度与测井值必须完整有限')
  if not math.isfinite(depth) or not 0<=depth<=10000 or not math.isfinite(value) or abs(value)>1e6:raise ValueError('深度[0,10000]米，读数有限且绝对值≤1e6')
  if hole in last and not math.isclose(depth-last[hole],1.,rel_tol=0,abs_tol=1e-9):raise ValueError('每孔深度须按输入严格递增且固定1米；重复/缺层/倒序拒绝，不跨缺口串链')
  reference=(raw.get('truth') or '').strip()
  if len(reference)>30:raise ValueError('模拟参考标签最多30字')
  last[hole]=depth;counts[hole]=counts.get(hole,0)+1;rows.append({'borehole':hole,'depth_m':depth,'value':value,'truth':reference or None})
  if len(rows)>MAX_ROWS or len(last)>MAX_HOLES or counts[hole]>1000:raise ValueError('最多5000行/8孔/每孔1000点')
 if not rows or any(n<3 for n in counts.values()):raise ValueError('每个完整孔段至少3点')
 return rows
