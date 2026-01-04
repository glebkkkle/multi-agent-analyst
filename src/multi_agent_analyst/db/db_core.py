import io
import re
import hashlib
from contextlib import contextmanager
from typing import Dict, List, Iterator, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool

from src.backend.config import settings


APP_DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:"
    f"{settings.postgres_password}"
    f"@{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

# Main app engine (privileged)
engine = create_engine(
    APP_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)

# Base agent engine for SET ROLE operations
# Uses the main user but will SET ROLE to thread-specific roles
agent_base_engine = create_engine(
    APP_DATABASE_URL,
    poolclass=NullPool,  # Don't pool since each connection uses different roles
)


SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]+$")

def validate_identifier(name: str, param_name: str) -> str:
    if not SAFE_IDENTIFIER.match(name or ""):
        raise ValueError(f"Invalid {param_name}: '{name}'")
    if len(name) > 63:
        raise ValueError(f"{param_name} too long (max 63 chars)")
    return name

def get_thread_role_name(thread_id: str) -> str:
    """Generate the role name for a thread."""
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    return f"thread_{safe_thread_id}"

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
# Thread initialization (ONE TIME per thread)
# ----------------------------

def initialize_thread(thread_id: str) -> None:
    """
    ONE-TIME setup for a new thread:
    1. Create the schema
    2. Create a dedicated role for this thread
    3. Grant the role access to its schema
    
    This is called once when a thread is created and never needs to be repeated.
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    with engine.begin() as conn:
        # Create schema
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_thread_id}"'))
        
        # Create role (if it doesn't exist)
        # Note: CREATE ROLE IF NOT EXISTS requires PostgreSQL 9.6+
        # For older versions, catch the exception
        try:
            conn.execute(text(f'CREATE ROLE "{role_name}" NOLOGIN'))
        except Exception as e:
            if "already exists" not in str(e):
                raise
        
        # Grant usage on schema
        conn.execute(text(f'GRANT USAGE ON SCHEMA "{safe_thread_id}" TO "{role_name}"'))
        
        # Grant all privileges on all current and future tables in the schema
        conn.execute(text(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "{safe_thread_id}" TO "{role_name}"'))
        conn.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{safe_thread_id}" GRANT ALL PRIVILEGES ON TABLES TO "{role_name}"'))
        
        # Grant all privileges on all current and future sequences
        conn.execute(text(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "{safe_thread_id}" TO "{role_name}"'))
        conn.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{safe_thread_id}" GRANT ALL PRIVILEGES ON SEQUENCES TO "{role_name}"'))
        
        # Allow the main app user to SET ROLE to this thread role
        conn.execute(text(f'GRANT "{role_name}" TO "{settings.postgres_user}"'))

def cleanup_thread(thread_id: str) -> None:
    """
    Clean up a thread's resources (optional, for thread deletion).
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    with engine.begin() as conn:
        # Drop schema and all contents
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{safe_thread_id}" CASCADE'))
        
        # Drop the role
        conn.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))

# ----------------------------
# Secure agent execution (NO LOCKS NEEDED!)
# ----------------------------

@contextmanager
def get_thread_conn(thread_id: str) -> Iterator[Connection]:
    """
    Get a connection that operates as the thread's role.
    
    SECURITY MODEL:
    - Connection assumes the thread-specific role using SET ROLE
    - PostgreSQL enforces all permission checks
    - No JIT grants/revokes needed
    - Multiple threads can run concurrently
    - Completely isolated by PostgreSQL's native permission system
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    with agent_base_engine.connect() as conn:
        with conn.begin():
            # Assume the thread's role - THIS IS THE SECURITY BOUNDARY
            conn.execute(text(f'SET ROLE "{role_name}"'))
            
            # Set search path for convenience
            conn.execute(text(f'SET search_path TO "{safe_thread_id}", public'))
            
            # Enforce RLS where present (defense in depth)
            conn.execute(text("SET row_security = on"))
            
            # Set thread_id for any RLS policies
            conn.execute(text("SET app.current_thread_id = :tid"), {"tid": safe_thread_id})
            
            # Prevent runaway queries
            conn.execute(text("SET statement_timeout = '30s'"))
            
            yield conn
            
            # Transaction is automatically committed or rolled back
            # Role automatically resets when connection is returned to pool

# For backward compatibility with the old API
@contextmanager
def agent_execution(thread_id: str) -> Iterator[None]:
    """
    Legacy compatibility wrapper.
    With per-thread roles, this is just a no-op context manager.
    """
    validate_identifier(thread_id, "thread_id")
    yield

# ----------------------------
# Legacy compatibility helpers
# ----------------------------

def ensure_schema(schema_name: str) -> None:
    """
    Ensure a schema exists.
    Note: For new code, use initialize_thread() instead.
    """
    safe_schema = validate_identifier(schema_name, "schema_name")
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))

def grant_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    """
    Legacy no-op - access is now permanent via roles.
    """
    pass

def revoke_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    """
    Legacy no-op - access is now permanent via roles.
    """
    pass

@contextmanager
def global_agent_lock() -> Iterator[None]:
    """
    Legacy no-op - no longer needed with per-thread roles.
    """
    yield

# ----------------------------
# Data management (unchanged)
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