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

mini=get_mini_llm()

@tool
def data_agent(data_agent_query: str, current_plan_step: str):
    """High-level DataAgent using SQL, selection, and merge tools."""
    print(' ')
    print('CALLING DATA AGENT📊')
    print(' ')
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

    result = agent.invoke({"messages": [{"role": "user", "content": data_agent_query}]})

    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]

    if not tool_msgs:
        create_log('DataAgent', 'Agent did not call any tools', 'error', current_plan_step, None, data_agent_query)
        print(True)
        print(execution_list.execution_log_list)        
        return {"object_id":None, "summary":'Agent did not call any tools', "exception":'No tool call'}
    
    last_tool_output = tool_msgs[-1].content

    try:
        tool_json=json.loads(last_tool_output)
    except Exception as e:
        print(True)
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

    print(msg)
    return msg


#if dataset is bigger than certain size, always reprompt to specify the constrains of the retrival. Setting hard limits is also ok for now
#data agent, planner should also know about not retriving the whole dataset.

#allow full execution only if user asked, also with the limit of not more than a 1000 
#otherwise, if not explicitely stated by user, reprompt about constraint, (if data exceeds a predifined limit)