from pydantic import BaseModel
from typing import Optional, Any, List, Dict, Literal
from src.multi_agent_analyst.graph.states import DAGNode, DAGEdge

class ResolverOutput(BaseModel):
    action: Literal['retry_with_fixed_step', 'abort']
    agent:str=None
    corrected_node: Optional[DAGNode] = None
    object_id:Optional[str]=None
    reason: str

class NewResolverOuput(BaseModel):
    action:Literal['retry_with_fixed_step', 'abort']
    agent:str=None
    corrected_node:Optional[DAGNode]=None
    reason:str
    object_id:str=None