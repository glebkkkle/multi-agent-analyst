from pydantic import BaseModel, Field
from typing import List, Dict, Literal

class CriticStucturalResponse(BaseModel):
    fixable:bool    
    requires_user_input:bool
    message_to_user:str
    plan_errors:List[str]
    valid:bool


class Step(BaseModel):
    id:str
    agent:str
    sub_query:str
    inputs:list[str]
    outputs:list[str]

class Plan(BaseModel):
    plan:List[Step]


class RevisionState(BaseModel):
    fixed_plan:Plan
    fixed_manually: bool

class IntentSchema(BaseModel):
    intent: Literal["plan", "clarification"]
    reason: str
    

class GraphState(BaseModel):
    query: str
    clarification : str | None = None
    plan: Plan | None = None
    desicion : str | None = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    awaiting_user_input : bool = False

    final_obj_id:str | None = None
    summary:str | None = None
    final_response:str | None = None

    f:str=None
    
    fixable:bool =False

    fixed_plan:Plan | None = None
    message_to_user : str = None
    fixed_manually:bool | None = None

    requires_user_clarification:bool=False

    critic_output: CriticStucturalResponse | None = None
    valid:bool=False


class ExternalAgentSchema(BaseModel):
    object_id:str=Field(..., description='A final ID of the object after all the modification completed.')
    summary:str=Field(..., description='A short summary of steps peformed and final result')
