from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
import io
import pandas as pd
import bcrypt
import time
import json 
import redis
from uuid import uuid4
from datetime import timedelta
from contextlib import asynccontextmanager
from dotenv import load_dotenv
# DB Imports
from src.multi_agent_analyst.db.db_core import (
    engine, 
    get_conn, 
    create_table, 
    copy_dataframe, 
    register_data_source, 
    ensure_schema
)
from psycopg2 import OperationalError
from src.multi_agent_analyst.db.loaders import load_user_tables
from src.multi_agent_analyst.utils.utils import object_store

# Internal App Imports
from src.backend.langgraph_runner.executor import run_initial_graph, clarify_graph
from data.converter.reader import read_file
from data.converter.infer_schema import infer_schema
from src.backend.auth import create_access_token, Token, get_current_user, CurrentUser
from src.backend.storage.thread_store import RedisSessionStore, RedisThreadMeta
from src.multi_agent_analyst.db.conversation_store import ThreadConversationStore
from src.backend.storage.redis_client import checkpointer
from pydantic import BaseModel
from src.backend.storage.execution_store import RedisExecutionStore

conversation_store = ThreadConversationStore()
MAX_CLARIFICATIONS = 3
MESSAGE_LIMIT = 4
QUOTA_WINDOW_SECONDS= 24 * 60 * 60

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup    
    try:
        checkpointer.setup()
        print("✅ LangGraph checkpointer indexes created")
    except Exception as e:
        print(f"⚠️ Checkpointer setup warning: {e}")
    
    yield

app = FastAPI(lifespan=lifespan)

def check_postgres():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        return True
    except Exception:
        return False

def check_redis(redis_client):
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def check_checkpointer():
    try:
        # Minimal sanity check — no mutation
        return checkpointer is not None
    except Exception:
        return False


def check_object_store():
    try:
        # Test save + read
        obj_id = object_store.save({"health": "ok"})
        _ = object_store.get(obj_id)
        return True
    except Exception:
        return False


@app.get("/api/health")
def health_check():
    components = {
        "postgres": "ok" if check_postgres() else "down",
        "redis": "ok" if check_redis(redis_client) else "down",
        "checkpointer": "ok" if check_checkpointer() else "down",
        "object_store": "ok" if check_object_store() else "down",
    }

    if any(v == "down" for v in components.values()):
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "components": components
            }
        )

    return {
        "status": "ok",
        "components": components
    }


from src.backend.config import settings

redis_client = redis.Redis(
    host=settings.redis_app_host,
    port=settings.redis_app_port,
    db=settings.redis_app_db,
    decode_responses=True
)
session_store = RedisSessionStore(redis_client)
thread_meta = RedisThreadMeta(redis_client)
execution_store=RedisExecutionStore(redis_client)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# --- Routes ---
from fastapi.responses import RedirectResponse
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return FileResponse("src/frontend/index.html")

@app.get("/app", response_class=HTMLResponse)
async def app_page():
    return FileResponse("src/frontend/app.html")


@app.get("/api/execution/{session_id}")
async def get_execution(session_id: str, after_seq: int = 0, user: CurrentUser = Depends(get_current_user)):
    snap = execution_store.get_snapshot(session_id, after_seq=after_seq)
    if snap is None:  # ✅ ONLY None means unknown
        raise HTTPException(404, "Unknown session")
    return snap

from fastapi import BackgroundTasks

@app.post("/api/message")
async def handle_message(payload: dict, background_tasks: BackgroundTasks, user: CurrentUser = Depends(get_current_user)):
    
    thread_id = user.thread_id
    used = thread_meta.incr_message_quota(thread_id, QUOTA_WINDOW_SECONDS)
    if used > MESSAGE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"Beta limit reached. You can send up to {MESSAGE_LIMIT} messages.",
                "limit": MESSAGE_LIMIT,
                "used": used,
            },
        )
    print(' ')
    print(f'QUATA USED :{used}')
    print(' ')



    message = payload["message"]
    session_id = uuid4().hex

    session_store.create_session(thread_id, session_id, message)
    thread_meta.set_active_session(thread_id, session_id)

    # Start execution asynchronously
    background_tasks.add_task(run_initial_graph, thread_id, session_id)

    # Store convo context (optional: mark running)
    conv_context = {"content": message, "created_at": time.time(), "status": "running"}
    conversation_store.append(thread_id=thread_id, role="user", content=json.dumps(conv_context))

    return {"session_id": session_id, "status": "processing"}


@app.post("/api/clarify")
async def handle_clarify(payload: dict, background_tasks: BackgroundTasks, user: CurrentUser = Depends(get_current_user)):
    thread_id = user.thread_id
    clarification = payload["clarification"]

    session_id = thread_meta.get_active_session(thread_id)
    if not session_id:
        raise HTTPException(400, "No active session")

    session = session_store.get_session(thread_id, session_id)
    if session.status != "waiting":
        raise HTTPException(400, "Session is not waiting for clarification")

    count = session_store.append_clarification(thread_id, session_id, clarification)

    if count >= MAX_CLARIFICATIONS:
        session_store.mark_aborted(thread_id, session_id)
        thread_meta.clear_active_session(thread_id)
        execution_store.mark_aborted(session_id, "I’m still missing required information. Please rephrase your request.")
        return {"session_id": session_id, "status": "aborted"}
    
    background_tasks.add_task(clarify_graph, thread_id, session_id)

    conv_context = {"content": clarification, "created_at": time.time(), "status": "running"}
    conversation_store.append(thread_id=thread_id, role="user", content=json.dumps(conv_context))

    return {"session_id": session_id, "status": "processing"}


@app.get("/api/object/{object_id}")
async def get_object(object_id: str):
    obj = object_store.get(object_id)
    if hasattr(obj, "read"):
        obj.seek(0)
        return StreamingResponse(obj, media_type="image/png")
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    return obj

@app.post("/api/upload_data")
async def upload_data(file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user)):
    thread_id = user.thread_id
    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX accepted")

    raw = await file.read()
    df = read_file(io.BytesIO(raw), override_filename=filename)
    if df.empty:
        raise HTTPException(status_code=400, detail="File is empty")

    schema_dict = infer_schema(df)
    table_name = filename.split(".")[0]

    # Use the pool-safe context manager
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM data_sources WHERE thread_id = %s AND original_filename = %s LIMIT 1;", (thread_id, filename))
            if cur.fetchone():
                raise HTTPException(400, detail=f"File '{filename}' already uploaded.")

            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s);", (thread_id, table_name))
            if cur.fetchone()[0]:
                raise HTTPException(400, detail=f"Table '{table_name}' already exists.")

    ensure_schema(thread_id)
    create_table(thread_id, table_name, schema_dict)
    copy_dataframe(thread_id, table_name, df)
    source_id = register_data_source(thread_id=thread_id, table_name=table_name, filename=filename)

    return {"status": "success", "rows": len(df), "table_name": table_name}

router = APIRouter(prefix="/api")

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login", response_model=Token)
def login(data: LoginRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash, thread_id FROM users WHERE email = %s",
                (data.email,)
            )
            row = cur.fetchone()

    if not row or not bcrypt.checkpw(data.password.encode(), row[2].encode()):
        raise HTTPException(401, "Invalid email or password")

    access_token = create_access_token(
        data={"user_id": row[0], "thread_id": row[3]},
        expires_delta=timedelta(days=1),
    )

    return {"access_token": access_token}

@app.get("/register", response_class=HTMLResponse)
def register_page():
    return FileResponse("src/frontend/register.html")

@router.post("/register_raw", response_model=Token)
def register_raw(data: LoginRequest):
    email = data.email.strip().lower()
    password = data.password.strip()

    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Check existing user
            cur.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            if cur.fetchone():
                raise HTTPException(400, "Email already registered")

            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            # Generate thread_id up front
            cur.execute("SELECT nextval(pg_get_serial_sequence('users','id'))")
            user_id = cur.fetchone()[0]
            thread_id = f"thread_{user_id}"

            # Insert fully valid row
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, thread_id)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, email, hashed, thread_id),
            )

            # Create schema
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{thread_id}"')

            conn.commit()

    return Token(
        access_token=create_access_token(
            data={"user_id": user_id, "thread_id": thread_id},
            expires_delta=timedelta(days=1),
        )
    )



@app.get("/api/data_sources")
def list_data_sources(user: CurrentUser = Depends(get_current_user)):
    thread_id = user.thread_id
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name;", (thread_id,))
            tables = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT table_name, original_filename FROM data_sources WHERE thread_id = %s", (thread_id,))
            meta_dict = {m[0]: m[1] for m in cur.fetchall()}

    response = [{"table_name": t, "filename": meta_dict.get(t, t)} for t in tables]
    return {"sources": response}

app.include_router(router)