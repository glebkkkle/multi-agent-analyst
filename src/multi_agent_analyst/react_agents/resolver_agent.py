from src.multi_agent_analyst.schemas.resolver_agent_schema import ResolverOutput, NewResolverOuput
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context, execution_list
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from langchain.agents import create_agent
from src.backend.llm.registry import get_default_llm
from src.multi_agent_analyst.logging import logger
llm=get_default_llm()

MAX_RETRIES=2

@tool 
def resolver_agent():
    'Resolver Agent that can solve exceptions that occurred during execution of agents'
    logger.info(
        "ResolverAgent started",
        extra={
            "agent": "ResolverAgent",
        }
    )
    attempt = len(execution_list.execution_log_list.get("resolver_fix", [])) + 1
    if attempt > MAX_RETRIES:
        logger.info(
            "ResolverAgent aborted after MAX TRIES",
            extra={
            "agent": "ResolverAgent",
        }
    )
        return {
            "action": "abort",
            "reason": f"Retry limit exceeded ({MAX_RETRIES})"
        }

    log=execution_list.execution_log_list

    agent=create_agent(model=llm, tools=[],response_format=ResolverOutput)

    result=agent.invoke({'messages':[{'role':'user', 'content':RESOLVER_AGENT_PROMPT.format(log=log)}]})
    repair_response=(result['structured_response'])

    execution_list.execution_log_list.setdefault('resolver_fix', []).append(repair_response)

    return repair_response

