from src.multi_agent_analyst.graph.graph import g as compiled_graph
from src.backend.storage.redis_client import redis_client
from src.backend.storage.thread_store import RedisSessionStore, RedisThreadMeta

session_store = RedisSessionStore(redis_client)
thread_meta = RedisThreadMeta(redis_client)

def _run_graph(thread_id: str, session_id: str, requires_user_clarification: bool):

    session = session_store.get_session(thread_id, session_id)

    events = compiled_graph.stream(
        {
            "query": session.canonical_query,
            "thread_id": thread_id,
            "session_id": session_id,
            "requires_user_clarification": requires_user_clarification,
        },
        config={"configurable": {"thread_id": thread_id}}
    )

    for event in events:
        if "ask_user" in event:
            session_store.mark_waiting(thread_id, session_id)
            return {
                "status": "needs_clarification",
                "message_to_user": event["ask_user"]["message_to_user"],
            }

    # ✅ graph completed
    session_store.mark_completed(thread_id, session_id)
    thread_meta.clear_active_session(thread_id)

    final = event.get("summarizer_node", {})
    return {
        "status": "completed",
        "result": final,
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
