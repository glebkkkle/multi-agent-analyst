# src/multi_agent_analyst/agents/controller_agent.py
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.prompts.react_agents.controller_agent import CONTROLLER_AGENT_PROMPT
from langchain_ollama import ChatOllama
from src.multi_agent_analyst.react_agents.data_agent import data_agent
from src.multi_agent_analyst.react_agents.analysis_agent import analysis_agent
from src.multi_agent_analyst.react_agents.visualization_agent import visualization_agent
from src.multi_agent_analyst.react_agents.resolver_agent import resolver_agent
from pydantic import Field, BaseModel
from typing import Optional


openai_llm = ChatOpenAI(model="gpt-5.1")
llm = ChatOllama(model="gpt-oss:20b", temperature=0)

class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    summary : str=Field(..., description='A final summary of execution')
    exception: Optional[str]=Field(..., description='placeholder for exception message')

controller_agent = create_agent(
    model=openai_llm,
    tools=[data_agent, analysis_agent, visualization_agent,],
    system_prompt=CONTROLLER_AGENT_PROMPT,
    response_format=ExternalAgentSchema,
)

#could potentially pass all the previous logs, for safety
#maybe catch some errors in the controller output and loop again with resolver, as with planning 

# result=controller_agent.invoke({'messages':[{'role':'user', 'content':'visualize profit with line plot'}]})

# print(result)
