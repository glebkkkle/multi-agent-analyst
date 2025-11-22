# src/multi_agent_analyst/agents/visualization_agent.py

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
import json
from src.multi_agent_analyst.prompts.react_agents.visualization_agent import VISUALIZATION_AGENT_PROMPT
from src.multi_agent_analyst.schemas.visualization_agent_schema import ExternalAgentSchema
from src.multi_agent_analyst.tools.visualization_agent_tools import (
    make_line_plot_tool,
    make_scatter_plot_tool,
    make_pie_chart_tool,
    make_table_visualization_tool,
)
from src.multi_agent_analyst.utils.utils import context, object_store

tool_llm = ChatOllama(model="gpt-oss:20b", temperature=0)


@tool(description="Visualization agent returning images/tables based on query.")
def visualization_agent(visualizer_query: str, current_plan_step: str, data_id: str):

    df = object_store.get(data_id)

    tools = [
        make_line_plot_tool(df),
        make_scatter_plot_tool(df),
        make_pie_chart_tool(df),
        make_table_visualization_tool(df),
    ]

    agent = create_agent(
        tool_llm,
        tools=tools,
        system_prompt=VISUALIZATION_AGENT_PROMPT,
        response_format=ExternalAgentSchema,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": visualizer_query}]})
    print(result)
    last_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content

    msg=json.loads(last_msg)
    final_obj_id=msg['final_obj_id']

    context.set("VisualizationAgent", current_plan_step, final_obj_id)

    return last_msg
