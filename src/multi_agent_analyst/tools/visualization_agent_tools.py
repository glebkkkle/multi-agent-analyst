import io
import matplotlib.pyplot as plt
from langchain_core.tools import StructuredTool

from src.multi_agent_analyst.schemas.visualization_agent_schema import (
    LinePlotSchema,
    ScatterPlotSchema,
    PieChartSchema,
    TableVisualizationSchema,
)

from src.multi_agent_analyst.utils.utils import object_store


def make_scatter_plot_tool(df):
    """Scatter plot using the first two numeric columns of the dataframe."""

    def scatter_plot():
        numeric_cols = df.select_dtypes(include=['float', 'int']).columns

        if len(numeric_cols) < 2:
            raise ValueError("Not enough numeric columns for scatter plot.")

        x_col, y_col = numeric_cols[:2]

        plt.figure(figsize=(10, 5))
        plt.scatter(df[x_col], df[y_col])
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return object_store.save(buf)

    return StructuredTool.from_function(
        func=scatter_plot,
        name="scatter_plot",
        description="Scatter plot based on the first two numeric columns of the dataframe.",
        args_schema=TableVisualizationSchema,
    )


def make_line_plot_tool(df):
    def line_plot():
        # Find date column
        date_col = None
        for col in df.columns:
            if "date" in col.lower():
                date_col = col
                break

        if date_col is None:
            raise ValueError("Line plot requires a date column.")

        # choose first numeric column
        numeric_cols = df.select_dtypes(include=['float', 'int']).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric column to plot.")

        y_col = numeric_cols[0]

        plt.figure(figsize=(10, 5))
        plt.plot(df[date_col], df[y_col], marker="o")
        plt.xlabel(date_col)
        plt.ylabel(y_col)
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return object_store.save(buf)

    return StructuredTool.from_function(
        func=line_plot,
        name="line_plot",
        description="Line plot using date + first numeric column.",
        args_schema=TableVisualizationSchema,
    )


def make_pie_chart_tool(df):
    """Factory: returns a pie chart tool bound to the given dataframe."""

    def pie_chart(column_names: list):
        values = df.iloc[0].tolist() if len(df) > 0 else []
        

        plt.figure(figsize=(6, 6))
        plt.pie(values, labels=column_names)
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close()

        return object_store.save(buf)

    return StructuredTool.from_function(
        func=pie_chart,
        name="pie_chart",
        description="Creates a pie chart from specified columns.",
        args_schema=PieChartSchema,
    )


def make_table_visualization_tool(df):
    """Factory: returns a table visualization tool bound to the given dataframe."""

    def table_visualization():
        return object_store.save(df)

    return StructuredTool.from_function(
        func=table_visualization,
        name="table_visualization",
        description="Stores the DataFrame as an object and returns its ID.",
        args_schema=TableVisualizationSchema,
    )

__all__ = [
    "make_line_plot_tool",
    "make_scatter_plot_tool",
    "make_pie_chart_tool",
    "make_table_visualization_tool",
]