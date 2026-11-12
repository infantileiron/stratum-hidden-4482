from src.models.entities import BoreholeDataset
from src.services.observations import parse_observations
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_datasets():
 return [{k:v for k,v in d.items() if k!='rows'}|{'row_count':len(d['rows']),'boreholes':sorted(set(r['borehole'] for r in d['rows']))} for d in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def create(data):return repo.put('datasets',BoreholeDataset(new_id('ds'),data.name,data.source,parse_observations(data.csv_text),now()))
def rename(id,data):
 d=repo.get('datasets',id);d['name']=data.name;return repo.put('datasets',d)
