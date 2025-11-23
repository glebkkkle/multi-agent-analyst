import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.resolver_agent_schema import (
ExecutionLogEntry, ExecutionLogList, ResolverOutput
)
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import object_store, context
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from langchain.agents import create_agent
openai_llm = ChatOllama(model="gpt-oss:20b", reasoning=True, temperature=0)
llm = ChatOpenAI(model="gpt-4.1-mini")

log=ExecutionLogEntry(id='S1', agent='DataAgent', sub_query='Retrive sales data with sql tool', status='Error', output_object_id='12sfdgbd', inputs=[' '], outputs=['sales_data'])


obj=ExecutionLogList()

obj.execution_log_list.setdefault('S1', log)

exception='Key Error: context.get[12sfdgbd]'

context={'DataAgent':{'S1':'a324hdfs'}, 'AnalysisAgent':{'S2':'3sdkfjh'}}

# @tool 
def resolver_agent(failed_step:str, exception:str):
    'Resolver Agent that can solve exceptions that occurred during execution'

    context={'DataAgent':{'S1':'a324hdfs'}, 'AnalysisAgent':{'S2':'3sdkfjh'}}

    step_log=obj.execution_log_list[failed_step]

    @tool
    def context_lookup(agent_name:str):
        'A tool that can look up the context dictionary to inspect ids returned by the agents.'
        results=context[agent_name]
        return results

    agent=create_agent(model=llm, tools=[context_lookup],response_format=ResolverOutput)

    result=agent.invoke({'messages':[{'role':'user', 'content':RESOLVER_AGENT_PROMPT.format(error_message=exception,failed_step=step_log, context=context)}]})
    print(result)
    
    return 

resolver_agent('S1', exception)