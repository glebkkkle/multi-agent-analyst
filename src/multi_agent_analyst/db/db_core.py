import psycopg2
import io
from datetime import datetime

import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

def get_thread_conn(thread_id):
    conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)
    cur = conn.cursor()

    if thread_id is not None:
        cur.execute(f"SET search_path TO {thread_id}, public;")

    return conn


conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)

def get_conn():
    conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)
    return conn 

def create_table(schema_name, table_name, columns):
    cols = ", ".join([f'"{col}" {dtype}' for col, dtype in columns.items()])
    sql = f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" ({cols});'

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

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
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO data_sources (thread_id, table_name, original_filename)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (thread_id, table_name, filename))
            new_id = cur.fetchone()[0]
        conn.commit()
    return new_id


def ensure_schema(schema_name):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        conn.commit()