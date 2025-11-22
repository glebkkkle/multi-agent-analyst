from pydantic import BaseModel, Field
from typing import List

class LinePlotSchema(BaseModel):
    pass

class ScatterPlotSchema(BaseModel):
    pass

class PieChartSchema(BaseModel):
    column_names:List[str]=Field(..., description='The names of the target columns for the pie chart')

class TableVisualizationSchema(BaseModel):
    pass


class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    summary:str=Field(..., description='A short summary of steps peformed and final result')
