# src/multi_agent_analyst/agents/controller_agent.py
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.schemas.analysis_agent_schema  import ExternalAgentSchema
from src.multi_agent_analyst.prompts.react_agents.controller_agent import CONTROLLER_AGENT_PROMPT
from langchain_ollama import ChatOllama
from src.multi_agent_analyst.react_agents.data_agent import data_agent
from src.multi_agent_analyst.react_agents.analysis_agent import analysis_agent
from src.multi_agent_analyst.react_agents.visualization_agent import visualization_agent
from src.multi_agent_analyst.react_agents.resolver_agent import resolver_agent

openai_llm = ChatOpenAI(model="gpt-5-mini")
llm = ChatOllama(model="gpt-oss:20b", temperature=0)

controller_agent = create_agent(
    model=openai_llm,
    tools=[data_agent, analysis_agent, visualization_agent],
    system_prompt=CONTROLLER_AGENT_PROMPT,
    response_format=ExternalAgentSchema,
)

#could potentially pass all the previous logs, for safety
#maybe catch some errors in the controller output and loop again with resolver, as with planning 
