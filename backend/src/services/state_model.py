from src.models.entities import StateModel
from src.services.model_config import parse_model
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_models():return repo.all_rows('state_models')
def create(data):return repo.put('state_models',StateModel(new_id('model'),data.name,parse_model(data.model_json),1,now()))
def update(id,data):
 item=repo.get('state_models',id);item.update(name=data.name,config=parse_model(data.model_json),revision=item['revision']+1);return repo.put('state_models',item)
