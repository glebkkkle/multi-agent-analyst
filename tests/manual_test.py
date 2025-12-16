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

# step1 = run_user_message("visualize profit, units_sold, revenue")

# if step1["type"] == "ask_user":
#     # pretend user answers:
#     step2 = send_clarification("with a pie chart")
#     print("\n\nFINAL RESULT:", step2)

# else:
#     print("\n\nFINAL RESULT:", step1)


# from src.backend.storage.redis_client import redis_client
# from src.backend.storage.thread_store import RedisThreadStore

# store = RedisThreadStore(redis_client)

# t = store.create_if_missing("thread_test", "analyze sales")
# print(t)

# t = store.append_to_query("thread_test", "only 2024")
# print(t.canonical_query)

# t = store.increment_clarifications("thread_test")
# print("clarifications:", t)

# t = store.set_waiting("thread_test", "Which metric?")
# print(t.status, t.last_system_message)

from src.backend.storage.redis_client import redis_client
from src.backend.storage.thread_store import RedisThreadStore

def run():
    store = RedisThreadStore(redis_client)

    thread_id = "thread_small_test"

    # cleanup from previous runs
    redis_client.delete(f"thread:{thread_id}")

    print("\n--- CREATE THREAD ---")
    t = store.get_or_create(thread_id)
    print(t)

    assert t.canonical_query == ""

    print("\n--- FIRST QUERY ---")
    t = store.append_query(thread_id, "analyze sales")
    print(t.canonical_query)
    assert t.canonical_query == "analyze sales"

    print("\n--- FIRST CLARIFICATION ---")
    t = store.append_query(thread_id, "only 2024")
    print(t.canonical_query)
    assert t.canonical_query == "analyze sales only 2024"

    print("\n--- SECOND CLARIFICATION ---")
    t = store.append_query(thread_id, "monthly breakdown")
    print(t.canonical_query)
    assert t.canonical_query == "analyze sales only 2024 monthly breakdown"

    print("\n--- HISTORY ---")
    for h in t.history:
        print(h)

    assert len(t.history) == 3


    print("\n✅ ALL TESTS PASSED")

    print(store.get_or_create(thread_id))
