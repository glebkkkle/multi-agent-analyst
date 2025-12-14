import io
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import numpy as np
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.visualization_agent_schema import (
    PieChartSchema,
    TableVisualizationSchema,
    BarPlotSchema
)
from src.multi_agent_analyst.utils.utils import object_store, viz_json


def make_scatter_plot_tool(df):
    """Beautiful scatter plot with gradient colors and styling."""

    def scatter_plot():
        try:
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns

            if len(numeric_cols) < 2:
                return {'object_id':None, 
                        'details':'Failed',
                        'plot_type':'scatter plot',
                        'exception': str(ValueError('Not enough nummerical column provided for the scatter plot.'))        
                    }

            x_col, y_col = numeric_cols[:2]

            # Create figur
            
            vis_json = {
                "type": "visualization",
                "plot_type": "scatter",
                "x": df[x_col].tolist(),
                "y": df[y_col].tolist(),
                "labels": {"x": x_col, "y": y_col},
                "title": f"{y_col} vs {x_col}"
            }
            

            obj_id=object_store.save(vis_json)
            return{
                'object_id':obj_id, 
                'details':{
                    'plot_type':'scatter plot',
                    'x':x_col,
                    'y':y_col
                }
            }
        
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
        description="Beautiful scatter plot with gradient colors based on numeric columns.",
        args_schema=TableVisualizationSchema,
    )


def make_line_plot_tool(df):
    """Elegant line plot with smooth curves and beautiful styling."""

    def line_plot():
        try:
            # Find date column
            date_col = None
            for col in df.columns:
                if "date" in col.lower():
                    date_col = col
                    break

            if date_col is None:
                print(' ')
                print('❌CURRENT EXCEPTION:')
                print("Line plot requires a date column.")
                raise ValueError("Line plot requires a date column.")

            # Choose first numeric column
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric column to plot.")

            y_col = numeric_cols[0]

            x_data = range(len(df))
            y_data = df[y_col].values
            


            x_data = list(range(len(df)))          
            y_data = df[y_col].astype(float).tolist()  
            vis_json = {
                "type": "visualization",
                "plot_type": "line_plot",
                "x": x_data,
                "y": y_data,
                "labels": {"x": date_col, "y": y_col},
                "title": ' '
            }

        except Exception as e:
            return {'object_id':None, 
                    'details':'Failed',
                    'plot_type':'line plot',
                    'exception':str(e)               
                }
        obj_id=object_store.save(vis_json)
        return{
                'object_id':obj_id, 
                'details':{
                    'plot_type':'line_plot',
                    'x':date_col,
                    'y':y_col
                }
            }

    return StructuredTool.from_function(
        func=line_plot,
        name="line_plot",
        description="Elegant line plot with smooth curves and gradient fill.",
        args_schema=TableVisualizationSchema,
    )

#fix pie chart
#tighten the prompting to the react, so that always return object ids!!!!
#fix the simple chatting node 


def make_pie_chart_tool(df):
    """Modern pie chart with beautiful gradients and styling, no params needed."""

    def pie_chart():
        try:
            # Ensure dataframe has data
            if df.empty:
                raise ValueError("Dataframe is empty, cannot create pie chart.")

            num_df=df.select_dtypes(include=['float', 'int'])

            # Column names are the labels
            labels = num_df.columns.tolist()

            # First row values are used for the pie chart
            values = num_df.iloc[0].tolist()

            vis_json = {
                "type": "visualization",
                "plot_type": "pie_chart",
                "labels": labels,
                'values':values,
                "title": " "
            }

        except Exception as e:
            return{
                 'object_id':None, 
                    'details':'Failed',
                    'plot_type':'pie chart',
                    'columns':labels,
                    'exception':str(e)               
                }

        obj_id=object_store.save(vis_json)
        
        return {
                'object_id':obj_id, 
                'details':{
                    'plot_type':'pie_chat',
                    'columns':labels,
                }
            }

    # Tool wrapper
    return StructuredTool.from_function(
        func=pie_chart,
        name="pie_chart",
        description="Generate a modern pie chart using all dataframe columns.",
        args_schema=None   # IMPORTANT: no args
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