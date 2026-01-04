import pandas as pd
from sqlalchemy import text
from src.multi_agent_analyst.db.db_core import engine, validate_identifier


def load_user_tables(thread_id: str) -> dict:
    """
    Backend-only loader. Uses thread_id to query the correct schema,
    but returns ONLY table information (no schema/thread_id in output).
    """
    schema = validate_identifier(thread_id, "thread_id")

    result = {
        "available_tables": [],
        "tables": {}
    }

    # 1) Tables in that schema
    tables_df = pd.read_sql(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """),
        engine,
        params={"schema": schema},
    )

    table_names = tables_df["table_name"].tolist()
    result["available_tables"] = table_names

    for table_name in table_names:
        # 2) Columns (ordered)
        cols_df = pd.read_sql(
            text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                ORDER BY ordinal_position
            """),
            engine,
            params={"schema": schema, "table": table_name},
        )

        columns = [
            {"name": str(r["column_name"]), "type": str(r["data_type"])}
            for _, r in cols_df.iterrows()
        ]

        # 3) Row count (qualified)
        row_count = pd.read_sql(
            text(f'SELECT COUNT(*) AS c FROM "{schema}"."{table_name}"'),
            engine,
        ).iloc[0, 0]

        result["tables"][table_name] = {
            "row_count": int(row_count),
            "columns": columns,
        }

    return result