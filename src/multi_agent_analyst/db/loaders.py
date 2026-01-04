import pandas as pd
from src.multi_agent_analyst.db.db_core import engine
from sqlalchemy import text

def load_user_tables() -> dict:
    """
    Load a deterministic description of all tables
    visible in the current search_path.

    PRIVILEGED BACKEND OPERATION.
    """
    result = {
        "available_tables": [],
        "tables": {}
    }

    # 1️⃣ List tables visible via search_path
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

        # 2️⃣ Column metadata (ordered)
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
            {
                "name": str(row["column_name"]),
                "type": str(row["data_type"]),
            }
            for _, row in cols_df.iterrows()
        ]

        # 3️⃣ Row count (unqualified table name uses search_path)
        row_count = pd.read_sql(
            text(f'SELECT COUNT(*) FROM "{table_name}"'),
            engine,
        ).iloc[0, 0]

        result["tables"][table_name] = {
            "row_count": int(row_count),
            "columns": columns,
        }

    return result