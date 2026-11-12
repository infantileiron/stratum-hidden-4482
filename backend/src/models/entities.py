from dataclasses import dataclass,field
from typing import Any
@dataclass
class BoreholeDataset:
 id:str
 name:str
 source:str
 rows:list[dict]
 created_at:str=''
@dataclass
class StateModel:
 id:str
 name:str
 config:dict
 revision:int=1
 created_at:str=''
@dataclass
class SequenceStudy:
 id:str
 name:str
 dataset_id:str
 model_id:str
 borehole:str
 snapshot:dict
 checksum:str
 created_at:str=''
@dataclass
class DecodeRun:
 id:str
 study_id:str
 status:str='queued'
 result:dict[str,Any]=field(default_factory=dict)
 error:str=''
 created_at:str=''
@dataclass
class LayerReview:
 id:str
 run_id:str
 comment:str
 status:str='pending'
 reviewer:str=''
 created_at:str=''
@dataclass
class Report:
 id:str
 run_id:str
 review_id:str
 title:str
 created_at:str=''
