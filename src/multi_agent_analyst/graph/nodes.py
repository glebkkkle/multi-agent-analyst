from langchain_core.messages import AIMessage
import json
from src.multi_agent_analyst.db.loaders import load_user_tables
from src.multi_agent_analyst.react_agents.controller_agent import controller_agent
from src.multi_agent_analyst.utils.utils import object_store, execution_list, current_tables
from src.multi_agent_analyst.graph.states import GraphState, CriticStucturalResponse, RequestTrace, IntentSchema, DAGPlan,RevisionState, CleanQueryState, ContextSchema
from src.multi_agent_analyst.prompts.graph.planner import PLANNER_PROMPT
from src.multi_agent_analyst.prompts.graph.critic import CRITIC_PROMPT
from src.multi_agent_analyst.prompts.graph.revision import PLAN_REVISION_PROMPT
from src.multi_agent_analyst.prompts.chat.intent_classifier import INTENT_CLASSIFIER_PROMPT
from src.multi_agent_analyst.prompts.chat.context_agent import cleaned_query
from src.multi_agent_analyst.prompts.chat.chat_reply_prompt import CHAT_REPLY_PROMPT
from src.backend.llm.registry import get_default_llm, get_mini_llm
from src.multi_agent_analyst.logging import logger, trace_logger
from src.backend.storage.emitter import emit, init_thread_tables, get_current_tables
from src.multi_agent_analyst.utils.utils import guarded

llm = get_default_llm()
mini = get_mini_llm()

@guarded("planner")
def planner_node(state: GraphState):
    logger.info(
        "Planner started",
        extra={
            "thread_id": state.thread_id,
            "retrieval_mode": state.retrieval_mode,
        }
    )
    plan = llm.with_structured_output(DAGPlan).invoke(
        PLANNER_PROMPT.format(schemas=state.dataset_schemas,query=state.query, retrieval_mode=state.retrieval_mode)
    )
    emit('Drafting Plan..')
    logger.info(
        "Planner finished",
        extra={
            "thread_id": state.thread_id,
        }
    )
    if state.trace:
        state.trace.plan = plan

    return {"plan": plan, "trace":state.trace, }

@guarded("critic")
def critic(state: GraphState):
    response = llm.with_structured_output(CriticStucturalResponse).invoke(
        CRITIC_PROMPT.format(
            schemas=state.dataset_schemas,
            query=state.query,
            plan=state.plan
        )
    )
    if state.trace:
        state.trace.critic_verdict = {
            "valid": response.valid,
            "requires_user_input": response.requires_user_input,
            "message_to_user": response.message_to_user,
        }

    return {
        "critic_output": response,
        "message_to_user": response.message_to_user,
        "requires_user_clarification": response.requires_user_input,
        "valid": response.valid,
        "desicion":str(response.valid), 
        "trace":state.trace
    }

@guarded("revision_node")
def revision_node(state: GraphState):

    logger.info(
        "Critic evaluating plan",
        extra={
            "thread_id": state.thread_id,
        }
    )
    response = llm.with_structured_output(RevisionState).invoke(
        PLAN_REVISION_PROMPT.format(
            critic_output=state.critic_output,
            initial_plan=state.plan,
            user_query=state.clean_query
        )
    )
    logger.info(
        "Critic finished evaluation",
        extra={
            "thread_id": state.thread_id,
            "valid": state.valid,
        }
    )

    return {
        "plan": response.fixed_plan,
        "fixed_manually": response.fixed_manually,
        "message_to_user": state.message_to_user, 
        "valid": state.valid
    }

@guarded("router_node")
def router_node(state: GraphState):
    current_tables.setdefault(state.thread_id, load_user_tables(state.thread_id))
    try:
        result = controller_agent.invoke({
            "messages": [
                {"role": "user", "content": str(state.plan)}
            ]
        })
    except Exception as e:        
        return  {"desicion": "error", "has_error": True, "execution_exception": str(e)}
    
    last = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    try:
        d = json.loads(last)
    except Exception as e:
        return {"desicion": "error", "has_error": True, "execution_exception": str(e)}

    if state.trace:
        state.trace.final = {
            "status":"completed", 
        }
    
    object_id=d.get("object_id")
    print(object_id)
    print(' ')
    return {
        "desicion":"ok",
        "final_obj_id": d["object_id"],
        "summary": d["summary"], 
        "final_table_shape":d['result_details'], 
        "trace":state.trace
    }

@guarded("revision_router")
def revision_router(state: GraphState):
    if state.valid:
        return {"desicion": "valid"}

    if state.requires_user_clarification:
        return {
            "desicion": "ask_user",
            "message_to_user": state.message_to_user
        }

    if state.fixed_manually:
        return {"desicion": "critic"}

    return {"desicion": "END"}

@guarded("ask_user")
def ask_user_node(state: GraphState):
    logger.info("Graph suspended")
    return {
        "message_to_user": state.message_to_user,
        "requires_user_clarification": True,
    }
def routing(state:GraphState):
    return state.desicion


def router_for(path_map: dict):
    allowed = set(path_map.keys())

    def _route(state: GraphState):
        # ERROR ALWAYS WINS
        if getattr(state, "has_error", False) and "error" in allowed:
            return "error"

        d = getattr(state, "desicion", None)
        if d in allowed:
            return d

        if "error" in allowed:
            return "error"

        return next(iter(allowed))
    return _route


def allow_execution(state:GraphState):
    return {}

@guarded("chat_node")
def chat_node(state: GraphState):
    user_msg = state.query

    schemas = load_user_tables(state.thread_id)
    current_tables.setdefault(state.thread_id, schemas)

    init_thread_tables(state.thread_id)

    intent = mini.with_structured_output(IntentSchema).invoke(
        INTENT_CLASSIFIER_PROMPT.format(
            user_query=user_msg,
            data_schemas=schemas,
            conversation_history=state.conversation_history
        )
    )
    if intent.intent == 'abort':
        new_history = state.conversation_history + [
        {"role":'user', "content":user_msg},
        {"role": "system", "content": intent.missing_info}
        ]
        return {"desicion":'abort', 
                "conversation_history":new_history, 
                "dataset_schemas":schemas, 
                "message_to_user":intent.missing_info
                }

    # 🔒 GUARD: insufficient information
    if intent.intent == "clarification" and intent.is_sufficient == False:
        new_history = state.conversation_history + [
        {"role":'user', "content":user_msg},
        {"role": "system", "content": intent.missing_info}
        ]
        return {
            "desicion": "ask_user",
            "requires_user_clarification": True,
            "message_to_user": intent.missing_info,
            "conversation_history": new_history,
            "dataset_schemas": schemas,
        }
    if intent.intent == "plan":
        new_history=state.conversation_history + [{"role":'user', "content":user_msg}]
        return {
            "desicion": "planner",
            "conversation_history": new_history,
            "dataset_schemas": schemas,
            "retrieval_mode":intent.result_mode
        }

    if intent.intent == "chat":
        new_history=state.conversation_history + [{"role":'user', "content":user_msg}]
        return {
            "desicion": "chat",
            "conversation_history": new_history,
            "dataset_schemas": schemas,
        }
    
@guarded("chat_reply")
def chat_reply(state: GraphState):
    reply = mini.invoke(CHAT_REPLY_PROMPT.format(user_query=state.query, conversation_history=state.conversation_history, data_list=state.dataset_schemas))
    return {"final_response": reply.content}

@guarded("execution_error")
def execution_error_node(state: GraphState):
    return {
        "final_response": (
            "I ran into a problem while executing your request.\n\n"
            f"Details: {state.execution_exception}\n\n"
            "You can try rephrasing your request or choosing a different operation."
        ),
        "final_obj_id": None,
        "image_base64": None,
    }

@guarded("clean_query")
def clean_query(state:GraphState):
    conv_history=state.conversation_history

    trace = state.trace
    if state.trace is None:
        trace = RequestTrace(
            thread_id=state.thread_id,
            input={"raw_query": state.query}
        )

    response=mini.with_structured_output(CleanQueryState).invoke(cleaned_query.format(original_query=state.query, session_context=conv_history))

    logger.info(
        "Cleaned query generated",
        extra={
            "thread_id":state.thread_id,
            "original_query": state.query,
            "cleaned_query": response.planner_query
        }
    )
    trace.input['cleaned_query'] = response.planner_query
    return {"query":response.planner_query, "trace":trace}


@guarded("final_result_node")
def final_result_node(state:GraphState):
    if state.desicion == 'chat':
            return {'final_response':state.final_response, "image_base64":None, 'final_obj_id':None}
    elif state.desicion == 'abort':
        return {'final_response' : state.message_to_user , "image_base64":None, "final_obj_id":None}
    else:
        if state.trace:
            trace_logger.info(json.dumps(state.trace.model_dump()))
        summary_react=state.summary
        execution_list.execution_log_list.clear()
        return {
            "final_response": summary_react,
            "final_obj_id": state.final_obj_id,
            "final_table_shape":state.final_table_shape, 
            "trace":state.trace
        }

