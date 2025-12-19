from langchain_core.messages import AIMessage
import json
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import io
from src.multi_agent_analyst.db.loaders import load_user_tables
import base64
from src.multi_agent_analyst.react_agents.controller_agent import controller_agent
from src.multi_agent_analyst.utils.utils import object_store, execution_list, current_tables
from src.multi_agent_analyst.graph.states import GraphState, CriticStucturalResponse, DAGPlan,RevisionState, IntentSchema, ContextSchema
from src.multi_agent_analyst.prompts.graph.planner import PLANNER_PROMPT
from src.multi_agent_analyst.prompts.graph.critic import CRITIC_PROMPT
from src.multi_agent_analyst.prompts.graph.revision import PLAN_REVISION_PROMPT
from src.multi_agent_analyst.prompts.graph.summarizer import SUMMARIZER_PROMPT
from src.multi_agent_analyst.prompts.chat.intent_classifier import  INTENT_CLASSIFIER_PROMPT, intent_class, new_intent
from src.multi_agent_analyst.prompts.chat.context_agent import cleaned_query
from src.multi_agent_analyst.prompts.chat.chat_reply_prompt import CHAT_REPLY_PROMPT

ollama_llm=ChatOllama(model='gpt-oss:20b', temperature=0)
llm=ChatOpenAI(model='gpt-4.1-mini')

#maybe use sql tool to only identify the appropriate database, and use select columns to format the db appropriately for later use
#might have to fix the planner 


def planner_node(state: GraphState):
    #perhaps fix the planner so outputs are [smth.example_obj_id]
    print('🧠CREATING EXECUTION PLAN: ')
    print(' ')
    print('QUERY')
    print(state.query)
    plan = llm.with_structured_output(DAGPlan).invoke(
        PLANNER_PROMPT.format(schemas=state.dataset_schemas,query=state.query)
    )
    print(plan, "\n")
    return {"plan": plan}

def critic(state: GraphState):
    print("\n🧠CRITIC RECEIVED PLAN\n")

    response = llm.with_structured_output(CriticStucturalResponse).invoke(
        CRITIC_PROMPT.format(
            schemas=state.dataset_schemas,
            query=state.query,
            plan=state.plan
        )
    )
    return {
        "critic_output": response,
        "message_to_user": response.message_to_user,
        "requires_user_clarification": response.requires_user_input,
        "valid": response.valid,
    }

def revision_node(state: GraphState):
    print("🧠REVISOR RECEIVED PLAN\n")

    response = llm.with_structured_output(RevisionState).invoke(
        PLAN_REVISION_PROMPT.format(
            critic_output=state.critic_output,
            initial_plan=state.plan,
            user_query=state.clean_query
        )
    )

    return {
        "plan": response.fixed_plan,
        "fixed_manually": response.fixed_manually,
        "message_to_user": state.message_to_user,  # stays for ask_user
        "valid": state.valid
    }

def router_node(state: GraphState):
    current_tables.setdefault(state.thread_id, load_user_tables(state.thread_id))
    try:
        result = controller_agent.invoke({
            "messages": [
                {"role": "user", "content": str(state.plan)}
            ]
        })
    except Exception as e:
        print(str(e))
        return {"desicion":'error', "execution_exception":str(e)}
    
    print(result)
    last = [m for m in result["messages"] if isinstance(m, AIMessage)][-1].content
    d = json.loads(last)
    
    return {
        "desicion":"ok",
        "final_obj_id": d["object_id"],
        "summary": d["summary"]
    }

def summarizer_node(state: GraphState):
    if state.desicion == 'chat':
        return {'final_response':state.final_response, "image_base64":None, 'final_obj_id':None}

    else:
        obj = object_store.get(state.final_obj_id)

        image_base64 = None
        if isinstance(obj, io.BytesIO):
            image_base64 = base64.b64encode(obj.getvalue()).decode()

        model = ChatOllama(model="gpt-oss:20b", temperature=0)
        final_text = model.invoke(
            SUMMARIZER_PROMPT.format(
                user_query=state.query,
                obj=obj,
                summary=state.summary
            )
        ).content

        execution_list.execution_log_list.clear()
        print(' ')
        print('RESPONSE TO THE USER:')
        print(' ')
        print(final_text)
        return {
            "final_response": final_text,
            "image_base64": image_base64,
            "final_obj_id": state.final_obj_id
        }

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

def ask_user_node(state: GraphState):
    print("SUSPENDING GRAPH FOR USER INPUT")
    print(state.message_to_user)
    
    return {
        "message_to_user": state.message_to_user,
        "requires_user_clarification": True,
    }
def routing(state:GraphState):
    print(state.desicion)
    return state.desicion

def allow_execution(state:GraphState):
    return state

intent_llm = llm.with_structured_output(IntentSchema)

from pydantic import BaseModel

class CleanQueryState(BaseModel):
    planner_query:str


lm = ChatOpenAI(model="gpt-5-mini").with_structured_output(IntentSchema)

def chat_node(state: GraphState):
    user_msg = state.query
    print(user_msg)
    schemas = load_user_tables(state.thread_id)
    current_tables.setdefault(state.thread_id, schemas)
    
    print(state.conversation_history)

    intent = lm.invoke(
        new_intent.format(
            user_query=user_msg,
            data_schemas=schemas,
            conversation_history=state.conversation_history
        )
    )
    print(intent)
    print(' ')

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
            "retrival_mode":intent.result_mode
        }

    if intent.intent == "chat":
        new_history=state.conversation_history + [{"role":'user', "content":user_msg}]
        return {
            "desicion": "chat",
            "conversation_history": new_history,
            "dataset_schemas": schemas,
        }

def chat_reply(state: GraphState):
    reply = llm.invoke(CHAT_REPLY_PROMPT.format(user_query=state.query, conversation_history=state.conversation_history, data_list=state.dataset_schemas))
    return {"final_response": reply.content}

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

#carefully using the information from the conversational history and only executing a current task, nothing else.


def clean_query(state:GraphState):
    conv_history=state.conversation_history
    print(conv_history)
    response=llm.with_structured_output(CleanQueryState).invoke(cleaned_query.format(original_query=state.query, session_context=conv_history))
    print(' ')
    print(cleaned_query.format(original_query=state.query, session_context=conv_history))
    print(' ')
    print(response.planner_query)
    return {"query":response.planner_query}


# def context_node(state: GraphState):
#     print(state.desicion)
#     clean = llm.with_structured_output(ContextSchema).invoke(
#         CONTEXT_AGENT_PROMPT.format(
#             user_msg=state.query,
#             conversation_history=state.conversation_history,
#         )
#     ).clean_query

#     return {"clean_query": clean, "desicion": state.desicion}


#chat node should be more strict on whats allowed to propagate and whats not 
#should be more informative and now that its a unit bounded to the project

#simply appending the clarification seems fraguile, needs a fix. 
