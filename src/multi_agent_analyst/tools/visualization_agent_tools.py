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

plt.rcParams.update({
    "figure.facecolor": "#050508",
    "axes.facecolor": "#0c0c11",
    "savefig.facecolor": "#050508",
    "axes.edgecolor": "#6366f1",
    "text.color": "#e5e7eb",
    "axes.labelcolor": "#e5e7eb",
    "xtick.color": "#d1d5db",
    "ytick.color": "#d1d5db",
    "font.family": "Inter",
    "axes.titleweight": "bold",
    "axes.titlecolor": "#ffffff",
})

COLORS = {
    'background': '#060b16',       # deep navy
    'panel':      '#0d1526',       # slightly lighter navy
    'primary':    '#3b82f6',       # blue-500
    'accent':     '#60a5fa',       # blue-400
    'grid':       '#1e293b',       # slate-800
    'text':       '#e2e8f0',       # slate-200
}


def setup_plot_style(fig, ax):
    # FIGURE BACKGROUND
    fig.patch.set_facecolor(COLORS['background'])
    ax.set_facecolor(COLORS['panel'])

    # GRID
    ax.grid(
        True,
        linestyle='--',
        linewidth=0.7,
        color=COLORS['grid'],
        alpha=0.25
    )

    # SPINES
    for spine in ax.spines.values():
        spine.set_color(COLORS['grid'])
        spine.set_linewidth(1.2)

    # TICKS
    ax.tick_params(
        colors=COLORS['text'],
        labelsize=10,
        length=6,
        width=1
    )

    # LABEL COLORS
    ax.xaxis.label.set_color(COLORS['text'])
    ax.yaxis.label.set_color(COLORS['text'])

    # TITLE
    ax.title.set_color(COLORS['text'])
    ax.title.set_weight('bold')

    # ENSURE EXPORT BG MATCHES
    plt.rcParams['savefig.facecolor'] = COLORS['background']


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