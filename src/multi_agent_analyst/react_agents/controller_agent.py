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

openai_llm = ChatOpenAI(model="gpt-5.2")

class ExternalAgentSchema(BaseModel):
    summary:str
    object_id:str
    result_details:Any 
    exception:Optional[str]

controller_agent = create_agent(
    model=openai_llm,
    tools=[data_agent, analysis_agent, visualization_agent, resolver_agent],
    system_prompt=CONTROLLER_AGENT_PROMPT,
    response_format=ExternalAgentSchema,
)

#alright so the left tasks are : figure out something about agents operating blindly with the data they receive 
#add analysis tool about distribution 
