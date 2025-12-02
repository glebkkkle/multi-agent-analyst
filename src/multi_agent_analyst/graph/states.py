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

#FIX FROM REVISOR
class RevisionState(BaseModel):
    fixed_plan:Plan
    fixed_manually: bool

#CLASSIFY USER'S INTENT
class IntentSchema(BaseModel):
    intent: Literal["plan", "chat"]
    reason: str
    
#REWRITE USER'S QUERY
class ContextSchema(BaseModel):
    clean_query:str

class GraphState(BaseModel):
    # USER INPUT
    query: str
    clean_query: Optional[str] = None
    clarification: Optional[str] = None

    # MEMORY
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    # PLANNING
    plan: Optional[Plan] = None
    critic_output: Optional[CriticStucturalResponse] = None
    fixed_manually: Optional[bool] = None
    valid: Optional[bool] = None

    # USER CLARITY
    requires_user_clarification: bool = False
    message_to_user: Optional[str] = None

    # INTERNAL ROUTING
    desicion: Optional[str] = None

    # EXECUTION OUTPUT
    final_obj_id: Optional[str] = None
    summary: Optional[str] = None
    final_response: Optional[str] = None

    data_samples:Optional[Dict]=None
    # THREAD
    thread_id: Optional[str] = None

    @staticmethod
    def reducers():
        return {
            "conversation_history": lambda old, new: old + new
        }