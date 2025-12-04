from src.multi_agent_analyst.schemas.resolver_agent_schema import ResolverOutput
from src.multi_agent_analyst.prompts.react_agents.resolver_agent import RESOLVER_AGENT_PROMPT
from src.multi_agent_analyst.utils.utils import context, execution_list
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from langchain.agents import create_agent

llm = ChatOpenAI(model="gpt-4.1-mini")
log="""{'S1': ExecutionLogEntry(id='S1', agent='DataAgent', sub_query='Retrieve the profit data from the database using sql_query', status='success', output_object_id='obj_289712ac', error_message=None), 'S2': ExecutionLogEntry(id='S2', agent='VisualizationAgent', sub_query='Visualize the profit data as a line_plot', status='success', output_object_id='', error_message='Line plot requires a date column.')}"""

P="""
You are the Resolver Agent in a multi-step execution system.
One step in the plan has FAILED. 

A **Plan** consists of ordered steps.  
Each step has:
- id (e.g., "S1")
- agent: "DataAgent" | "AnalysisAgent" | "VisualizationAgent"
- sub_query: natural-language instruction for that agent
- inputs: list of objects required for execution (if any)
- outputs: expected output of the agent. 

Your job is to carefully analyze what went wrong and return a corrected version of the
step that should be re-executed.

────────────────────────────────────────
### HOW TO REASON
Internally, analyze:

1. What does the exception say?
2. What exactly caused the failure?
   - Missing column? → The DataAgent step that produced the dataframe may need to be corrected.
   - Wrong object ID? → Use context_lookup to find the correct one.
   - Wrong agent/tool? → Replace agent with the correct one.
   - Incorrect or incomplete sub_query? → Rewrite it clearly.

3. Decide which step MUST be corrected:
   - If the failing step itself is incorrect, correct that step.
   - If the failure was caused by a previous step (e.g., DataAgent returned incomplete data),
     correct THAT step instead.
Use:
- The failed_step object  
- The execution_log (previous tool results & messages)  
- The error_message  
- The CURRENT OBJECT STORE (called **context**)  

You may correct *either* the failing step or the upstream producing step,
but NEVER create new steps.

You have access to a TOOL:
`context_lookup(object_name_or_id)`
→ Returns the correct existing object ID OR "not found".

Always use this tool when:
- An input ID looks wrong

### How to repair a step
You may:
- Fix incorrect object IDs using context_lookup
- Fix incorrect inputs list
- Fix column names based on previous outputs
- Fix sub_query wording to match what the agent actually requires

────────────────────────────────────────
Your corrected_step MUST be:
   - A complete and valid Step object
   - With rewritten sub_query if needed to clearly emphasize the fix
   - With corrected agent, input_object_ids, or object_id fixes

────────────────────────────────────────
### WHEN TO ABORT
Return action="abort" ONLY when:
   - The missing information cannot be recovered from context
   - The step cannot be repaired reliably

────────────────────────────────────────
### OUTPUT FORMAT (JSON ONLY)

  "action": "retry_with_fixed_step" | "abort",
  'agent': <AgentName to rerun the corrected step>
  "corrected_step": <Step object or null>,
  "object_id": <corrected id or null>,
  "reason": "<short explanation>"


- corrected_step MUST be present when action="retry_with_fixed_step"
- object_id is optional (only if an ID was wrong)

Do NOT output anything outside this JSON.

Current Log:
{log}
"""


# @tool 
def resolver_agent():
    'Resolver Agent that can solve exceptions that occurred during execution of agents'

    print('CALLING RESOLVER')
    
    # print(failed_step)
    log=execution_list.execution_log_list
    
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
    result=agent.invoke({'messages':[{'role':'user', 'content':P.format(log=log)}]})
    repair_response=(result['structured_response'])

    print(repair_response)

    return repair_response


#add a tool that allows for the controller to re-run the plan, if something went wrong and cannot be fixed easily

# resolver_agent('S2')
