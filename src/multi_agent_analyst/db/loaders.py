import pandas as pd
from src.multi_agent_analyst.db.db_core import engine # Import the engine directly

def load_user_tables(thread_id: str):
    schema = thread_id

    query_tables = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}';
    """

    tables = pd.read_sql(query_tables, engine)['table_name'].tolist()

    output = {}
    for table in tables:
        try:
            col_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = '{table}';
            """
            col_df = pd.read_sql(col_query, engine)

            column_map = {
                str(row["column_name"]): str(row["data_type"])
                for _, row in col_df.iterrows()
            }

            row_count = pd.read_sql(
                f'SELECT COUNT(*) FROM "{schema}"."{table}"',
                engine
            ).iloc[0, 0]

            output[table] = {
                "description": f"User table '{table}'",
                "columns": column_map,
                "row_count": int(row_count),
            }
        except Exception as e:
            output[table] = {
                "description": f"Error reading table '{table}'",
                "columns": {},
                "row_count": None,
                "error": str(e)
            }
    return output