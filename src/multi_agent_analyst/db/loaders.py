# src/multi_agent_analyst/db/loaders.py
import pandas as pd
# from src.multi_agent_analyst.db.db2 import conn
from src.multi_agent_analyst.db.db_core import get_conn
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

def load_user_tables(thread_id: str):
    conn = get_conn()
    schema = thread_id

    query_tables = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}';
    """

    tables = pd.read_sql(query_tables, conn)['table_name'].tolist()

    output = {}

    for table in tables:
        try:
            # get column info
            col_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = '{table}';
            """
            col_df = pd.read_sql(col_query, conn)

            column_map = {
                str(row["column_name"]): str(row["data_type"])
                for _, row in col_df.iterrows()
            }

            # get row count
            row_count = pd.read_sql(
                f'SELECT COUNT(*) FROM "{schema}"."{table}"',
                conn
            ).iloc[0, 0]

            # force to python int
            row_count = int(row_count)

            output[table] = {
                "description": f"User table '{table}'",
                "columns": column_map,
                "row_count": row_count,
            }

        except Exception as e:
            output[table] = {
                "description": f"Error reading table '{table}'",
                "columns": {},
                "row_count": None,
                "error": str(e)
            }

    return output

