from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from src.multi_agent_analyst.graph.states import Step
# class ResolverAgentState(BaseModel):
#     failed_step:str=''
#     failed_agent:str=''
#     execution_log:List=[]
#     error_message=''

openai_llm = ChatOllama(model="gpt-oss:20b", reasoning=True, temperature=0)
llm = ChatOpenAI(model="gpt-4.1-mini")

class ExecutionLogEntry(BaseModel):
    id: str
    agent: str
    sub_query: str
    inputs:List[str]=[]
    outputs:List[str]=[]
    status: str  # "success" | "error"
    output_object_id: Optional[str] = None
    error_message: str | None = None

class ExecutionLogList(BaseModel):
    execution_log_list:Dict[str, ExecutionLogEntry]={}

class ResolverOutput(BaseModel):
    action: str 
    corrected_step: Optional[Step] = None
    object_id:Optional[str]=None
    reason: str

# error="KeyError: context.get['bhds1_2435]"

# context='AnalysisAgent:b1245edfg'
# execution_log=ExecutionLogEntry(step_id='S2', agent='AnalysisAgent', sub_query='Run correlation analysis on data', status='Error', output_object_id='b1245edfg', error_message=error)

# def resolver_agent(failed_step, error, execution_log, context_dict):
#     response=llm.invoke(RESOLVER_AGENT_PROMPT.format(failed_step=failed_step, execution_log=execution_log, error_message=error, context=context_dict))

#     print(response.corrected_step)

#     return 

# # resolver_agent('S2', error, execution_log, context)
