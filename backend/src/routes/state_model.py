from fastapi import APIRouter,Depends
from src.controllers import state_model as controller
from src.schemas.entities import StateModelInput
from src.services.auth import current,editor
router=APIRouter(prefix='/models',tags=['models'])
@router.get('')
def list_items(user=Depends(current)):return controller.list_items()
@router.post('',status_code=201)
def create(data:StateModelInput,user=Depends(editor)):return controller.create(data)

@router.patch('/{id}')
def update(id:str,data:StateModelInput,user=Depends(editor)):
 from src.services.state_model import update
 return update(id,data)
