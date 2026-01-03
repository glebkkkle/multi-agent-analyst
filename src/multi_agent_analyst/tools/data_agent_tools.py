import pandas as pd
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.data_agent_schema import (
    SQLQuerySchema,
    SelectColumnsSchema,
    MergeTablesSchema,
    ListDataSchema
)

from src.multi_agent_analyst.db.db_core import get_thread_conn

from src.multi_agent_analyst.utils.utils import object_store, current_tables
import pandas as pd
from langchain_core.tools import StructuredTool

from src.multi_agent_analyst.db.db_core import engine, get_thread_conn
from src.multi_agent_analyst.utils.utils import object_store, current_tables, normalize_dataframe_types


def make_sql_query_tool():
    thread_id = list(current_tables.keys())[0]

    def sql_query(query: str):
        try:
            with get_thread_conn(thread_id) as conn:  
                df = pd.read_sql_query(query, conn)
                df = normalize_dataframe_types(df)
                print(df)
                
                obj_id = object_store.save(df)
                print(' ')
                print(obj_id)
                print(' ')

                return {
                    "object_id": obj_id,
                    "details": {"row_count": len(df)},
                    "exception": None  
                }

        except Exception as e:
            return {
                'object_id': None,
                'exception': str(e),  
                'details': {}
            }

    return StructuredTool.from_function(
        func=sql_query,
        name="sql_query",
        description="Executes an SQL query on the database and returns the result.",
        args_schema=SQLQuerySchema,
    )

def make_schema_list(schemas):
    def list_available_data():
        readable = []

        for schema in schemas:
            readable.append({
                k: (
                    ", ".join(f"{ck}: {cv}" for ck, cv in v.items())
                    if isinstance(v, dict)
                    else v
                )
                for k, v in schema.items()
            })
        print(readable)
        obj_id = object_store.save(readable)

        return {
            "object_id": obj_id,
            "details": {"schemas": "listed"}
        }

    return StructuredTool.from_function(
        func=list_available_data,
        name="list_available_data",
        description="A function that provides a list of available data",
        args_schema=ListDataSchema
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
        print(obj_id)

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
        return {
            "object_id": obj_id,
            "details": {
                "row_count": len(merged),
                "columns": list(merged.columns),
                "preview": merged.head(5).to_dict(orient="records")
            }
        }

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