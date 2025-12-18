from src.multi_agent_analyst.graph.graph import g as compiled_graph
from src.backend.storage.redis_client import redis_client
from src.backend.storage.thread_store import RedisSessionStore, RedisThreadMeta
from src.multi_agent_analyst.db.conversation_store import ThreadConversationStore

conversation_store = ThreadConversationStore()

session_store = RedisSessionStore(redis_client)
thread_meta = RedisThreadMeta(redis_client)

def _run_graph(thread_id: str, session_id: str, requires_user_clarification: bool):

    session = session_store.get_session(thread_id, session_id)

    conversation_history = conversation_store.get_recent(
        thread_id=thread_id,
        limit=6,
    )
    events = compiled_graph.stream(
        {
            "query": session.canonical_query,
            "thread_id": thread_id,
            "session_id": session_id,
            "requires_user_clarification": requires_user_clarification,
            "conversation_history":conversation_history
        },
        config={"configurable": {"thread_id": thread_id}}
    )

    last_event = None

    for event in events:
        last_event = event

        # 🟡 clarification requested
        if "ask_user" in event:
            session_store.mark_waiting(thread_id, session_id)
            return {
                "status": "needs_clarification",
                "message_to_user": event["ask_user"]["message_to_user"],
            }

    # 🔒 Safety guard
    if last_event is None:
        session_store.mark_completed(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)
        return {
            "status": "error",
            "result": {
                "final_response": "The system produced no output.",
                "final_obj_id": None,
                "image_base64": None,
            },
        }

    # 🔴 execution error path
    if "execution_error" in last_event:
        session_store.mark_completed(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)
        return {
            "status": "error",
            "result": last_event["execution_error"],
        }

    # 🟢 success path
    if "summarizer_node" in last_event:
        session_store.mark_completed(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)
        return {
            "status": "completed",
            "result": last_event["summarizer_node"],
        }

    # ❌ unexpected terminal state
    session_store.mark_completed(thread_id, session_id)
    thread_meta.clear_active_session(thread_id)
    return {
        "status": "error",
        "result": {
            "final_response": "The system ended in an unexpected state.",
            "final_obj_id": None,
            "image_base64": None,
        },
    }


def run_initial_graph(thread_id: str, session_id: str):
    """
    Run graph for a NEW session.
    """
    return _run_graph(
        thread_id=thread_id,
        session_id=session_id,
        requires_user_clarification=False,
    )


def clarify_graph(thread_id: str, session_id: str):
    """
    Resume graph for an EXISTING session after clarification.
    """
    return _run_graph(
        thread_id=thread_id,
        session_id=session_id,
        requires_user_clarification=True,
    )
