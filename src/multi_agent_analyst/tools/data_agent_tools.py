import pandas as pd
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.data_agent_schema import (
    SQLQuerySchema,
    SelectColumnsSchema,
    MergeTablesSchema,
    ListDataSchema
)

from src.multi_agent_analyst.db.db_core import get_thread_conn
from src.backend.storage.emitter import current_thread_id

from src.multi_agent_analyst.utils.utils import object_store, current_tables
import pandas as pd
from langchain_core.tools import StructuredTool

from src.multi_agent_analyst.db.db_core import engine, get_thread_conn, agent_execution
from src.multi_agent_analyst.utils.utils import object_store, current_tables, normalize_dataframe_types
import re
import math 

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


def qualify_sql(sql: str, schema: str) -> str:
    """
    Naively qualifies unqualified table names with the thread schema.
    Assumes simple SELECTs (which is exactly your agent use case).
    """
    # Example: FROM radial_data → FROM "thread_21".radial_data
    return re.sub(
        r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        rf'FROM "{schema}".\1',
        sql,
        flags=re.IGNORECASE
    )

def make_sql_query_tool():
    thread_id = current_thread_id.get()
    def sql_query(query: str):
        try:
            with agent_execution(thread_id):
                with get_thread_conn(thread_id) as conn:
                    qualified_query = qualify_sql(query, thread_id)

                    df = pd.read_sql_query(qualified_query, conn)
                    df = normalize_dataframe_types(df)
                    obj_id = object_store.save(df)

                    return {
                        "object_id": obj_id,
                        "details": {
                            "row_count": len(df),
                            "columns": list(df.columns),
                        },
                        "exception": None
                    }

        except Exception as e:
            return {
                "object_id": None,
                "exception": str(e),
                "details": {}
            }

    return StructuredTool.from_function(
        func=sql_query,
        name="sql_query",
        description="Executes an SQL query on the database and returns the result.",
        args_schema=SQLQuerySchema,
    )

def make_schema_list(schemas: dict):
    """
    schemas format (trusted input):
    {
      "available_tables": [...],
      "tables": {
        table_name: {
          "row_count": int,
          "columns": [{"name": str, "type": str}]
        }
      }
    }
    """

    def list_available_data():
        readable = []

        for table_name in schemas.get("available_tables", []):
            meta = schemas["tables"].get(table_name, {})

            columns = meta.get("columns", [])
            column_strings = [
                f"{col['name']} ({col['type']})"
                for col in columns
            ]

            readable.append({
                "table": table_name,
                "row_count": meta.get("row_count", 0),
                "columns": column_strings,
            })

        obj_id = object_store.save(readable)

        return {
            "object_id": obj_id,
            "details": {
                "table_count": len(readable),
                "tables": [t["table"] for t in readable],
            },
        }

    return StructuredTool.from_function(
        func=list_available_data,
        name="list_available_data",
        description=(
            "Returns a human-readable catalog of available tables for the current user. "
            "This does NOT query the database and should only be used when explicitly "
            "requested by the Planner."
        ),
        args_schema=ListDataSchema,
    )

def make_select_columns_tool():
    """Factory: returns a column-selection tool."""

    def select_columns(table_id: str, columns: list):
        try:
            df = object_store.get(table_id)
            result = df[columns]
        except Exception as e:
            return {
                'exception': str(e)
            }
        
        obj_id = object_store.save(result)

        return {
                "object_id": obj_id,
                "details": {
                    "input_table_id": table_id,
                    "selected_columns": columns,
                    "output_rows": len(result),
                    "output_cols": len(columns),
                    },

                }
    return StructuredTool.from_function(
        func=select_columns,
        name="select_columns",
        description="Select specific columns from a table referenced by ID.",
        args_schema=SelectColumnsSchema,
    )

def make_merge_tool():
    """Factory: returns a dataframe merge tool."""

    def merge_tables(left_id: str, right_id: str, on: str, how: str = "inner"):
        try:
            left = object_store.get(left_id)
            right = object_store.get(right_id)

            merged = left.merge(right, on=on, how=how)

        except Exception as e:
            return {
                'exception': str(e)
            }
        
        obj_id = object_store.save(merged)
        payload = {
            "object_id": obj_id,
            "details": {
                "row_count": len(merged),
                "columns": list(map(str, merged.columns)),
                "preview": merged.head(5).to_dict(orient="records"),
            },
            "exception": None,
        }

        return sanitize_for_json(payload)

    return StructuredTool.from_function(
        func=merge_tables,
        name="merge_tables",
        description="Merge/join two tables by ID.",
        args_schema=MergeTablesSchema,
    )


__all__ = [
    "make_sql_query_tool",
    "make_select_columns_tool",
    "make_merge_tool",
]