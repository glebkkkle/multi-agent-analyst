from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.backend.langgraph_runner.executor import run_initial_graph, resume_graph
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from data.converter.reader import read_file
from data.converter.infer_schema import infer_schema
import io
import pandas as pd

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



from data.converter.reader import read_file
from data.converter.infer_schema import infer_schema
from src.multi_agent_analyst.db.db_core import create_table, copy_dataframe, register_data_source, ensure_schema
from fastapi import UploadFile, File, HTTPException

@app.post("/api/upload_data")
async def upload_data(
    file: UploadFile = File(...),
    thread_id: str = "thread_1"  # ✅ NEW: thread_id parameter
):
    filename = file.filename.lower()

    # Validate file extension
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX accepted")

    # Read raw bytes
    raw = await file.read()
    buffer = io.BytesIO(raw)

    # Convert to DataFrame
    df = read_file(buffer, override_filename=filename)
    if df.empty:
        raise HTTPException(status_code=400, detail="File is empty")

    # Detect column types
    schema_dict = infer_schema(df)

    # Clean table name (no extension)
    table_name = filename.split(".")[0]

    ensure_schema(thread_id)

    create_table(thread_id, table_name, schema_dict)

    copy_dataframe(thread_id, table_name, df)

    source_id = register_data_source(
        table_name=table_name,
        filename=filename,
        schema_name=thread_id 
    )

    return {
        "status": "success",
        "thread_id": thread_id,
        "table_name": table_name,
        "source_id": source_id,
        "schema": thread_id,
        "rows": len(df)
    }