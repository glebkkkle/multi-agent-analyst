from fastapi import FastAPI
from src.backend.langgraph_runner.executor import run_initial_graph, resume_graph

app = FastAPI()

@app.post("/api/message")
async def handle_message(payload: dict):
    thread_id = payload["thread_id"]
    message = payload["message"]
    return run_initial_graph(thread_id, message)

@app.post("/api/clarify")
async def handle_clarification(payload: dict):
    thread_id = payload["thread_id"]
    clarification = payload["clarification"]
    return resume_graph(thread_id, clarification)