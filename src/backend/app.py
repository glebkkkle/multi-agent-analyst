from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.backend.langgraph_runner.executor import run_initial_graph, resume_graph
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from data.converter.reader import read_file
from data.converter.infer_schema import infer_schema
import io
from data.converter.reader import read_file
from data.converter.infer_schema import infer_schema
from src.multi_agent_analyst.db.db_core import create_table, copy_dataframe, register_data_source, ensure_schema
from fastapi import UploadFile, File, HTTPException
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
import bcrypt
from src.multi_agent_analyst.db.db2 import conn 
from fastapi import Form

app = FastAPI()

# Allow frontend JS to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.mount("/frontend", StaticFiles(directory="src/frontend", html=True), name="frontend")
# app.mount("/", StaticFiles(directory="src/frontend", html=True), name="frontend")

app.mount("/frontend", StaticFiles(directory="src/frontend"), name="frontend")

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

@app.post("/api/upload_data")
async def upload_data(
    thread_id: str = Form(...),
    file: UploadFile = File(...),    
):
    print("Received thread_id:", thread_id)
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id missing")

    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX accepted")

    raw = await file.read()
    buffer = io.BytesIO(raw)

    df = read_file(buffer, override_filename=filename)
    if df.empty:
        raise HTTPException(status_code=400, detail="File is empty")

    schema_dict = infer_schema(df)
    table_name = filename.split(".")[0]

    ensure_schema(thread_id)
    create_table(thread_id, table_name, schema_dict)
    copy_dataframe(thread_id, table_name, df)

    source_id = register_data_source(
        thread_id=thread_id,
        table_name=table_name,
        filename=filename
    )

    return {
        "status": "success",
        "thread_id": thread_id,
        "table_name": table_name,
        "source_id": source_id,
        "rows": len(df)
    }

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login_raw")
def login_raw(data: LoginRequest):
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, email, password_hash, thread_id 
        FROM users WHERE email = %s
    """, (data.email,))
    
    row = cur.fetchone()
    
    if not row:
        raise HTTPException(401, "Invalid email or password")
    
    user_id, email, password_hash, thread_id = row
    
    # verify password
    if not bcrypt.checkpw(data.password.encode(), password_hash.encode()):
        raise HTTPException(401, "Invalid email or password")
    
    # success
    return {
        "user_id": user_id,
        "email": email,
        "thread_id": thread_id
    }


@router.post("/register_raw")
def register_raw(data: LoginRequest):
    email = data.email.strip().lower()
    password = data.password.strip()

    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    cur = conn.cursor()

    # Check if user already exists
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    exists = cur.fetchone()

    if exists:
        raise HTTPException(400, "Email already registered")

    # Hash pw
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Temporary thread placeholder
    cur.execute("""
        INSERT INTO users(email, password_hash, thread_id)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (email, hashed, "temp"))
    
    user_id = cur.fetchone()[0]

    # Create thread schema name
    thread_id = f"thread_{user_id}"

    # Update thread_id
    cur.execute("UPDATE users SET thread_id = %s WHERE id = %s", (thread_id, user_id))

    # Create schema
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {thread_id}")

    conn.commit()

    return {
        "user_id": user_id,
        "email": email,
        "thread_id": thread_id
    }


app.include_router(router)