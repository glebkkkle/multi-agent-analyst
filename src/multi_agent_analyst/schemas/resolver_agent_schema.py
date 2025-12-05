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
