from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Any 

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
    intent: Literal["plan", "chat"]
    reason: str
    

class ContextSchema(BaseModel):
    clean_query:str

class GraphState(BaseModel):
    query: str
    clarification : str | None = None
    plan: Plan | None = None
    desicion : str | None = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    clean_query:str | None = None

    awaiting_user_input : bool = False

    final_obj_id:str | None = None
    summary:str | None = None
    final_response:str | None = None

    fixable:bool =False

    fixed_plan:Plan | None = None
    message_to_user : str = None
    fixed_manually:bool | None = None

    requires_user_clarification:bool=False

    critic_output: CriticStucturalResponse | None = None
    valid:bool=False 

    react_error:str | None = None
    failed_agent: str | None = None
    failed_step: str | None = None
    error_message : str | None = None
    _inputs: Dict[Any, Any] = {}

    @staticmethod
    def reducers():
        return {
            "conversation_history": lambda old, new: old + new
        }