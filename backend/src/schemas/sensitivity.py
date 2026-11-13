from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
class SensitivityInput(BaseModel):
    name:str=Field(min_length=2,max_length=140)
    run_id:int
class SensitivityOut(BaseModel):
    id:int
    name:str
    run_id:int
    ridge:float
    repeats:int
    seed:int
    status:str
    result:dict
    error:str
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)
