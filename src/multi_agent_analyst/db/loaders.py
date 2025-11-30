# src/multi_agent_analyst/db/loaders.py
import pandas as pd
# from src.multi_agent_analyst.db.db2 import conn
from src.multi_agent_analyst.db.db_core import get_conn

def load_user_tables(thread_id: str):
    """
    Dynamically load all tables inside the user's schema
    and return a dict containing sample rows + descriptions.
    """
    conn=get_conn()

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

