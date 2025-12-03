from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from src.multi_agent_analyst.graph.nodes import planner_node, critic, router_node, routing, revision_node, revision_router, allow_execution, summarizer_node, chat_node, chat_reply, ask_user_node, clarification_node, context_node
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
graph.add_node('context_node', context_node)

graph.set_entry_point('chat_node')
graph.add_edge('chat_node', 'context_node')
graph.add_conditional_edges('context_node', routing, {'chat':'chat_reply', 'planner': 'planner'})
graph.add_edge('chat_reply', 'summarizer_node')

graph.add_edge('planner', 'critic')
graph.add_edge('critic', 'revision_node')
graph.add_edge('revision_node', 'revision_router')
graph.add_conditional_edges('revision_router', routing, {'valid':'finalizer', 'ask_user':'ask_user', 'critic':'critic', 'END':END})
graph.add_edge('ask_user', 'clarification_node')
graph.add_edge('clarification_node', 'planner')

graph.add_edge('finalizer', 'router_node')
graph.add_edge('router_node', 'summarizer_node')
graph.add_edge('summarizer_node', END)

g = graph.compile(checkpointer=InMemorySaver())

#FIX CHAT NODES
