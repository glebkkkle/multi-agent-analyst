from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

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

