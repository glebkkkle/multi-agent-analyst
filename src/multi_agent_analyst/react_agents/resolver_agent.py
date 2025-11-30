from src.multi_agent_analyst.schemas.resolver_agent_schema import ResolverOutput
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context, execution_list
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from langchain.agents import create_agent

llm = ChatOpenAI(model="gpt-4.1-mini")

@tool 
def resolver_agent(failed_step:str):
    'Resolver Agent that can solve exceptions that occurred during execution'
    'Args:failed_step:str'

    step_log=execution_list.execution_log_list[failed_step]

    current_exception=step_log.error_message

    @tool
    def context_lookup(agent_name:str):
        'A tool that can look up the context dictionary to inspect ids returned by the agents.'
        results=context[agent_name]
        return results

    agent=create_agent(model=llm, tools=[context_lookup],response_format=ResolverOutput)

    result=agent.invoke({'messages':[{'role':'user', 'content':RESOLVER_AGENT_PROMPT.format(error_message=current_exception,failed_step=step_log, context=context, execution_log=execution_list.execution_log_list)}]})

    return result
