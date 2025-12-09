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
    make_bar_chart_tool
)
from src.multi_agent_analyst.utils.utils import context, object_store, execution_list, ExecutionLogEntry, agent_logs

tool_llm = ChatOllama(model="gpt-oss:20b", temperature=0)
openai_llm = ChatOpenAI(model="gpt-5-mini")

@tool(description="Visualization agent returning images/tables based on query.")
def visualization_agent(visualizer_query: str, data_id: str):
    print(' ')
    print('CALLING VISUALIZATION AGENT🎨')
    print(visualizer_query)
    df = object_store.get(data_id)

    tools = [
        make_line_plot_tool(df),
        make_scatter_plot_tool(df),
        make_pie_chart_tool(df),
        make_table_visualization_tool(df),
        make_bar_chart_tool(df)
    ]

    agent = create_agent(
        openai_llm,
        tools=tools,
        system_prompt=VISUALIZATION_AGENT_PROMPT,
        response_format=ExternalAgentSchema,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": visualizer_query}]})

    r=result['structured_response']

    agent_logs.append(r)
    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    tool_obj_id=[m for m in result['messages'] if isinstance(m, ToolMessage)][-1].content
    msg=json.loads(last_msg)

    final_obj_id=msg['object_id']
    exception=msg['exception']

    # context.set("VisualizationAgent", current_plan_step, final_obj_id)
    # log=ExecutionLogEntry(id=current_plan_step, agent='VisualizationAgent', sub_query=visualizer_query, status='success' if exception is None else 'error', output_object_id=final_obj_id, error_message=exception)

    msg['object_id']=tool_obj_id

    # execution_list.execution_log_list.setdefault(current_plan_step, log)
    print(agent_logs)
    return r
