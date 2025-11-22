# src/multi_agent_analyst/agents/controller_agent.py
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.utils.utils import context
from src.multi_agent_analyst.schemas.analysis_agent_schema  import ExternalAgentSchema
from src.multi_agent_analyst.prompts.react_agents.controller_agent import CONTROLLER_AGENT_PROMPT
from langchain_ollama import ChatOllama
from src.multi_agent_analyst.react_agents.data_agent import data_agent
from src.multi_agent_analyst.react_agents.analysis_agent import analysis_agent
from src.multi_agent_analyst.react_agents.visualization_agent import visualization_agent
from src.multi_agent_analyst.graph.states import Plan
from src.multi_agent_analyst.prompts.graph.planner import GLOBAL_PLANNER_PROMPT


openai_llm = ChatOpenAI(model="gpt-4.1-mini")
llm = ChatOllama(model="gpt-oss:20b", temperature=0)


controller_agent = create_agent(
    model=openai_llm,
    tools=[data_agent, analysis_agent, visualization_agent],
    system_prompt=CONTROLLER_AGENT_PROMPT,
    response_format=ExternalAgentSchema,
)

plan=llm.with_structured_output(Plan).invoke(GLOBAL_PLANNER_PROMPT.format(query='Run correlation analysis on profit from sales table'))

plan=str(plan)
print(plan)

res=controller_agent.invoke({'messages':[{'role':'user', 'content':plan}]})

