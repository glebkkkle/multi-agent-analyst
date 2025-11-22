from langchain_ollama import ChatOllama
import pandas as pd
import numpy as np
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from src.multi_agent_analyst.agents.agents_prompts import (
    DATA_AGENT_PROMPT,
    CONTROLLER_AGENT_PROMPT,
    ANALYST_AGENT_PROMPT,
    VISUALIZATION_AGENT_PROMPT,
)
from src.multi_agent_analyst.agents.execution_agent_schemas  import CorrelationSchema, AnomalySchema, PeriodicSchema, SummarySchema, LinePlotSchema, ScatterPlotSchema,PieChartSchema, TableVisualizationSchema
from src.multi_agent_analyst.graph.states import ExternalAgentSchema
from langchain_core.messages import AIMessage
import matplotlib.pyplot as plt
import io
from src.multi_agent_analyst.db.connection import get_conn
from langchain_core.tools import StructuredTool
from statsmodels.tsa.seasonal import STL
from src.multi_agent_analyst.utils.utils import context, object_store

openai_llm=ChatOpenAI(model='gpt-4.1-mini')
tool_llm=ChatOllama(model='gpt-oss:20b', temperature=0, reasoning=True) 


@tool
def get_data(agent_name:str, step_id:str):
    'A tool that retrives the data from the previous step.'
    'Args:agent_name (e.g DataAnalyst, VisualizationAgent), step_id (e.g S1, S5 ...)'
    return context.get(agent_name, step_id) 


@tool
def data_agent(data_agent_query:str, current_plan_step:str):
    'An Intelligent DataAgent that handles data queriyng, data segmentation and data formatting.'
    'Args: data_agent_query, current_plan_step'
    print('DATA AGENT IS HIT')
    obj_id=None #Final object after all modifications

    @tool
    def sql_query(query:str):
        'A tool that queries the relevant SQL table'
        'Args:query'
        nonlocal obj_id
        query_result=pd.read_sql_query(query, conn)
        obj_id = object_store.save(query_result)
        print(obj_id)
        return obj_id
    
    @tool
    def select_columns(columns, table_id):
        'A tool that selects given columns from the relevant table'
        'Args:columns:List, table_id:id'
        nonlocal obj_id
        print(table_id)
        print(object_store.store)
        table=object_store.get(table_id)

        result=table[columns]
        obj_id=object_store.save(result)

        return obj_id
    

    @tool
    def merge(table1, table2):
        'A tool that merges (joins) two distinct tables together, resulting into a joint table.'
        'Args:table1, table2'

        return 


    agent=create_agent(tool_llm, tools=[sql_query, select_columns, merge], system_prompt=DATA_AGENT_PROMPT, response_format=ExternalAgentSchema)

    result = agent.invoke({
        "messages": [{"role": "user", "content": data_agent_query}]
    })


    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    last_ai_msg = ai_messages[-1].content
    context.set('DataAgent', current_plan_step, obj_id)

    print(last_ai_msg)
    return last_ai_msg

@tool
def analysis_agent(analysis_agent_query:str, current_plan_step:str, data_id:str):
    'An Intelligent AnalysisAgent that performs statistical tools on **given** data (specified id in data_id argument)'
    'Args:analysis_agent_query, current_plan_step, data_id'
    obj_id=None
    current_data=object_store.get(data_id)
    print('hit analysis agent')
    print(current_data)
    print(analysis_agent_query)


    def correlation_analysis(current_data=current_data):
        result = current_data.corr(numeric_only=True)
        return object_store.save(result)

    def anomaly_detection(current_data=current_data):
        df = current_data.select_dtypes([int, float])

        print(df)

        q1 = df.quantile(0.25)
        q3 = df.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = df[(df < lower) | (df > upper)]

        return object_store.save(outliers)

    def periodic_analysis(frequency: int, current_data=current_data):
        current_data['date'] = pd.to_datetime(current_data['date'])
        current_data = current_data.sort_values('date')

        series = current_data.values
        series = series - np.mean(series)

        stl = STL(series, period=frequency, robust=True).fit()
        decomposition = {
            "trend": stl.trend.tolist(),
            "seasonal": stl.seasonal.tolist(),
            "residual": stl.resid.tolist()
        }

        # autocorrelation
        acf_vals = []
        n = len(series)
        var = np.var(series)

        for lag in range(0, min(20, n - 1)):
            if lag == 0:
                acf_vals.append(1.0)
                continue
            cov = np.sum(series[:-lag] * series[lag:]) / (n - lag)
            acf_vals.append(float(cov / var))

        fft_vals = np.fft.fft(series)
        freqs = np.fft.fftfreq(len(series))

        mask = freqs > 0
        positive_freqs = freqs[mask]
        positive_power = np.abs(fft_vals)[mask]

        dominant_freq = float(positive_freqs[np.argmax(positive_power)])

        result = {
            "decomposition": decomposition,
            "autocorrelation": acf_vals,
            "dominant_frequency": dominant_freq,
            "interpretation":
                f"Dominant cycle occurs every {round(1/dominant_freq, 2)} steps."
                if dominant_freq > 0 else "No clear periodicity detected."
        }

        return object_store.save(result)


    def summary_statistics(current_data=current_data):
        stats = current_data.describe(include='all').to_dict()
        return object_store.save(stats)

    correlation_tool = StructuredTool.from_function(
        func=correlation_analysis,
        name="correlation_analysis",
        description="Computes correlation matrix for numeric columns.",
        schema=CorrelationSchema,
    )

    anomaly_tool = StructuredTool.from_function(
        func=anomaly_detection,
        name="anomaly_detection",
        description="Detects outliers using the IQR rule.",
        schema=AnomalySchema,
    )

    periodic_tool = StructuredTool.from_function(
        func=periodic_analysis,
        name="periodic_analysis",
        description="Performs STL decomposition and dominant frequency analysis.",
        schema=PeriodicSchema,
    )

    summary_tool = StructuredTool.from_function(
        func=summary_statistics,
        name="summary_statistics",
        description="Computes simple summary statistics for a dataset.",
        schema=SummarySchema,
    )


    analysis_agent=create_agent(model=openai_llm, tools=[correlation_tool, anomaly_tool, periodic_tool, summary_tool], system_prompt=ANALYST_AGENT_PROMPT, response_format=ExternalAgentSchema)
    result= analysis_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"{analysis_agent_query}"
            }
        ]
    })

    context.set('AnalysisAgent', current_plan_step, obj_id)
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    last_ai_msg = ai_messages[-1].content
    print(last_ai_msg)

    return last_ai_msg


@tool
def visualization_agent(visualizer_agent_query:str, current_plan_step:str, data_id:str):
    'An intelligent Visualization agent, that transforms numerical findings into Visual Interpretations'
    'Args:visualizer_agent_query, current_plan_step, data_id'
    obj_id=None
    current_data=object_store.get(data_id)
    
    def line_plot(x:str,y:str):
        'A tool that visualizes data with a line_plot'
        'Args: x :(usually time-period), y:(target_column)'
        nonlocal current_data, obj_id

        print('Line plot was hit')

        x_plot, y_plot=current_data[x], current_data[y]

        plt.figure(figsize=(10, 5))
        plt.plot(x_plot, y_plot, marker="o", linewidth=2)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.grid(True)
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close()

        obj_id = object_store.save(buf)        
        return obj_id

    def scatter_plot(column1:str, column2:str):
        'A tool that performs a scatter plot for two columns'
        'Args:column1, column2'
        nonlocal obj_id, current_data

        x,y=current_data[column1], current_data[column2]

        plt.figure(figsize=(10, 5))
        plt.scatter(x, y)
        plt.xlabel(column1)
        plt.ylabel(column2)
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close()

        obj_id=object_store.save(buf)
        return obj_id

    def pie_chart(columns:list):
        'A tool that creates pie-chart on the given columns'
        'Args:columns'
        labels=columns
        sizes=current_data[columns]

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close()

        obj_id=object_store.save(buf)
        print(obj_id)
        return obj_id 

    def table_visualization():
        'A tool that visualizes table'
        'Args:None'
        return current_data


    line_plot_tool = StructuredTool.from_function(
        func=line_plot,
        name="line_plot",
        description="Creates a line plot.",
        args_schema=LinePlotSchema,
    )

    scatter_plot_tool = StructuredTool.from_function(
        func=scatter_plot,
        name="scatter_plot",
        description="Creates a scatter plot.",
        args_schema=ScatterPlotSchema,
    )

    pie_chart_tool = StructuredTool.from_function(
        func=pie_chart,
        name="pie_chart",
        description="Creates a pie chart.",
        args_schema=PieChartSchema,
    )

    table_visualization_tool = StructuredTool.from_function(
        func=table_visualization,
        name="table_visualization",
        description="Displays the table.",
        args_schema=TableVisualizationSchema,
    )
    viz_agent=create_agent(model=tool_llm, tools=[line_plot_tool, table_visualization_tool, pie_chart_tool, scatter_plot_tool], system_prompt=VISUALIZATION_AGENT_PROMPT, response_format=ExternalAgentSchema)

    result=viz_agent.invoke({'messages':[{'role':'user', 'content':visualizer_agent_query}]})
    print(result)
    context.set('VisualizationAgent', current_plan_step, obj_id)
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    last_ai_msg = ai_messages[-1].content

    return last_ai_msg


controller_agent=create_agent(model=openai_llm, tools=[data_agent, analysis_agent, visualization_agent], system_prompt=CONTROLLER_AGENT_PROMPT, response_format=ExternalAgentSchema)

