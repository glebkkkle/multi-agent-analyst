# src/multi_agent_analyst/db/loaders.py
import pandas as pd
from src.multi_agent_analyst.db.connection import get_conn
from src.multi_agent_analyst.db.db2 import conn

def load_sample_tables():
    """Load sample rows from each table (first 5 rows)."""

    conn = get_conn()

    tables = [
        "website_traffic",
        "sales",
        "customer_feedback",
        "inventory",
        "campaign_analysis",
    ]

    output = {}

    for table in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn).head()
            output[table] = {
                "description": f"SQL table with information about {table.replace('_', ' ')}",
                "columns": df
            }
            print(df)
        except Exception as e:
            # If table doesn't exist, skip instead of crashing
            output[table] = {
                "description": f"Table '{table}' not found",
                "columns": None
            }

    conn.close()
    return output


def load_user_tables(thread_id: str):
    """
    Dynamically load all tables inside the user's schema
    and return a dict containing sample rows + descriptions.
    """

    schema = thread_id
    
    query_tables = f"""
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname = '{schema}';
    """

    table_names = pd.read_sql(query_tables, conn)['tablename'].tolist()

    output = {}

    for table in table_names:
        try:
            # 2. Load sample rows (first 5)
            df = pd.read_sql(f'SELECT * FROM "{schema}"."{table}" LIMIT 5', conn)

            output[table] = {
                "description": f"User table '{table}'",
                "sample": df
            }

        except Exception as e:
            output[table] = {
                "schema": schema,
                "description": f"Error reading table '{table}'",
                "error": str(e),
                "sample": None
            }

    # conn.close()
    return output

