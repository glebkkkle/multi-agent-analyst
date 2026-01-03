# src/multi_agent_analyst/agents/analysis_agent.py

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import json

from src.multi_agent_analyst.tools.analysis_agent_tools import (
    make_correlation_tool,
    make_anomaly_tool,
    make_summary_tool,
    make_groupby_tool, 
    make_difference_tool, 
    make_filter_tool, 
    make_sort_tool, 
    make_distribution_tool
)
from pydantic import BaseModel
from src.multi_agent_analyst.prompts.react_agents.analysis_agent import ANALYST_AGENT_PROMPT
from src.multi_agent_analyst.schemas.analysis_agent_schema import ExternalAgentSchema
from src.multi_agent_analyst.utils.utils import context, object_store, load_and_validate_df, generate_data_preview, agent_error, agent_success
from src.multi_agent_analyst.utils.utils import execution_list, ExecutionLogEntry
from src.backend.llm.registry import get_default_llm
from src.multi_agent_analyst.logging import logger
from src.backend.storage.emitter import emit
llm=get_default_llm()

class AnalysisAgentArgs(BaseModel):
    analysis_query: str
    current_plan_step: str
    data_id: str

@tool(args_schema=AnalysisAgentArgs)
def analysis_agent(analysis_query: str, current_plan_step: str, data_id: str):
    """Analysis Agent performing correlation, anomaly detection, periodicity, etc."""
    logger.info(
        "AnalysisAgent started",
        extra={
            "agent": "AnalysisAgent",
            "step_id": current_plan_step,
        }
    )

    df, error = load_and_validate_df(data_id)
    data_overview=generate_data_preview(data_id)

    if error:
        return agent_error(error)

    correlation_tool = make_correlation_tool(df)
    anomaly_tool = make_anomaly_tool(df)
    summary_tool = make_summary_tool(df)
    groupby_tool=make_groupby_tool(df)
    difference_analysis=make_difference_tool(df)
    filter_rows_tool=make_filter_tool(df)
    sort_rows_tool=make_sort_tool(df)
    analyze_distribution_tool=make_distribution_tool(df)

    agent = create_agent(
        llm,
        tools=[correlation_tool, anomaly_tool, summary_tool, groupby_tool, difference_analysis, sort_rows_tool,analyze_distribution_tool,filter_rows_tool],
        system_prompt=ANALYST_AGENT_PROMPT.format(data_preview=data_overview),
        response_format=ExternalAgentSchema,
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": analysis_query}]})
    
    last_agent_message = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]

    if not tool_msgs:
        logger.warning(
            "AnalysisAgent finished without tool call",
            extra={
                "agent": "AnalysisAgent",
                "step_id": current_plan_step,
            }
        )
        return agent_error("Agent did not call any tools")
    
    last_tool_output = tool_msgs[-1].content
    try:
        tool_output=json.loads(last_tool_output)
    except Exception as e:
        logger.error(
            "DataAgent failed to parse tool output",
            extra={
                "agent": "DataAgent",
                "step_id": current_plan_step,
                "error": str(e),
            }
        )
            
        return agent_error("Failed to parse tool output")
    
    obj_id=tool_output.get("object_id")
    exception=tool_output.get("exception")
    operation_type=tool_output.get('operation_type', ' ')

    emit(f'Computing {operation_type}')
    try:
        msg=json.loads(last_agent_message)
    
    except Exception:
        return {"object_id":obj_id,
                "summary":tool_output.get("details", " "),
                "exception":exception
                }

    context.set("AnalysisAgent", current_plan_step,obj_id)

    log=ExecutionLogEntry(id=current_plan_step, 
                          agent='AnalysisAgent',
                            sub_query=analysis_query, 
                            status='success' if exception is None else exception, 
                            output_object_id=obj_id, 
                            error_message=exception if exception is not None else None)
    
    msg['object_id']=obj_id
    msg['exception']=exception
    if exception:
        logger.error(
            "AnalysisAgent tool execution failed",
            extra={
                "agent": "AnalysisAgent",
                "step_id": current_plan_step,
                "error": exception,
            }
        )
    else:
        logger.info(
            "AnalysisAgent completed successfully",
            extra={
                "agent": "AnalysisAgent",
                "step_id": current_plan_step,
                "object_id": obj_id,
            }
        )
    execution_list.execution_log_list.setdefault(current_plan_step, []).append(log)
    return msg
