from src.multi_agent_analyst.schemas.resolver_agent_schema import ResolverOutput
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT, f
from src.multi_agent_analyst.utils.utils import context, execution_list
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from langchain.agents import create_agent

llm = ChatOpenAI(model="gpt-4.1-mini")


@tool 
def resolver_agent():
    'Resolver Agent that can solve exceptions that occurred during execution of agents'

    
    # print(failed_step)
    log=execution_list.execution_log_list
    print(' ')
    print(f'CALLING RESOLVER AGENT WITH EXCEPTION🛠️')
    print(' ')
    # print(step_log)
    # current_exception=step_log.error_message if step_log.error_message is not None else step_log.error_message

    @tool
    def context_lookup(agent_name:str):
        'A tool that can look up the context dictionary to inspect ids returned by the agents.'
        print('CALLING WITH REPAIR')
        print(agent_name)        
        return context.dict

    agent=create_agent(model=llm, tools=[],response_format=ResolverOutput)

    # result=agent.invoke({'messages':[{'role':'user', 'content':RESOLVER_AGENT_PROMPT.format(error_message=current_exception,failed_step=step_log, context=context, execution_log=execution_list.execution_log_list)}]})
    result=agent.invoke({'messages':[{'role':'user', 'content':RESOLVER_AGENT_PROMPT.format(log=log)}]})
    repair_response=(result['structured_response'])
    print(' ')
    print(repair_response)
    print(' ')
    execution_list.execution_log_list.setdefault('resolver', repair_response)
    return repair_response

