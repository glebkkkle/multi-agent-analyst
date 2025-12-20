from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal, Union, List

class SummarySchema(BaseModel):
    class Config:
        extra = "forbid"

class PeriodicSchema(BaseModel):
    frequency: int = Field(..., description="Seasonal cycle length (e.g., 7, 30).")

    class Config:
        extra = "forbid"

class AnomalySchema(BaseModel):
    class Config:
        extra = "forbid"

class CorrelationSchema(BaseModel):
    class Config:
        extra = "forbid"

class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    summary:str=Field(..., description='A short summary of steps peformed and final result')
    exception: Optional[str]=Field(..., description='placeholder for exception message')
    final_table_shape : Optional[Dict[Any, Any]]
    
class GroupBySchema(BaseModel):
    group_column: str
    agg_column: str
    agg_function: str  # "mean", "sum", "count", "min", "max"

class DifferenceSchema(BaseModel):
    column: str
    method: str = "absolute" 

class FilterSchema(BaseModel):
    column: str = Field(..., description="Column to filter on")

    operator: Literal[
        "==", "!=", ">", ">=", "<", "<=", "in", "not_in"
    ]

    value: Union[
        int,
        float,
        str,
        List[int],
        List[float],
        List[str],
    ] = Field(
        ...,
        description="Value to compare against. Use list only with 'in' or 'not_in'."
    )

class SortSchema(BaseModel):
    column: str
    order: Literal["asc", "desc"] = "desc"
    limit: int = 10


