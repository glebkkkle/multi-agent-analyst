import io
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import numpy as np
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.visualization_agent_schema import (
    PieChartSchema,
    TableVisualizationSchema,
    BarPlotSchema, 
    ScatterPlotSchema, 
    LinePlotSchema
)
from typing import List


from src.multi_agent_analyst.utils.utils import object_store


def make_scatter_plot_tool(df):
    def scatter_plot(x_axis: str , y_axis: str):
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            x_col = x_axis if x_axis in df.columns else (numeric_cols[0] if numeric_cols else None)
            y_col = y_axis if y_axis in df.columns else (numeric_cols[1] if len(numeric_cols) > 1 else None)

            if not x_col or not y_col:
                raise ValueError("Insufficient numeric data for scatter plot.")

            vis_json = {
                "type": "visualization",
                "plot_type": "scatter",
                "x": df[x_col].tolist(),
                "y": df[y_col].tolist(),
                "labels": {"x": x_col, "y": y_col},
            }
            obj_id = object_store.save(vis_json)
            return {"object_id": obj_id, "status": "success", "type": "visualization"}
        
        except Exception as e:
            return {'object_id':None, 
                    'details':'Failed',
                    'plot_type':'scatter plot',
                    'x':x_col,
                    'y':y_col,
                    'exception':str(e)               
                }
        
    return StructuredTool.from_function(
        func=scatter_plot,
        name="scatter_plot",
        description="Creates a scatter plot. Agent must specify x_axis and y_axis from available columns.",
        args_schema=ScatterPlotSchema
    )


def make_line_plot_tool(df):
    def line_plot(x_axis: str , y_axis: str ):
        try:
            if not x_axis:
                for col in df.columns:
                    if "date" in col.lower() or "time" in col.lower():
                        x_axis = col
                        break
            
            y_col = y_axis if y_axis in df.columns else df.select_dtypes(include=['number']).columns[0]

            temp_df = df.sort_values(by=x_axis) if x_axis in df.columns else df

            vis_json = {
                "type": "visualization",
                "plot_type": "line_plot",
                "x": temp_df[x_axis].tolist() if x_axis in temp_df.columns else list(range(len(temp_df))),
                "y": temp_df[y_col].astype(float).tolist(),
                "labels": {"x": x_axis or "Index", "y": y_col},
            }
        
            obj_id = object_store.save(vis_json)
            return {"object_id": obj_id, "status": "success"}
        
        except Exception as e:
            return {'object_id':None, 
                    'details':'Failed',
                    'plot_type':'line plot',
                    'exception':str(e)               
                }

    return StructuredTool.from_function(
        func=line_plot,
        name="line_plot",
        description="Creates a line plot. Best for trends. Specify a date/time column for x_axis.",
        args_schema=LinePlotSchema
    )

def make_pie_chart_tool(df):
    def pie_chart(column_names: List[str]):
        try:
            missing = [c for c in column_names if c not in df.columns]
            if missing:
                raise ValueError(f"Columns not found in dataframe: {', '.join(missing)}")

            subset = df[column_names].select_dtypes(include=['number'])
            values = subset.sum().astype(float).tolist()
            labels = subset.columns.tolist()

            if not values:
                raise ValueError("None of the selected columns contain numeric data.")

            vis_json = {
                "type": "visualization",
                "plot_type": "pie_chart",
                "labels": labels,
                "values": values,
            }

            obj_id = object_store.save(vis_json)
            
            return {
                "object_id": obj_id, 
                "status": "success",
                "details": f"Generated pie chart for: {', '.join(labels)}"
            }

        except Exception as e:
            return{
                 'object_id':None, 
                    'details':'Failed',
                    'plot_type':'pie chart',
                    'columns':labels,
                    'exception':str(e)               
                }

    return StructuredTool.from_function(
        func=pie_chart,
        name="pie_chart",
        description="Creates a pie chart comparing different numeric columns. Pass a list of column names.",
        args_schema=PieChartSchema
    )


def make_bar_chart_tool(df):
    """Beautiful bar chart with gradients and modern styling."""

    def bar_chart():
        try:
            # Get first categorical and first numeric column
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            num_cols = df.select_dtypes(include=['float', 'int']).columns
            

            if len(cat_cols) == 0 or len(num_cols) == 0:
                raise ValueError("Need at least one categorical and one numeric column")
            
            cat_col = cat_cols[0]
            num_col = num_cols[0]

            vis_json = {
                "type": "visualization",
                "plot_type": "bar",
                "x": num_col,
                'y':cat_col,
                "title": "BAR PLOT"
            }

        except Exception as e:
            return {'exception': e}
        

    
    return StructuredTool.from_function(
        func=bar_chart,
        name="bar_chart",
        description="Beautiful bar chart with gradient colors.",
        args_schema=TableVisualizationSchema,
    )


def make_table_visualization_tool(df):
    """Factory: returns a table visualization tool bound to the given dataframe."""

    def table_visualization():
        return object_store.save(df)

    return StructuredTool.from_function(
        func=table_visualization,
        name="table_visualization",
        description="Stores the DataFrame as an object and returns its ID.",
        args_schema=BarPlotSchema,
    )


__all__ = [
    "make_line_plot_tool",
    "make_scatter_plot_tool",
    "make_pie_chart_tool",
    "make_bar_chart_tool",
    "make_table_visualization_tool",
]