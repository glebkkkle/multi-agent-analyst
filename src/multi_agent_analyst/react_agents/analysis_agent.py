# src/multi_agent_analyst/agents/analysis_agent.py

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import json

from src.multi_agent_analyst.tools.analysis_agent_tools import (
    make_correlation_tool,
    make_anomaly_tool,
    make_periodic_tool,
    make_summary_tool,
)
from pydantic import BaseModel
from src.multi_agent_analyst.prompts.react_agents.analysis_agent import ANALYST_AGENT_PROMPT
from src.multi_agent_analyst.schemas.analysis_agent_schema import ExternalAgentSchema
from src.multi_agent_analyst.utils.utils import context, object_store
from src.multi_agent_analyst.utils.utils import execution_list, ExecutionLogEntry
openai_llm = ChatOpenAI(model="gpt-5-mini")


class AnalysisAgentArgs(BaseModel):
    analysis_query: str
    current_plan_step: str
    data_id: str

@tool(args_schema=AnalysisAgentArgs)
def analysis_agent(analysis_query: str, current_plan_step: str, data_id: str):
    """Analysis Agent performing correlation, anomaly detection, periodicity, etc."""

    # print(analysis_query, current_plan_step, data_id)
    log=ExecutionLogEntry(id=current_plan_step, agent='AnalysisAgent', sub_query=analysis_query)
    execution_list.execution_log_list.setdefault(current_plan_step, log)
    # 1) Load the data based on the ID
    df = object_store.get(data_id)

    # 2) Create df-bound tool instances
    correlation_tool = make_correlation_tool(df)
    anomaly_tool = make_anomaly_tool(df)
    periodic_tool = make_periodic_tool(df)
    summary_tool = make_summary_tool(df)

    # 3) Create agent *with the tools bound to this df*
    agent = create_agent(
        openai_llm,
        tools=[correlation_tool, anomaly_tool, periodic_tool, summary_tool],
        system_prompt=ANALYST_AGENT_PROMPT,
        response_format=ExternalAgentSchema,
    )

    #catch exception here, return with schema (ExternalAgentSchema) to controller that error occurred

    # 4) Execute LLM agent
    result = agent.invoke({"messages": [{"role": "user", "content": analysis_query}]})
    
    print(result)
    last = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_obj_id=[m for m in result['messages'] if isinstance(m, ToolMessage)][-1].content


    msg=json.loads(last)
    final_obj_id=msg['object_id']
    # 5) Save final output ID
    exception=msg['exception']
    context.set("AnalysisAgent", current_plan_step,final_obj_id)

    log.output_object_id=final_obj_id

    log.status='success' if exception is None else 'error'
    # # #move the log 
    
    # print(log)
    # print(' ')
    # execution_list.execution_log_list.setdefault(current_plan_step, log)
    execution_list.execution_log_list[current_plan_step]=log

    msg['object_id']=tool_obj_id
    print(msg)
    return msg

#issue with returning correct object id!! 
#copy the id from the output of the tool and pass it to the json manually

#fix the issue with logs 
