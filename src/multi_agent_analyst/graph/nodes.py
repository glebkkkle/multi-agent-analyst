from langchain_core.messages import AIMessage
import json
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
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
from src.multi_agent_analyst.prompts.chat.chat_reply_prompt import CHAT_REPLY_PROMPT

ollama_llm=ChatOllama(model='gpt-oss:20b', temperature=0)
llm=ChatOpenAI(model='gpt-4.1-mini')

#maybe use sql tool to only identify the appropriate database, and use select columns to format the db appropriately for later use
#might have to fix the planner 


def planner_node(state: GraphState):
    #perhaps fix the planner so outputs are [smth.example_obj_id]
    print('🧠CREATING EXECUTION PLAN: ')
    print(' ')
    query = state.clean_query or state.query
    plan = llm.with_structured_output(Plan).invoke(
        GLOBAL_PLANNER_PROMPT.format(query=query)
    )

    print(plan, "\n")
    return {"plan": plan}

def critic(state: GraphState):
    print("\n🧠CRITIC RECEIVED PLAN\n")

    response = llm.with_structured_output(CriticStucturalResponse).invoke(
        CRITIC_PROMPT.format(
            query=state.clean_query,
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

    query=state.clean_query
    result = controller_agent.invoke({
        "messages": [
            {"role": "user", "content": query}
        ]
    })
    r=result['structured_response']
    print(r)
    exception=r.exception
    summary=r.summary
    obj_id=r.object_id
    # print(r['observation'])

    if exception is not None:
        print(True)
    else:
        print(False)
        
    return {
        'exception':exception,
        "final_obj_id": obj_id,
        "summary": summary
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

    return {
        "message_to_user": state.message_to_user,
        "requires_user_clarification": True,
        "interrupt": "user_input",
    }
def routing(state:GraphState):
    return state.desicion


def allow_execution(state:GraphState):
    return state

intent_llm = llm.with_structured_output(IntentSchema)

def clarification_node(state: GraphState):
    new_query = (state.clean_query or "") + " " + state.clarification

    return {
        "query": new_query.strip(),
        "requires_user_clarification": False,
        "desicion": "planner",
    }

def chat_node(state: GraphState):
    user_msg = state.query
    current_tables.setdefault(state.thread_id, load_user_tables(state.thread_id))

    new_history = state.conversation_history + [
        {"role": "user", "content": user_msg}
    ]

    intent = intent_llm.invoke(
        CHAT_INTENT_PROMPT.format(user_query=user_msg)
    )

    if intent.intent == "plan":
        return {"desicion": "planner", "conversation_history": new_history}

    if intent.intent == "chat":
        return {"desicion": "chat", "conversation_history": new_history}

    return {"conversation_history": new_history}

def chat_reply(state: GraphState):
    reply = llm.invoke(CHAT_REPLY_PROMPT.format(user_query=state.query, conversation_history=state.conversation_history, data_list=state.data_samples))
    return {"final_response": reply.content}
#refactor react agents (architecture/tools)

def context_node(state: GraphState):
    clean = llm.with_structured_output(ContextSchema).invoke(
        CONTEXT_AGENT_PROMPT.format(
            user_msg=state.query,
            conversation_history=state.conversation_history,
        )
    ).clean_query

    return {"clean_query": clean, "desicion": state.desicion}


#TIGHTEN THE PROMPTING for everything

