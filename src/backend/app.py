from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.backend.langgraph_runner.executor import run_initial_graph, clarify_graph
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
import bcrypt
from src.multi_agent_analyst.db.db_core import conn 
from fastapi import Form
from src.multi_agent_analyst.db.loaders import load_user_tables
from fastapi.responses import HTMLResponse, FileResponse
from src.backend.auth import create_access_token, Token
from datetime import timedelta
from src.backend.auth import get_current_user, CurrentUser
from fastapi import Depends
import redis
import time
import json 
from contextlib import asynccontextmanager
from uuid import uuid4
from src.backend.storage.thread_store import RedisSessionStore, RedisThreadMeta
from src.multi_agent_analyst.db.conversation_store  import ThreadConversationStore
from src.backend.storage.redis_client import checkpointer

conversation_store = ThreadConversationStore()

MAX_CLARIFICATIONS=3

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    checkpointer.setup()
    yield


redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
session_store = RedisSessionStore(redis_client)
thread_meta = RedisThreadMeta(redis_client)

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("src/frontend/register.html")

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return FileResponse("src/frontend/index.html")

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

# app.mount("/frontend", StaticFiles(directory="src/frontend"), name="static")
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

#some issues with the database, more tools are needed, prettier visualization, more concise summary

#redis, rag later

@app.post("/api/message")
async def handle_message(payload: dict, user: CurrentUser = Depends(get_current_user)):
    thread_id = user.thread_id
    message = payload["message"]

    session_id = uuid4().hex
    session_store.create_session(thread_id, session_id, message)

    thread_meta.set_active_session(thread_id, session_id)

    result = run_initial_graph(
        thread_id=thread_id,
        session_id=session_id,
    )
    if result['status'] == 'completed':
        conv_context={"content":message, "created_at":time.time(), "status":'completed'}
        conversation_store.append(
            thread_id=thread_id,
            role="user",
            content=json.dumps(conv_context),
        )
    elif result['status'] == 'needs_clarification':
        conv_context={"content":message, "created_at":time.time(), "status":'clarification_required'}
        conversation_store.append(
            thread_id=thread_id,
            role="user",
            content=json.dumps(conv_context),
        )

    return {
        "session_id": session_id,
        **result,
    }


@app.get("/app", response_class=HTMLResponse)
async def app_page():
    return FileResponse("src/frontend/app.html")


@app.post("/api/clarify")
async def handle_clarify(payload: dict, user: CurrentUser = Depends(get_current_user)):
    thread_id = user.thread_id
    clarification = payload["clarification"]

    # 1️⃣ Fetch ACTIVE session
    session_id = thread_meta.get_active_session(thread_id)
    if not session_id:
        raise HTTPException(400, "No active session")

    session = session_store.get_session(thread_id, session_id)
    if session.status != "waiting":
        raise HTTPException(400, "Session is not waiting for clarification")

    # 2️⃣ Append clarification to SESSION state
    count = session_store.append_clarification(thread_id, session_id, clarification)

    if count >= MAX_CLARIFICATIONS:
        session_store.mark_aborted(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)

        abort_msg = (
            "I’m still missing required information. "
            "Please rephrase your request as a new message."
        )

    
        return {
            "status": "aborted",
            "message_to_user": abort_msg,
        }

    result = clarify_graph(
        thread_id=thread_id,
        session_id=session_id,
    )

    if result['status'] == 'completed':
        conv_context={"content":clarification, "created_at":time.time(), "status":'completed'}
        conversation_store.append(
            thread_id=thread_id,
            role="user",
            content=json.dumps(conv_context),
        )
    elif result['status'] == 'needs_clarification':
        conv_context={"content":clarification, "created_at":time.time(), "status":'clarification_required'}
        conversation_store.append(
            thread_id=thread_id,
            role="user",
            content=json.dumps(conv_context),
        )

    return {
        "session_id": session_id,
        **result,
    }


from fastapi.responses import StreamingResponse
from src.multi_agent_analyst.utils.utils import object_store

@app.get("/api/object/{object_id}")
async def get_object(object_id: str):
    obj = object_store.get(object_id)
    print(obj)
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
    file: UploadFile = File(...),    
    user: CurrentUser = Depends(get_current_user),
):
    thread_id = user.thread_id

    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id missing")

    filename = file.filename.lower()

    # Validate extension
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX accepted")

    # Read file bytes
    raw = await file.read()
    buffer = io.BytesIO(raw)

    df = read_file(buffer, override_filename=filename)
    if df.empty:
        raise HTTPException(status_code=400, detail="File is empty")

    schema_dict = infer_schema(df)
    table_name = filename.split(".")[0]


    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1
            FROM data_sources
            WHERE thread_id = %s
            AND original_filename = %s
            LIMIT 1;
        """, (thread_id, filename))
        file_exists = cur.fetchone()

    if file_exists:
        raise HTTPException(
            status_code=400,
            detail=f"File '{filename}' was already uploaded earlier."
        )


    # ------------------------------------
    # 🔥 Duplicate TABLE check (schema-level)
    # ------------------------------------
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            );
        """, (thread_id, table_name))
        table_exists = cur.fetchone()[0]

    if table_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' already exists."
        )

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

@router.post("/login_raw", response_model=Token)
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
    access_token = create_access_token(
        data={"user_id": user_id, "thread_id": thread_id},
        expires_delta=timedelta(minutes=60 * 24),
    )
    print("SENDING TOKEN:", access_token)

    return Token(access_token=access_token)

@router.post("/register_raw", response_model=Token)
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
        cur.close()
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
    cur.close()

    # ✅ Auto-login: issue JWT
    access_token = create_access_token(
        data={"user_id": user_id, "thread_id": thread_id},
        expires_delta=timedelta(minutes=60 * 24),
    )

    return Token(access_token=access_token)

@app.get("/api/data_sources")
def list_data_sources(user: CurrentUser = Depends(get_current_user)):

    thread_id = user.thread_id

    with conn.cursor() as cur:

        # 1. Load all table names inside the user's Postgres schema
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name;
        """, (thread_id,))
        tables = [row[0] for row in cur.fetchall()]

        # 2. Load metadata from data_sources table filtered by thread_id
        cur.execute("""
            SELECT table_name, original_filename, uploaded_at
            FROM data_sources
            WHERE thread_id = %s
            ORDER BY uploaded_at DESC;
        """, (thread_id,))
        meta = cur.fetchall()

    # Convert metadata rows into dict for fast lookup
    meta_dict = {
        m[0]: {
            "filename": m[1],
            "uploaded_at": m[2]
        }
        for m in meta
    }

    # Build frontend response
    response = []
    for tbl in tables:
        print(meta_dict.get(tbl, {}).get('filename'), tbl)

        response.append({
            "table_name": tbl,
            "filename": meta_dict.get(tbl, {}).get("filename", tbl),
        })

    return {"sources": response}




app.include_router(router)