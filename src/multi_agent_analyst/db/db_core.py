import io
import re
import hashlib
from contextlib import contextmanager
from typing import Dict, List, Iterator, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from src.backend.config import settings

# ----------------------------
# Engines
# ----------------------------

APP_DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:"
    f"{settings.postgres_password}"
    f"@{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

engine = create_engine(
    APP_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)

agent_engine = create_engine(
    f"postgresql://data_agent:"
    f"{settings.data_agent_password}"
    f"@{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}",
    pool_size=10,
    max_overflow=20,
)

# ----------------------------
# Identifier validation
# ----------------------------

SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]+$")

def validate_identifier(name: str, param_name: str) -> str:
    if not SAFE_IDENTIFIER.match(name or ""):
        raise ValueError(f"Invalid {param_name}: '{name}'")
    if len(name) > 63:
        raise ValueError(f"{param_name} too long (max 63 chars)")
    return name

# ----------------------------
# Privileged raw connection (COPY)
# ----------------------------

@contextmanager
def get_conn():
    """
    App-level privileged raw connection.
    Used for COPY, etc.
    """
    conn = engine.raw_connection()
    try:
        yield conn
    finally:
        conn.close()

# ----------------------------
# Thread schema management (privileged)
# ----------------------------

def initialize_thread(thread_id: str) -> None:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    with engine.begin() as conn:
        conn.execute(text("SELECT initialize_thread_schema(:thread_id)"), {"thread_id": safe_thread_id})

def grant_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    if conn is None:
        with engine.begin() as c:
            c.execute(text("SELECT grant_thread_access(:thread_id)"), {"thread_id": safe_thread_id})
    else:
        conn.execute(text("SELECT grant_thread_access(:thread_id)"), {"thread_id": safe_thread_id})

def revoke_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    if conn is None:
        with engine.begin() as c:
            c.execute(text("SELECT revoke_thread_access(:thread_id)"), {"thread_id": safe_thread_id})
    else:
        conn.execute(text("SELECT revoke_thread_access(:thread_id)"), {"thread_id": safe_thread_id})

# ----------------------------
# Advisory lock (prevents concurrent thread grants)
# ----------------------------

def _advisory_key(name: str) -> int:
    """
    Convert a string into a stable 64-bit signed int key for pg_advisory_lock.
    """
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    # take first 8 bytes as signed int64
    return int.from_bytes(digest[:8], "big", signed=True)

@contextmanager
def global_agent_lock() -> Iterator[None]:
    """
    Global lock: REQUIRED when using a single LOGIN role (data_agent) and JIT GRANT/REVOKE.
    Ensures only one agent run is active at a time.
    """
    lock_key = _advisory_key("global_data_agent_lock")

    with engine.begin() as conn:
        # Block until acquired
        conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": lock_key})
        try:
            yield
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key})

# ----------------------------
# Secure agent execution boundary
# ----------------------------

@contextmanager
def agent_execution(thread_id: str) -> Iterator[None]:
    """
    HARD security boundary:
      - Acquire a global lock (prevents concurrent grants)
      - Grant access to exactly one thread schema
      - Ensure revoke ALWAYS happens
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")

    with global_agent_lock():
        # Use a single privileged transaction for grant/revoke operations
        with engine.begin() as priv_conn:
            grant_thread_access(safe_thread_id, conn=priv_conn)

        try:
            yield
        finally:
            # Always revoke, even if the agent crashes/throws
            with engine.begin() as priv_conn:
                revoke_thread_access(safe_thread_id, conn=priv_conn)

# ----------------------------
# Agent connection (restricted)
# ----------------------------

@contextmanager
def get_thread_conn(thread_id: str) -> Iterator[Connection]:
    """
    Agent-only connection.
    SECURITY NOTE:
      - search_path is for convenience only (not a security boundary)
      - privileges enforce isolation
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")

    with agent_engine.begin() as conn:
        # convenience for unqualified table names
        conn.execute(text(f'SET LOCAL search_path TO "{safe_thread_id}"'))

        # enforce RLS where present
        conn.execute(text("SET LOCAL row_security = on;"))

        # set the thread_id for your RLS policies (data_sources/thread_messages)
        conn.execute(text("SET LOCAL app.current_thread_id = :tid"), {"tid": safe_thread_id})

        # prevent runaway queries
        conn.execute(text("SET LOCAL statement_timeout = '30s';"))

        yield conn

# ----------------------------
# Data operations (privileged)
# ----------------------------

def create_table(schema_name: str, table_name: str, columns: Dict[str, str]) -> None:
    safe_schema = validate_identifier(schema_name, "schema_name")
    safe_table = validate_identifier(table_name, "table_name")
    cols = ", ".join([f'"{col}" {dtype}' for col, dtype in columns.items()])
    sql = f'CREATE TABLE IF NOT EXISTS "{safe_schema}"."{safe_table}" ({cols});'
    with engine.begin() as conn:
        conn.execute(text(sql))

def copy_dataframe(schema_name: str, table_name: str, df: pd.DataFrame) -> None:
    safe_schema = validate_identifier(schema_name, "schema_name")
    safe_table = validate_identifier(table_name, "table_name")

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.copy_expert(
                f'COPY "{safe_schema}"."{safe_table}" FROM STDIN WITH CSV',
                csv_buffer
            )
        conn.commit()

def register_data_source(thread_id: str, table_name: str, filename: str) -> int:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    safe_table = validate_identifier(table_name, "table_name")

    sql = """
        INSERT INTO data_sources (thread_id, table_name, original_filename)
        VALUES (:thread_id, :table_name, :filename)
        RETURNING id;
    """
    with engine.begin() as conn:
        res = conn.execute(text(sql), {
            "thread_id": safe_thread_id,
            "table_name": safe_table,
            "filename": filename
        })
        return int(res.fetchone()[0])

def list_thread_tables(thread_id: str) -> List[str]:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """), {"schema_name": safe_thread_id})
        return [r[0] for r in res.fetchall()]

def get_table_info(thread_id: str, table_name: str) -> List[Dict[str, str]]:
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    safe_table = validate_identifier(table_name, "table_name")
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema_name
              AND table_name = :table_name
            ORDER BY ordinal_position;
        """), {"schema_name": safe_thread_id, "table_name": safe_table})

        return [
            {"column": r[0], "type": r[1], "nullable": (r[2] == "YES")}
            for r in res.fetchall()
        ]
