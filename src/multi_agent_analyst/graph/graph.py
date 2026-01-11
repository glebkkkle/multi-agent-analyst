from langgraph.graph import StateGraph, END
from src.multi_agent_analyst.graph.nodes import planner_node, router_for, final_result_node, critic, router_node, routing,clean_query, revision_node, revision_router, allow_execution, execution_error_node, chat_node, chat_reply, ask_user_node
from src.multi_agent_analyst.graph.states import GraphState
from src.backend.storage.redis_client import checkpointer

graph = StateGraph(GraphState)

graph.add_node('planner', planner_node)
graph.add_node('critic', critic)
graph.add_node('revision_node', revision_node)
graph.add_node('revision_router', revision_router) 
graph.add_node('finalizer', allow_execution)
graph.add_node('router_node', router_node)
graph.add_node('ask_user', ask_user_node)
graph.add_node('chat_node', chat_node)
graph.add_node('chat_reply', chat_reply)
graph.add_node('execution_error', execution_error_node)
graph.add_node('clean_query', clean_query)
graph.add_node('final_result_node', final_result_node)

clean_query_map = {
    'chat_node': 'chat_node',
    'abort': 'final_result_node', 
}
graph.set_entry_point('clean_query')

graph.add_conditional_edges(
    'clean_query',
    router_for(clean_query_map),
    clean_query_map
)

chat_map = {
    'chat': 'chat_reply',
    'planner': 'planner',
    'ask_user': 'ask_user',
    'abort': 'final_result_node',
    'error': 'execution_error',
}

graph.add_conditional_edges(
    'chat_node',
    router_for(chat_map),
    chat_map
)

graph.add_edge('chat_reply', 'final_result_node')

graph.add_edge('planner', 'critic')

critic_map = {
    'True': 'finalizer',
    'False': 'revision_node',
    'error': 'execution_error',
}

graph.add_conditional_edges(
    'critic',
    router_for(critic_map),
    critic_map
)

graph.add_edge('revision_node', 'revision_router')
revision_map = {
    'valid': 'finalizer',
    'ask_user': 'ask_user',
    'critic': 'critic',
    'END': END,
    'error': 'execution_error',
}

graph.add_conditional_edges(
    'revision_router',
    router_for(revision_map),
    revision_map
)
graph.add_edge('ask_user', END)

graph.add_edge('finalizer', 'router_node')

router_map = {
    'ok': 'final_result_node',
    'error': 'execution_error',
}

graph.add_conditional_edges(
    'router_node',
    router_for(router_map),
    router_map
)


graph.add_edge('final_result_node', END)
graph.add_edge('execution_error', END)

g = graph.compile(checkpointer=checkpointer)

