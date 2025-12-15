from src.multi_agent_analyst.graph.graph import g as compiled_graph

def run_initial_graph(thread_id: str, message: str):
    events = compiled_graph.stream(
        {
            "query": message,
            "thread_id": thread_id,
            "requires_user_clarification": False,
        },
        config={"configurable": {"thread_id": thread_id}}
    )

    for event in events:
        if "ask_user" in event:
            return {
                "status": "needs_clarification",
                "message_to_user": event["ask_user"]["message_to_user"],
            }

    final = event.get("summarizer_node", {})
    return {"status": "completed", "result": final}


def clarify_graph(thread_id: str, clarification: str):
    events = compiled_graph.stream(
        {
            "clarification": clarification,
            "requires_user_clarification": True,
            "thread_id": thread_id,
        },
        config={"configurable": {"thread_id": thread_id}}
    )

    for event in events:
        if "ask_user" in event:
            return {
                "status": "needs_clarification",
                "message_to_user": event["ask_user"]["message_to_user"],
            }

    final = event.get("summarizer_node", {})
    return {"status": "completed", "result": final}

#MUST fix the resuming logic completely