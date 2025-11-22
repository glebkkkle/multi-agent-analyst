# tests/manual_test.py

from src.multi_agent_analyst.graph.graph import g
from langgraph.graph import END

thread_id = "test-thread-1"

def run_user_message(msg):
    print(f"\n>>> USER: {msg}\n")

    events = g.stream(
        {"query": msg},
        config={"configurable": {"thread_id": thread_id}}
    )

    for e in events:
        print("EVENT:", e)

        # If the graph requests clarification:
        if "ask_user" in e:
            print("\n⛔ ASK USER FOR CLARIFICATION")
            print("MESSAGE:", e["ask_user"]["message_to_user"])
            return {
                "type": "ask_user",
                "msg": e["ask_user"]["message_to_user"]
            }

        # If graph finishes normally:
        if "summarizer_node" in e:
            print("\n✅ FINAL RESPONSE READY")
            print(e["summarizer_node"])
            return {
                "type": "final",
                "data": e["summarizer_node"]
            }

    return {"type": "unknown"}


def send_clarification(clarification_text):
    print(f"\n>>> USER CLARIFICATION: {clarification_text}\n")

    new_state = g.update_state(
        {"configurable": {"thread_id": thread_id}},
        values={"clarification": clarification_text}
    )

    events = g.stream(None, config=new_state)

    for e in events:
        print("EVENT:", e)

        if "summarizer_node" in e:
            print("\n🟢 FINAL RESULT AFTER CLARIFICATION")
            return {
                "type": "final",
                "data": e["summarizer_node"]
            }

    return {"type": "unknown"}

# -------------------------------------------------------------------------
# ACTUAL TEST
# -------------------------------------------------------------------------

step1 = run_user_message("visualize profit, units_sold, revenue")

if step1["type"] == "ask_user":
    # pretend user answers:
    step2 = send_clarification("with a pie chart")
    print("\n\nFINAL RESULT:", step2)

else:
    print("\n\nFINAL RESULT:", step1)
