# src/multi_agent_analyst/agents/data_agent.py
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.tools.data_agent_tools import (
    make_sql_query_tool,
    make_select_columns_tool,
    make_merge_tool,
)
import json
from src.multi_agent_analyst.prompts.react_agents.data_agent import DATA_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context, object_store
from src.multi_agent_analyst.schemas.data_agent_schema import ExternalAgentSchema
from src.multi_agent_analyst.schemas.resolver_agent_schema import ExecutionLogList, ExecutionLogEntry

openai_llm = ChatOpenAI(model="gpt-4.1-mini")

@tool
def data_agent(data_agent_query: str, current_plan_step: str):
    """High-level DataAgent using SQL, selection, and merge tools."""

    tools = [
        make_sql_query_tool(),
        make_select_columns_tool(),
        make_merge_tool(),
    ]

    agent = create_agent(
        openai_llm,
        tools=tools,
        system_prompt=DATA_AGENT_PROMPT,
        response_format=ExternalAgentSchema,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": data_agent_query}]})

    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content

    msg=json.loads(last_msg)
    final_obj_id=msg['object_id']

    log=ExecutionLogEntry(step_id=current_plan_step, agent='DataAgent', sub_query=data_agent_query, status='success', output_object_id=final_obj_id)
    print(' ')
    print('DATA AGENT LOG')
    print(log)
    print(' ')
    context.set("DataAgent", current_plan_step, final_obj_id)
    
    return last_msg


