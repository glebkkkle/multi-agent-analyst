from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SQLQuerySchema(BaseModel):
    query: str = Field(..., description="SQL query string.")

class SelectColumnsSchema(BaseModel):
    table_id: str = Field(..., description="Object ID of the table.")
    columns: List[str] = Field(..., description="Columns to select.")

class MergeTablesSchema(BaseModel):
    left_id: str = Field(..., description="Left table object ID.")
    right_id: str = Field(..., description="Right table object ID.")
    on: str = Field(..., description="Join key.")
    how: str = Field("inner", description="Join type.")

class ObservationState(BaseModel):
    agent:str
    tools_used:List[str]
    summary:str
    details:Dict[str, Any]

class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    observation:ObservationState=Field(..., description='An observation of performed actions')
    exception: Optional[str]=Field(..., description='placeholder for exception message')

