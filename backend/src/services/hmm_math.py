import math
NEG_INF=float('-inf')
def logsumexp(values):
 values=list(values);m=max(values)
 if m==NEG_INF:return NEG_INF
 return m+math.log(math.fsum(math.exp(x-m) for x in values))
def safelog(x):return math.log(x) if x>0 else NEG_INF
def validate(values,initial,transition,means,variances):
 k=len(means)
 if not 2<=k<=4 or len(variances)!=k or len(initial)!=k or len(transition)!=k or any(len(row)!=k for row in transition):raise ValueError('HMM需2—4个状态及一致概率维度')
 numeric=lambda x:isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
 if not values or len(values)>1000 or any(not numeric(v) or abs(v)>1e6 for v in values):raise ValueError('完整孔段需1—1000个有限测井值，绝对值≤1e6')
 if any(not numeric(x) or abs(x)>1e6 for x in means) or any(not numeric(x) or x<1e-8 or x>1e8 for x in variances):raise ValueError('均值需有限，方差在[1e-8,1e8]且为正')
 def rowcheck(row):
  if any(not numeric(p) or not 0<=p<=1 for p in row) or abs(math.fsum(row)-1)>1e-10:raise ValueError('初始/转移概率需有限非负，逐行和1；允许精确0')
  total=math.fsum(row);return [float(x/total) for x in row]
 pi=rowcheck(initial);A=[rowcheck(row) for row in transition]
 emissions=[[-.5*(math.log(2*math.pi)+math.log(var)+(value-mean)**2/var) for mean,var in zip(means,variances)] for value in values]
 return pi,A,emissions
def json_logs(rows):return [[None if x==NEG_INF else x for x in row] for row in rows]

def relative_emissions(emissions):
 offsets=[max(row) for row in emissions]
 return [[value-offset for value in row] for row,offset in zip(emissions,offsets)],offsets
