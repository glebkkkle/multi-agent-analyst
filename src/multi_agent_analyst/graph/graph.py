from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from src.multi_agent_analyst.graph.nodes import planner_node, critic, router_node, routing, revision_node, revision_router, allow_execution, summarizer_node, chat_node, chat_reply, ask_user_node, clarification_node
from src.multi_agent_analyst.graph.states import GraphState


graph = StateGraph(GraphState)

graph.add_node('planner', planner_node)
graph.add_node('critic', critic)
graph.add_node('revision_node', revision_node)
graph.add_node('revision_router', revision_router) 
graph.add_node('finalizer', allow_execution)
graph.add_node('router_node', router_node)
graph.add_node('summarizer_node', summarizer_node)
graph.add_node('ask_user', ask_user_node)
graph.add_node('chat_node', chat_node)
graph.add_node('chat_reply', chat_reply)
graph.add_node("clarification_node", clarification_node)


graph.set_entry_point('chat_node')
graph.add_conditional_edges('chat_node', routing, {'chat':'chat_reply', 'planner': 'planner', 'clarification':'ask_user'})
graph.add_edge('ask_user', 'clarification_node')
graph.add_edge('clarification_node', 'planner')

graph.add_edge('planner', 'critic')
graph.add_edge('critic', 'revision_node')
graph.add_edge('revision_node', 'revision_router')
graph.add_conditional_edges('revision_router', routing, {'valid':'finalizer', 'ask_user':'ask_user', 'critic':'critic', 'END':END})
graph.add_edge('finalizer', 'router_node')
graph.add_edge('router_node', 'summarizer_node')


# graph.add_node('router', router_node)
# graph.add_node('finalizer', finalizer_node)


# graph.set_entry_point('planner')
# graph.add_edge('planner','router')
# graph.add_edge('router', 'finalizer')
# graph.add_edge('finalizer', END)


g = graph.compile(checkpointer=InMemorySaver())

thread_id = "user-123"

events = g.stream(
    {"query": "visualize profit,units_sold, revenue"},
    config={"configurable": {"thread_id": thread_id}}
)

for event in events:
    print(event)
    print(' ')

    # STOP HERE if interruption requested
    if "ask_user" in event:
        print("❗ WAITING FOR USER CLARIFICATION")
        print("MESSAGE_TO_USER:", event["ask_user"]["message_to_user"])
        break

new_state=g.update_state({'configurable':{'thread_id':thread_id}}, values={'clarification':'with a pie chart'})

events = g.stream(
    None,
    config=new_state
)

for event in events:
    print(' ')
    print('RESUMING GRAPH')
    print(' ')
    print(event)
    