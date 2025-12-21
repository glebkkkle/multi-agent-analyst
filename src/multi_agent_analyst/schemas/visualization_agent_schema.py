from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class LinePlotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x_axis: str= Field(..., description="The column name for the X axis")
    y_axis: str = Field(..., description="The column name for the Y axis")


class ScatterPlotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x_axis: str = Field(..., description="The column name for the X axis")
    y_axis: str = Field(..., description="The column name for the Y axis")


class PieChartSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column_names: List[str] = Field(..., description="The names of the target columns for the pie chart")

class TableVisualizationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

class BarPlotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ExternalAgentSchema(BaseModel):
    object_id: str = Field(..., description="Final object ID after all modifications")
    summary: str = Field(..., description="Short summary of steps performed and final result")
    exception: Optional[str] = Field(None, description="Exception message if any")