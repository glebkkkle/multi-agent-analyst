from pydantic import BaseModel, Field
from typing import List

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


class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    summary:str=Field(..., description='A short summary of steps peformed and final result')
