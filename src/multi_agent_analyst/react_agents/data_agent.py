# src/multi_agent_analyst/agents/data_agent.py
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.tools.data_agent_tools import (
    make_sql_query_tool,
    make_select_columns_tool,
    make_merge_tool,
)

import json
from src.multi_agent_analyst.prompts.react_agents.data_agent import DATA_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context,ExecutionLogEntry, execution_list, agent_logs, current_tables
from src.multi_agent_analyst.schemas.data_agent_schema import ExternalAgentSchema
openai_llm = ChatOpenAI(model="gpt-4.1-mini")



@tool
def data_agent(data_agent_query: str):
    """High-level DataAgent using SQL, selection, and merge tools."""
    print(' ')
    print('CALLING DATA AGENT📊')
    print(' ')
    print(data_agent_query)

    tools = [
        make_sql_query_tool(),
        make_select_columns_tool(),
        make_merge_tool(),
    ]
    # .format(tables=list(current_tables.values())
    agent = create_agent(
        openai_llm,
        tools=tools,
        system_prompt=DATA_AGENT_PROMPT.format(tables=current_tables.values()),
        response_format=ExternalAgentSchema,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": data_agent_query}]})
    print(' ')
    r=(result['structured_response'])

    agent_logs.append(r)

    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_obj_id=[m for m in result['messages'] if isinstance(m, ToolMessage)][-1].content



    msg=json.loads(last_msg)
    final_obj_id =msg['object_id']
    exception=msg['exception']

    # log=ExecutionLogEntry(id=current_plan_step, agent='DataAgent', sub_query=data_agent_query, status='success' if exception is None else exception, output_object_id=final_obj_id, error_message=exception if exception is not None else None)
    # execution_list.execution_log_list.setdefault(current_plan_step, log)

    msg['object_id']=tool_obj_id

    print(agent_logs)
    # context.set("DataAgent", current_plan_step, final_obj_id)
    return r 


#perhaps some security for the sql agent (recheck queries or smth)


#fix so the resolver identifies CORRECT AGENT THAT CAUSED THE FAILURE
#fix the prompting to the controller about what when to run, ensuring correct object ids are passed after correction has been completed.
