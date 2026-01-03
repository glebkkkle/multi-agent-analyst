from src.multi_agent_analyst.graph.graph import g as compiled_graph
from src.backend.storage.redis_client import redis_client
from src.backend.storage.thread_store import RedisSessionStore, RedisThreadMeta
from src.multi_agent_analyst.db.conversation_store import ThreadConversationStore
from src.backend.storage.emitter import set_emitter, emit
from src.backend.storage.execution_store import RedisExecutionStore
from src.backend.storage.emitter import set_emitter, emit, clear_emitter
import time 
conversation_store = ThreadConversationStore()
session_store = RedisSessionStore(redis_client)
thread_meta = RedisThreadMeta(redis_client)
execution_store=RedisExecutionStore(redis_client)

def _run_graph(thread_id: str, session_id: str, requires_user_clarification: bool, init_execution_store: bool):
    MAX_EXECUTION_SECONDS = 180  
    # Only init the execution_store once per session (new message)
    if init_execution_store:
        execution_store.init_session(session_id)
    else:
        execution_store.mark_running(session_id, reset_clock=True)

    def milestone_emitter(msg: str) -> None:
        execution_store.add_milestone(session_id, msg)

    set_emitter(milestone_emitter)
    try:
        
        session = session_store.get_session(thread_id, session_id)

        conversation_history = conversation_store.get_recent(
            thread_id=thread_id,
            max_age_seconds=300,
            limit=3,
        )

        events = compiled_graph.stream(
            {
                "query": session.canonical_query,
                "thread_id": thread_id,
                "session_id": session_id,
                "requires_user_clarification": requires_user_clarification,
                "conversation_history": conversation_history,
            },
            config={"configurable": {"thread_id": thread_id}},
        )

        last_event = None
        emit("Analyzing query…")
        for event in events:
            snap = execution_store.get_snapshot(session_id)
            started_at = snap.get("started_at", time.time())

            if time.time() - started_at > MAX_EXECUTION_SECONDS:
                session_store.mark_completed(thread_id, session_id)
                thread_meta.clear_active_session(thread_id)

                execution_store.mark_aborted(
                    session_id,
                    "Execution timed out. Please try a simpler query."
                )
                return {
                    "status": "aborted",
                    "final_response": "Execution timed out. Please try a simpler query."
                }
            
            last_event = event
            # 🟡 clarification requested
            if "ask_user" in event:
                msg = event["ask_user"]["message_to_user"]

                session_store.mark_waiting(thread_id, session_id)

                # UI sees: status=waiting + final_response=prompt
                execution_store.mark_waiting(session_id, msg)
                emit("Waiting for clarification.")

                return {"status": "waiting", "final_response": msg}

        # Safety guard
        if last_event is None:
            session_store.mark_completed(thread_id, session_id)
            thread_meta.clear_active_session(thread_id)

            execution_store.mark_failed(session_id, "The system produced no output.")
            return {"status": "failed", "final_response": "The system produced no output."}

        # execution error path
        if "execution_error" in last_event:
            session_store.mark_completed(thread_id, session_id)
            thread_meta.clear_active_session(thread_id)

            err = str(last_event["execution_error"])
            execution_store.mark_failed(session_id, err)
            return {"status": "failed", "final_response": f"Internal error: {err}"}

        # success path
        if "final_result_node" in last_event:
            session_store.mark_completed(thread_id, session_id)
            thread_meta.clear_active_session(thread_id)

            # Your final_result_node looks like dict with final_response etc.
            result = last_event["final_result_node"]

            execution_store.mark_done(session_id, {
                "final_response": result.get("final_response"),
                "final_obj_id": result.get("final_obj_id"),
                "final_table_shape": result.get("final_table_shape"),
            })
            emit("Completed.")

            return {"status": "completed", "final_response": result.get("final_response") }

        # unexpected terminal state
        session_store.mark_completed(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)

        execution_store.mark_failed(session_id, "Unexpected terminal state.")
        return {"status": "failed", "final_response": "The system ended in an unexpected state."}

    finally:
        # Hygiene: clear emitter so this task doesn't leak it
        clear_emitter()

def run_initial_graph(thread_id: str, session_id: str):
    return _run_graph(thread_id, session_id, requires_user_clarification=False, init_execution_store=True)

def clarify_graph(thread_id: str, session_id: str):
    # do NOT init store again; keep milestones and seq
    return _run_graph(thread_id, session_id, requires_user_clarification=True, init_execution_store=False)
