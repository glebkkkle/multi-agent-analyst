from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LinePlotSchema(BaseModel):
    pass

class ScatterPlotSchema(BaseModel):
    pass

class PieChartSchema(BaseModel):
    column_names:List[str]=Field(..., description='The names of the target columns for the pie chart')

class TableVisualizationSchema(BaseModel):
    pass

class BarPlotSchema(BaseModel):
    pass


class ObservationState(BaseModel):
    agent:str
    tools_used:List[str]
    summary:str
    details:Dict[str, Any]

class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    observation:ObservationState=Field(..., description='An observation of performed actions')
    exception: Optional[str]=Field(..., description='placeholder for exception message')

