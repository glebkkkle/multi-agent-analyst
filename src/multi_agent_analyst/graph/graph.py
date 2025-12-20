from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from src.multi_agent_analyst.graph.nodes import planner_node, final_result_node, critic, router_node, routing,clean_query, revision_node, revision_router, allow_execution, execution_error_node,summarizer_node, chat_node, chat_reply, ask_user_node
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
graph.add_node('execution_error', execution_error_node)
graph.add_node('clean_query', clean_query)
graph.add_node('final_result_node', final_result_node)


graph.set_entry_point('clean_query')
graph.add_edge('clean_query', 'chat_node')
graph.add_conditional_edges('chat_node', routing, {'chat':'chat_reply', 'planner': 'planner', 'ask_user':'ask_user',})
graph.add_edge('chat_reply', 'final_result_node')

graph.add_edge('planner', 'critic')
graph.add_conditional_edges('critic', routing, {'True':'finalizer', 'False':'revision_node'})

graph.add_edge('revision_node', 'revision_router')
graph.add_conditional_edges('revision_router', routing, {'valid':'finalizer', 'ask_user':'ask_user', 'critic':'critic', 'END':END})
graph.add_edge('ask_user', END)

graph.add_edge('finalizer', 'router_node')
graph.add_conditional_edges('router_node', routing,{'ok':'final_result_node', 'error':'execution_error'})
graph.add_edge('final_result_node', END)
graph.add_edge('execution_error', END)

g = graph.compile(checkpointer=InMemorySaver())


#decrease latency by improving the graph structure 

