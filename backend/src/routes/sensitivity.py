from fastapi import APIRouter,Depends
from src.config.database import get_db
from src.utils.auth import current_user,editor
from src.schemas.sensitivity import SensitivityInput,SensitivityOut
from src.controllers import sensitivity_controller as controller
router=APIRouter(prefix='/sensitivity',tags=['sensitivity'])
@router.get('',response_model=list[SensitivityOut])
def index(db=Depends(get_db),user=Depends(current_user)):return controller.index(db)
@router.post('',response_model=SensitivityOut,status_code=201)
def create(data:SensitivityInput,db=Depends(get_db),user=Depends(editor)):return controller.create(db,data)
@router.get('/{id}',response_model=SensitivityOut)
def detail(id:int,db=Depends(get_db),user=Depends(current_user)):return controller.detail(db,id)
