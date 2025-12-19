from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Any, Optional

#CRITIC SCHEMA
class CriticStucturalResponse(BaseModel):
    fixable:bool    
    requires_user_input:bool
    message_to_user:str
    plan_errors:List[str]
    valid:bool

#PLANNER SCHEMA
class Step(BaseModel):
    id:str
    agent:str
    sub_query:str
    inputs:list[str]
    outputs:list[str]

#PLAN OF STEPS
class Plan(BaseModel):
    plan:List[Step]

class DAGNode(BaseModel):
    id: str                     # "S1", "S2", ...
    agent: str                 # "DataAgent", "AnalysisAgent", etc.
    sub_query: str             # instruction for the agent
    inputs: List[str] = []     # placeholder input object IDs
    outputs: List[str] = []    # ["<output_of_S1>"]

class DAGEdge(BaseModel):
    from_node: str             # "S1"
    to_node: str               # "S2"
    condition: Optional[str] = None   # e.g. "outlier_count > 0"

class DAGPlan(BaseModel):
    nodes: List[DAGNode]
    edges: List[DAGEdge]

#FIX FROM REVISOR
class RevisionState(BaseModel):
    fixed_plan:DAGPlan
    fixed_manually: bool

#CLASSIFY USER'S INTENT
class IntentSchema(BaseModel):
    intent:str
    is_sufficient:bool
    missing_info:str
    result_mode:Literal['analysis', 'preview', 'full']

#REWRITE USER'S QUERY
class ContextSchema(BaseModel):
    clean_query:str

class GraphState(BaseModel):
    # USER INPUT
    query: str
    clean_query: Optional[str] = None
    clarification: Optional[str] = None

    # MEMORY
    conversation_history: List[Dict[Any, Any]] = Field(default_factory=list)

    # PLANNING
    plan: Optional[DAGPlan] = None
    critic_output: Optional[CriticStucturalResponse] = None
    fixed_manually: Optional[bool] = None
    valid: Optional[bool] = None

    # USER CLARITY
    requires_user_clarification: bool = False
    message_to_user: Optional[str] = None

    # INTERNAL ROUTING
    desicion: Optional[str] = None
    execution_exception: Optional[str]=None
    retrival_mode:Optional[str]=None

    # EXECUTION OUTPUT
    final_obj_id: Optional[str] = None
    summary: Optional[str] = None
    final_response: Optional[str] = None
    # THREAD
    thread_id: Optional[str] = None
    dataset_schemas:Optional[Dict[str, Any]] = None

    @staticmethod
    def reducers():
        return {
            "conversation_history": lambda old, new: old + new
        }