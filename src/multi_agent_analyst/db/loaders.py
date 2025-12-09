# src/multi_agent_analyst/db/loaders.py
import pandas as pd
# from src.multi_agent_analyst.db.db2 import conn
from src.multi_agent_analyst.db.db_core import get_conn
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

def load_user_tables(thread_id: str):
    """
    Load metadata for all tables in the user's schema.
    Returns ONLY:
        - table name
        - list of columns
        - list of types

    NO data samples are returned.
    """

    conn = get_conn()
    schema = thread_id

    # 1. Get all table names
    query_tables = f"""
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname = '{schema}';
    """

    table_names = pd.read_sql(query_tables, conn)['tablename'].tolist()

    output = {}

    for table in table_names:
        try:
            # 2. Fetch column metadata for each table
            query_columns = f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = '{table}';
            """

            column_info = pd.read_sql(query_columns, conn)

            columns = column_info['column_name'].tolist()

            output[table] = {
                "description": f"User table '{table}'",
                "columns": columns,
            }

        except Exception as e:
            output[table] = {
                "description": f"Could not load metadata for table '{table}'",
                "error": str(e),
                "columns": None,
            }

    return output
