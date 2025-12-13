from pydantic import BaseModel
from typing import Optional, Any, List, Dict, Literal
from src.multi_agent_analyst.graph.states import DAGNode, DAGEdge

class ResolverOutput(BaseModel):
    action: Literal['retry_with_fixed_step', 'abort']
    agent:str=None
    corrected_node: Optional[DAGNode] = None
    object_id:Optional[str]=None
    reason: str

#a better schema needed for the resolver, with actual concrete fixes 
#changing the prompting both to the controller and resolver 
class NewResolverOuput(BaseModel):
    action:Literal['retry_with_fixed_step', 'abort']
    agent:str=None
    corrected_node:Optional[DAGNode]=None
    reason:str
    object_id:str=None