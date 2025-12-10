import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ObjectStore:
    def __init__(self):
        self.store = {}
    
    def save(self, obj):
        obj_id = f"obj_{uuid.uuid4().hex[:8]}"
        self.store[obj_id] = obj
        #could potentially save the results of all intermediate steps inside a STEP (S1, ...)
        return obj_id

    def get(self, obj_id):
        return self.store[obj_id]


object_store = ObjectStore()

class CurrentToolContext:
    def __init__(self):
        self.dict={'DataAgent':{}, 'AnalysisAgent':{}, 'VisualizationAgent':{}}

    def set(self,agent, step, data):
        self.dict[agent][step]=data
    
    def get(self,agent, step_id):
        return self.dict[agent][step_id]
    
class ExecutionLogEntry(BaseModel):
    id: str
    agent: str
    sub_query: str
    status: Optional[str]=None  # "success" | "error"
    output_object_id: Optional[str] = None
    error_message: Optional[str] = None

class ExecutionLogList(BaseModel):
    execution_log_list:Dict[str, Any]={}

execution_list=ExecutionLogList()

context=CurrentToolContext()

current_tables={}

viz_json={}