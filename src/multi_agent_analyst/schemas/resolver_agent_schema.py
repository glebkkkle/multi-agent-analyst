from pydantic import BaseModel
from typing import Optional, Any, List, Dict, Literal
from src.multi_agent_analyst.graph.states import Step

class ResolverOutput(BaseModel):
    action: Literal['retry_with_fixed_step', 'abort']
    agent:str=None
    corrected_step: Optional[Step] = None
    object_id:Optional[str]=None
    reason: str

#a better schema needed for the resolver, with actual concrete fixes 
#changing the prompting both to the controller and resolver 

"""
action=retry_with_fixed_step:
    should indicate that the controller should try to run the plan again, only with corrected input now

corrected_step:
    A complete STEP field, which has rewritten query (for more clarity), and all of the neccessary info for successful execution

object_id:
    optional, if the id was wrong in the first place

reason:
    short reasoning about what and why went wrong, so the controller understands

carefully analyze the exception, what was the issue, what went wrong? 
if column is missing, should try to rerun the DataAgent, wrong id - correct it and also rerun, wrong tool choice - rerun 

wire the new plan to the controller, and explicitely say to rerun it (fixed version), either from the beginning if the failled step depended on the previous step, or from the failed step directly.
heavily empasize to actually reason about what went wrong and what could be done to fix it

chaning the controller prompt as well so it knows how to handle such scenarios 
"""
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

{
  "action": "retry_with_fixed_step" | "abort",
  "corrected_step": <Step object or null>,
  "object_id": <corrected id or null>,
  "reason": "<short explanation>"
}

- corrected_step MUST be present when action="retry_with_fixed_step"
- object_id is optional (only if an ID was wrong)

Do NOT output anything outside this JSON.

Current Log:
{log}
"""