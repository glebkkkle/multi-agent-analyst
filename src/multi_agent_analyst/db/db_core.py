import io
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# 1. Create the persistent Engine
# This manages the pool of connections automatically.
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from src.backend.config import settings

if settings.database_url:
    DATABASE_URL = settings.database_url
else:
    DATABASE_URL = (
        f"postgresql://{settings.postgres_user}:"
        f"{settings.postgres_password}@"
        f"{settings.postgres_host}:"
        f"{settings.postgres_port}/"
        f"{settings.postgres_db}"
    )

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)
@contextmanager 
def get_conn():
    """Context manager that yields a connection and returns it to the pool."""
    conn = engine.raw_connection()
    try:
        yield conn # 3. 'Yield' the connection to the 'with' block
    finally:
        # 4. This ensures the connection is ALWAYS returned to the pool
        conn.close() 

from sqlalchemy import text 

def get_thread_conn(thread_id):
    """Returns a SQLAlchemy Connection object with the search_path set."""
    conn = engine.connect() 
    
    if thread_id:
        # Use .execute(text(...)) for SQLAlchemy compatibility
        conn.execute(text(f'SET search_path TO "{thread_id}", public;'))
        
    return conn

def create_table(schema_name, table_name, columns):
    cols = ", ".join([f'"{col}" {dtype}' for col, dtype in columns.items()])
    sql = f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" ({cols});'
    
    # Using 'with' on the engine directly is cleaner for simple executions
    with engine.begin() as conn:
        conn.execute(text(sql))

def copy_dataframe(schema_name, table_name, df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    # We get a raw connection for the copy_expert feature
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.copy_expert(
                f'COPY "{schema_name}"."{table_name}" FROM STDIN WITH CSV',
                csv_buffer
            )
        conn.commit()
    finally:
        conn.close() # Returns it to the pool

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