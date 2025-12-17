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
    execution_log_list: Dict[str, list[Any]] = {}

execution_list=ExecutionLogList()

context=CurrentToolContext()

current_tables={}

viz_json={}

def load_and_validate_df(data_id):
    try:
        df = object_store.get(data_id)
    except Exception as e:
        return None, f"DATA_ACCESS_ERROR: {e}"

    if df is None:
        return None, f"DATA_NOT_FOUND: object '{data_id}' does not exist"

    if len(df) == 0:
        return None, f"DATA_EMPTY: object '{data_id}' is empty"

    return df, None

def create_log(agent, exception, status, id,output_object_id, sub_query):
    log=ExecutionLogEntry(id=id, agent=agent, sub_query=sub_query, status=status, output_object_id=output_object_id, error_message=exception)
    execution_list.execution_log_list.setdefault(id, []).append(log)
    return log
