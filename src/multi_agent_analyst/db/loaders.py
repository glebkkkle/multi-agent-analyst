import pandas as pd
from sqlalchemy import text
from src.multi_agent_analyst.db.db_core import engine


def load_user_tables(thread_id: str) -> dict:
    """
    Load table metadata for the CURRENT search_path.

    thread_id is accepted for compatibility with the graph/state,
    but is NOT used directly (search_path already enforces isolation).
    """

    result = {
        "available_tables": [],
        "tables": {}
    }

    # Tables visible via current search_path
    tables_df = pd.read_sql(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = ANY (current_schemas(false))
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """),
        engine,
    )

    for table_name in tables_df["table_name"].tolist():
        result["available_tables"].append(table_name)

        # Columns
        cols_df = pd.read_sql(
            text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = ANY (current_schemas(false))
                  AND table_name = :table
                ORDER BY ordinal_position
            """),
            engine,
            params={"table": table_name},
        )

        columns = [
            {"name": row["column_name"], "type": row["data_type"]}
            for _, row in cols_df.iterrows()
        ]

        # Row count
        row_count = pd.read_sql(
            text(f'SELECT COUNT(*) FROM "{table_name}"'),
            engine,
        ).iloc[0, 0]

        result["tables"][table_name] = {
            "row_count": int(row_count),
            "columns": columns,
        }

    return result
