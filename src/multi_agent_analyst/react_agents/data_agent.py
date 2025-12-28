# src/multi_agent_analyst/agents/data_agent.py
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.tools.data_agent_tools import (
    make_sql_query_tool,
    make_select_columns_tool,
    make_merge_tool,
    make_schema_list
)
import json
from src.multi_agent_analyst.prompts.react_agents.data_agent import DATA_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context, current_tables,ExecutionLogEntry, execution_list, object_store, create_log
from src.multi_agent_analyst.schemas.data_agent_schema import ExternalAgentSchema
from src.backend.llm.registry import  get_mini_llm
from src.multi_agent_analyst.logging import logger

from src.backend.storage.emitter import emit


mini=get_mini_llm()

@tool
def data_agent(data_agent_query: str, current_plan_step: str):
    """High-level DataAgent using SQL, selection, and merge tools."""

    logger.info(
        "DataAgent started",
        extra={
            "agent": "DataAgent",
            "step_id": current_plan_step,
        }
    )
    tools = [
        make_sql_query_tool(),
        make_select_columns_tool(),
        make_merge_tool(),
        make_schema_list(list(current_tables.values()))
    ]

    agent = create_agent(
        mini,
        tools=tools,
        system_prompt=DATA_AGENT_PROMPT.format(tables=list(current_tables.values())),
        response_format=ExternalAgentSchema,
    )
    emit("Data Agent retrives data.")
    result = agent.invoke({"messages": [{"role": "user", "content": data_agent_query}]})

    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]

    if not tool_msgs:
        create_log('DataAgent', 'Agent did not call any tools', 'error', current_plan_step, None, data_agent_query)
        logger.warning(
            "DataAgent finished without tool call",
            extra={
                "agent": "DataAgent",
                "step_id": current_plan_step,
            }
        )
        return {"object_id":None, "summary":'Agent did not call any tools', "exception":'No tool call'}
    
    last_tool_output = tool_msgs[-1].content

    try:
        tool_json=json.loads(last_tool_output)
    except Exception as e:
        logger.error(
            "DataAgent failed to parse tool output",
            extra={
                "agent": "DataAgent",
                "step_id": current_plan_step,
                "error": str(e),
            }
        )
        create_log('DataAgent', str(e), 'error', current_plan_step, None, data_agent_query)
        return {"object_id":None, "summary":'failed to parse tool output', "exception":'Failed Parsing'}

    object_id=tool_json.get("object_id")
    exception=tool_json.get("exception")

    try:
        msg=json.loads(last_msg)

    except Exception:
        return {"object_id":object_id, 
                "summary":tool_json.get("details", " "), 
                "exception":exception
                }

    log=ExecutionLogEntry(id=current_plan_step, 
                          agent='DataAgent', 
                          sub_query=data_agent_query, 
                          status='success' if exception is None else 'error', 
                          output_object_id=object_id, 
                          error_message=exception if exception is not None else None)

    msg['object_id']=object_id
    msg['exception']=exception

    context.set("DataAgent", current_plan_step, object_id)
    execution_list.execution_log_list.setdefault(current_plan_step, []).append(log)
    if exception:
        logger.error(
            "DataAgent tool execution failed",
            extra={
                "agent": "DataAgent",
                "step_id": current_plan_step,
                "error": exception,
            }
        )
    else:
        logger.info(
            "DataAgent completed successfully",
            extra={
                "agent": "DataAgent",
                "step_id": current_plan_step,
                "object_id": object_id,
            }
        )
    return msg
