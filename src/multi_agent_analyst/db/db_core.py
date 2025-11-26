import psycopg2
import psycopg2.extras
import io
from datetime import datetime

DB_CONFIG = {
    "dbname": "multi_analyst",
    "user": "glebkle",
    "password": "123",
    "host": "localhost",
    "port": 5432
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)

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


def register_data_source(table_name: str, filename: str, schema_name:str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO data_sources (table_name, original_filename, schema_name)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (table_name, filename, schema_name))
            new_id = cur.fetchone()[0]
        conn.commit()
    return new_id


def ensure_schema(schema_name):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        conn.commit()