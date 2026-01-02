import io
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import re
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from src.backend.config import settings

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
    f"postgresql://agent_role:"
    f"{settings.agent_role_password}"
    f"@{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}",
    pool_size=10,
    max_overflow=20,
)

 
@contextmanager
def get_conn():
    """
    App-level privileged connection.
    Used for schema creation, COPY, metadata tables.
    """
    conn = engine.raw_connection()
    try:
        yield conn
    finally:
        conn.close()

from sqlalchemy import text 

from contextlib import contextmanager

@contextmanager
def get_thread_conn(thread_id: str):
    """
    Agent-only, thread-isolated connection.
    """
    with agent_engine.begin() as conn:
        conn.execute(
            text(f'SET LOCAL search_path TO "{thread_id}", pg_catalog')
        )
        yield conn


def create_table(schema_name, table_name, columns):
    cols = ", ".join([f'"{col}" {dtype}' for col, dtype in columns.items()])
    sql = f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" ({cols});'
    
    with engine.begin() as conn:
        conn.execute(text(sql))

def copy_dataframe(schema_name, table_name, df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.copy_expert(
                f'COPY "{schema_name}"."{table_name}" FROM STDIN WITH CSV',
                csv_buffer
            )
        conn.commit()

def register_data_source(thread_id: str, table_name: str, filename: str):
    sql = """
        INSERT INTO data_sources (thread_id, table_name, original_filename)
        VALUES (:thread_id, :table_name, :filename)
        RETURNING id;
    """
    with engine.begin() as conn:
        result = conn.execute(text(sql), {
            "thread_id": thread_id, 
            "table_name": table_name, 
            "filename": filename
        })
        return result.fetchone()[0]

def ensure_schema(schema_name):
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";'))

SAFE_IDENTIFIER = re.compile(r'^[a-zA-Z0-9_-]+$')

def validate_identifier(name: str, param_name: str) -> str:
    """Validate that an identifier is safe to use in SQL."""
    if not SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Invalid {param_name}: '{name}'")
    if len(name) > 63:
        raise ValueError(f"{param_name} too long (max 63 chars)")
    return name

def initialize_thread(thread_id: str):
    """Initialize a new thread with its own isolated schema."""
    safe_thread_id = validate_identifier(thread_id, "thread_id")

    with engine.begin() as conn:
        # Create schema
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_thread_id}"'))

        # No implicit access
        conn.execute(text(f'REVOKE ALL ON SCHEMA "{safe_thread_id}" FROM PUBLIC'))

        # Agent can use the schema
        conn.execute(text(f'GRANT USAGE ON SCHEMA "{safe_thread_id}" TO agent_role'))

        # Existing tables
        conn.execute(text(f'''
            GRANT SELECT, INSERT, UPDATE, DELETE
            ON ALL TABLES IN SCHEMA "{safe_thread_id}"
            TO agent_role
        '''))

        # Existing sequences
        conn.execute(text(f'''
            GRANT USAGE, SELECT, UPDATE
            ON ALL SEQUENCES IN SCHEMA "{safe_thread_id}"
            TO agent_role
        '''))

        # Future tables
        conn.execute(text(f'''
            ALTER DEFAULT PRIVILEGES IN SCHEMA "{safe_thread_id}"
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO agent_role
        '''))

        # Future sequences
        conn.execute(text(f'''
            ALTER DEFAULT PRIVILEGES IN SCHEMA "{safe_thread_id}"
            GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO agent_role
        '''))
