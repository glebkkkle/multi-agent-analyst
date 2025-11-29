from src.multi_agent_analyst.graph.graph import g as compiled_graph

def run_initial_graph(thread_id: str, message: str):
    events = compiled_graph.stream(
        {"query": message, 'thread_id':thread_id},
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

    # Extract data from summarizer_node
    summarizer_data = final.get("summarizer_node", {})
    
    return {
        "status": "completed",
        "result": {
            "summarizer_node": {
                "final_response": summarizer_data.get("final_response"),
                "image_base64": summarizer_data.get("image_base64"),
                "final_obj_id": summarizer_data.get("final_obj_id")
            }
        }
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

    # Extract data from summarizer_node
    summarizer_data = final.get("summarizer_node", {})
    
    return {
        "status": "completed",
        "result": {
            "summarizer_node": {
                "final_response": summarizer_data.get("final_response"),
                "image_base64": summarizer_data.get("image_base64"),
                "final_obj_id": summarizer_data.get("final_obj_id")
            }
        }
    }