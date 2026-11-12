from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class InputModel(BaseModel):
 model_config=ConfigDict(allow_inf_nan=False)
class LoginInput(InputModel):
 email:str
 password:str
class DatasetInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 source:str=Field(default='shenxi_logs_202611.csv',max_length=100)
 csv_text:str=Field(min_length=10,max_length=400000)
class RenameDataset(InputModel):
 name:str=Field(min_length=2,max_length=100)
class StateModelInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 model_json:str=Field(min_length=2,max_length=15000)
class DepthConstraintInput(InputModel):
 depth_m:float=Field(ge=0,le=10000)
 allowed_state_ids:list[str]=Field(min_length=1,max_length=4)
class SequenceStudyInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 model_id:str
 borehole:str=Field(min_length=1,max_length=30)
 depth_constraints:list[DepthConstraintInput]=Field(default_factory=list,max_length=1000)
 constraint_source_run_id:str=Field(default='',max_length=60)
class RunInput(InputModel):
 study_id:str
class ReviewInput(InputModel):
 run_id:str
 comment:str=Field(min_length=5,max_length=2000)
class DecisionInput(InputModel):
 status:Literal['approved','rejected']
 comment:str=Field(min_length=5,max_length=2000)
class ReportInput(InputModel):
 run_id:str
 review_id:str
 title:str=Field(min_length=2,max_length=100)
