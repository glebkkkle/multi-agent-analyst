# src/multi_agent_analyst/db/loaders.py
import pandas as pd
from src.multi_agent_analyst.db.connection import get_conn


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

