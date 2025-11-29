from langchain_core.messages import AIMessage
import json
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from PIL import Image
import io
from src.multi_agent_analyst.db.loaders import load_user_tables
import base64
from src.multi_agent_analyst.react_agents.controller_agent import controller_agent
from src.multi_agent_analyst.utils.utils import object_store, execution_list, current_tables
from src.multi_agent_analyst.graph.states import GraphState, CriticStucturalResponse, Plan, RevisionState, IntentSchema, ContextSchema
from src.multi_agent_analyst.prompts.graph.planner import  GLOBAL_PLANNER_PROMPT
from src.multi_agent_analyst.prompts.graph.critic import CRITIC_PROMPT
from src.multi_agent_analyst.prompts.graph.revision import PLAN_REVISION_PROMPT
from src.multi_agent_analyst.prompts.graph.summarizer import SUMMARIZER_PROMPT
from src.multi_agent_analyst.prompts.chat.intent_classifier import CHAT_INTENT_PROMPT
from src.multi_agent_analyst.prompts.chat.context_agent import CONTEXT_AGENT_PROMPT

ollama_llm=ChatOllama(model='gpt-oss:20b', temperature=0)
llm=ChatOpenAI(model='gpt-4.1-mini')


def planner_node(state: GraphState):
    print(' ')
    print('PLAN RECEIVED')
    print(' ')
    print(state.query)
    print(state.clean_query)
    plan=llm.with_structured_output(Plan).invoke(GLOBAL_PLANNER_PROMPT.format(query=state.clean_query if state.clean_query else state.query))
    print(plan)
    print(' ')
    return {'plan':plan}

def critic(state:GraphState):
    print(' ')
    print('CRITIC RECIVED A PLAN ')

    plan=state.plan

    response=llm.with_structured_output(CriticStucturalResponse).invoke(CRITIC_PROMPT.format(query=state.clean_query, plan=plan))
    
    fixable, requires_user_input, message_to_user, valid=response.fixable, response.requires_user_input, response.message_to_user, response.valid

    return {'critic_output':response, 'message_to_user':message_to_user, 'fixable':fixable, 'requires_user_clarification':requires_user_input, 'valid':valid}


def revision_node(state:GraphState):
    print(' ')
    print('REVISOR RECEIVED A PLAN')
    print(' ')

    critic_output, initial_plan, user_query, valid =state.critic_output, state.plan, state.clean_query, state.valid

    response=llm.with_structured_output(RevisionState).invoke(PLAN_REVISION_PROMPT.format(critic_output=critic_output, initial_plan=initial_plan, user_query=user_query))

    fixed_plan, fixed_manually = response.fixed_plan, response.fixed_manually

    return {'message_to_user':state.message_to_user, 'valid':valid, 'plan':fixed_plan, 'fixed_manually':fixed_manually}


def router_node(state: GraphState):
    current_tables.setdefault(state.thread_id, load_user_tables(state.thread_id))
    print(current_tables)
    result = controller_agent.invoke({
        'messages': [
            {'role':'user', 'content': str(state.plan)}
        ]
    })
    print(' ')
    print('CONTROLLER AGENT')
    
    print(result)
    print(' ')
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    last_ai_msg = ai_messages[-1].content
    
    d = json.loads(last_ai_msg)

    id, summary=d['object_id'], d['summary']

    return {'final_obj_id':id, 'summary':summary}


def summarizer_node(state:GraphState):
    user_query = state.query

    obj_id, summary = state.final_obj_id, state.summary
    print(f'FINAL OBJ ID:{obj_id}')

    obj = object_store.get(obj_id)

    # If object is image BytesIO → convert to base64
    image_base64 = None
    if isinstance(obj, io.BytesIO):
        image_bytes = obj.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    llm = ChatOllama(model='gpt-oss:20b', temperature=0)
    final_text = llm.invoke(SUMMARIZER_PROMPT.format(user_query=user_query, obj=obj, summary=summary)).content

    print('INITIAL EX')
    print(execution_list.execution_log_list)

    #clear the log list after the graph has been compiled for one turn 

    execution_list.execution_log_list.clear()

    print('FINAL EX')
    print(execution_list.execution_log_list)

    return {
        "final_response": final_text,
        "image_base64": image_base64,
        "final_obj_id":obj_id
    }


def revision_router(state: GraphState):
    if state.valid:
        return {'desicion':'valid'}
    
    if state.requires_user_clarification:
        return {'desicion' : 'ask_user', 'message_to_user':state.message_to_user}
    
    if state.fixed_manually:        
        return {'desicion':'critic'}

    return {'desicion':'END'}


def ask_user_node(state: GraphState):
    print('SUSPENDING GRAPH FOR USER EXECUTION')
    return {
        "message_to_user": state.message_to_user,
        "requires_user_clarification": True,
        "awaiting_user_input": True,
        "interrupt": "user_input"
    }

def routing(state:GraphState):
    return state.desicion


def allow_execution(state:GraphState):
    print(' ')
    print('ALLOWING FINAL EXECUTION AFTER REVISING THE PLAN')
    print(state.plan)
    print(' ')

    return state

intent_llm = llm.with_structured_output(IntentSchema)

def clarification_node(state: GraphState):

    # Build the corrected query
    new_query = state.clean_query + " " + state.clarification
    
    # Reset flags
    return {
        "query": new_query,
        "requires_user_clarification": False,
        "awaiting_user_input": False,
        "desicion": "planner"
    }

def chat_node(state: GraphState):

    user_msg = state.query

    # 1. Update memory
    print(' ')
    print('CONVERSATION SO FAR')
    print(state.conversation_history)
    print(' ')

    new_history = state.conversation_history + [
        {"role": "user", "content": user_msg}
    ]
    # 2. If system is expecting clarification → skip classification
    # 3. Classify intent normally
    intent = intent_llm.invoke(
        CHAT_INTENT_PROMPT.format(user_query=user_msg))
    print(intent)
    # 4. Route based on intent
    if intent.intent == "plan":
        return {"desicion": "planner", 'conversation_history':new_history}
    
    if intent.intent == "chat":
        return {"desicion": "chat"}

    return {
        "conversation_history": new_history
    }

def chat_reply(state:GraphState):
    reply = llm.invoke(
        f"You are a helpful assistant. Respond naturally to: {state.query}"
    ).content

    return {
        "final_response": reply
    }

#refactor react agents (architecture/tools)

def context_node(state:GraphState):
    user_query, conversational_history=state.query, state.conversation_history
    clean_query=llm.with_structured_output(ContextSchema).invoke(CONTEXT_AGENT_PROMPT.format(user_msg=user_query, conversation_history=conversational_history))
    print(' ')
    print(state.desicion)
    
    print(' ')
    print(conversational_history)
    print('REWRITTEN QUERY')
    print(clean_query)
    cl_query=clean_query.clean_query
    desicion=state.desicion
    print(' ')

    return {"clean_query": cl_query, 'desicion':desicion}