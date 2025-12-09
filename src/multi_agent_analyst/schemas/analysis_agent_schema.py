from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

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

class ObservationState(BaseModel):
    agent:str
    tools_used:List[str]
    summary:str
    details:Dict[str, Any]

class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    observation:ObservationState=Field(..., description='An observation of performed actions')
    exception: Optional[str]=Field(..., description='placeholder for exception message')

