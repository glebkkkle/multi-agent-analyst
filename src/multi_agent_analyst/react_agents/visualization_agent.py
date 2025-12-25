# src/multi_agent_analyst/agents/visualization_agent.py

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langchain_ollama import ChatOllama
import json
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.prompts.react_agents.visualization_agent import VISUALIZATION_AGENT_PROMPT
from src.multi_agent_analyst.schemas.visualization_agent_schema import ExternalAgentSchema
from src.multi_agent_analyst.tools.visualization_agent_tools import (
    make_line_plot_tool,
    make_scatter_plot_tool,
    make_pie_chart_tool,
    make_table_visualization_tool,
    make_bar_chart_tool, 
    make_histogram_tool
)
from src.multi_agent_analyst.utils.utils import context, object_store, execution_list, ExecutionLogEntry, generate_data_preview, load_and_validate_df
from src.backend.llm.registry import  get_mini_llm
from src.multi_agent_analyst.logging import logger
from src.backend.storage.emitter import emit
from src.backend.storage.execution_store import execution_store

mini=get_mini_llm()

@tool(description="Visualization agent returning images/tables based on query.")
def visualization_agent(visualizer_query: str, current_plan_step: str, data_id: str):
    logger.info(
        "VisualizationAgent started",
        extra={
            "agent": "VisualizationAgent",
            "step_id": current_plan_step,
        }
    )
    try:
        df = object_store.get(data_id)
        if len(df) < 2:
            raise ValueError("Visualization Agent requires at least two columns")
    except Exception as e:
        return {"status":"error",
                "object_id":None,
                "exception":str(e)
                }

    data_overview=generate_data_preview(data_id)
    df, error = load_and_validate_df(data_id)

    if error:
        return {"status":"error", "object_id":None, "exception":error}

    tools = [
        make_line_plot_tool(df),
        make_scatter_plot_tool(df),
        make_pie_chart_tool(df),
        make_table_visualization_tool(df),
        make_bar_chart_tool(df), 
        make_histogram_tool(df)
    ]

    agent = create_agent(
        mini,
        tools=tools,
        system_prompt=VISUALIZATION_AGENT_PROMPT.format(data_overview=data_overview),
        response_format=ExternalAgentSchema,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": visualizer_query}]})

    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]

    if not tool_msgs:
        logger.warning(
            "VisualizationAgent finished without tool call",
            extra={
                "agent": "VisualizationAgent",
                "step_id": current_plan_step,
            }
        )
        return {"object_id":None, "summary":'Agent did not call any tools', "exception":'No tool call'}
    
    last_tool_output = tool_msgs[-1].content
    try:
        tool_json=json.loads(last_tool_output)
    except Exception as e:
        logger.error(
            "VisualizationAgent failed to parse tool output",
            extra={
                "agent": "VisualizationAgent",
                "step_id": current_plan_step,
                "error": str(e),
            }
        )
        return {"object_id":None, "summary":'Failed to parse tool output', "exception":'Failed parsing.'}

    object_id=tool_json.get("object_id")
    exception=tool_json.get("exception")

    try:
        msg=json.loads(last_msg)
        
    except Exception:
        return {"object_id":object_id, 
                "summary":tool_json.get("details", " "), 
                "exception":exception
                }
    

    context.set("VisualizationAgent", current_plan_step, object_id)
    log=ExecutionLogEntry(id=current_plan_step, 
                          agent='VisualizationAgent', 
                          sub_query=visualizer_query, 
                          status='success' if exception is None else 'error', 
                          output_object_id=object_id, 
                          error_message=exception)

    msg['object_id']=object_id
    msg['exception']=exception
    execution_list.execution_log_list.setdefault(current_plan_step, []).append(log)

    if exception:
        logger.error(
            "VisualizationAgent tool execution failed",
            extra={
                "agent": "VisualizationAgent",
                "step_id": current_plan_step,
                "error": exception,
            }
        )
    else:
        logger.info(
            "VisualizationAgent completed successfully",
            extra={
                "agent": "VisualizationAgent",
                "step_id": current_plan_step,
                "object_id": object_id,
            }
        )    
    return msg
