from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.backend.langgraph_runner.executor import run_initial_graph, resume_graph

app = FastAPI()

# Allow frontend JS to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/frontend", StaticFiles(directory="src/frontend", html=True), name="frontend")

@app.post("/api/message")
async def handle_message(payload: dict):
    thread_id = payload["thread_id"]
    message = payload["message"]
    return run_initial_graph(thread_id, message)


@app.post("/api/clarify")
async def handle_clarify(payload: dict):
    thread_id = payload["thread_id"]
    clarification = payload["clarification"]
    return resume_graph(thread_id, clarification)

from fastapi.responses import StreamingResponse
from src.multi_agent_analyst.utils.utils import object_store

@app.get("/api/object/{object_id}")
async def get_object(object_id: str):
    obj = object_store.get(object_id)

    # Case 1: BytesIO buffer → image
    if hasattr(obj, "read"):
        obj.seek(0)
        return StreamingResponse(obj, media_type="image/png")

    # Case 2: DataFrame → return JSON
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
    except:
        pass

    # Case 3: raw python object
    return obj