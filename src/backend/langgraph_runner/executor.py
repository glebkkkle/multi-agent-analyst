from src.multi_agent_analyst.graph.graph import g as compiled_graph

def run_initial_graph(thread_id: str, message: str):
    events = compiled_graph.stream(
        {"query": message},
        config={"configurable": {"thread_id": thread_id}}
    )

    final = None
    for event in events:
        final = event
        if "ask_user" in event:
            return {
                "status": "needs_clarification",
                "message_to_user": event["ask_user"]["message_to_user"],
            }

    return {
        "status": "completed",
        "result": final,
    }


def resume_graph(thread_id: str, clarification: str):
    new_state = compiled_graph.update_state(
        {"configurable": {"thread_id": thread_id}},
        values={"clarification": clarification},
    )

    events = compiled_graph.stream(None, config=new_state)

    final = None
    for event in events:
        final = event

    return {
        "status": "completed",
        "result": final,
    }
