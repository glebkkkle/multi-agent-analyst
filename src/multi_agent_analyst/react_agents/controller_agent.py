# src/multi_agent_analyst/agents/controller_agent.py
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.prompts.react_agents.controller_agent import CONTROLLER_AGENT_PROMPT
from src.multi_agent_analyst.react_agents.data_agent import data_agent
from src.multi_agent_analyst.react_agents.analysis_agent import analysis_agent
from src.multi_agent_analyst.react_agents.visualization_agent import visualization_agent
from src.multi_agent_analyst.react_agents.resolver_agent import resolver_agent
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.backend.llm.registry import get_default_llm

llm=get_default_llm()

class ExternalAgentSchema(BaseModel):
    summary:str
    object_id:str
    result_details:Any 
    exception:Optional[str]

controller_agent = create_agent(
    model=llm,
    tools=[data_agent, analysis_agent, visualization_agent, resolver_agent],
    system_prompt=CONTROLLER_AGENT_PROMPT,
    response_format=ExternalAgentSchema,
)

