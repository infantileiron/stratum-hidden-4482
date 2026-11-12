from src.services import state_model as service
def list_items():return service.list_models()
def create(data):return service.create(data)
