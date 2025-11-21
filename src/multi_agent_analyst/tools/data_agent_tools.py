import pandas as pd
from langchain_core.tools import StructuredTool

from src.multi_agent_analyst.schemas.data_agent_schema import (
    SQLQuerySchema,
    SelectColumnsSchema,
    MergeTablesSchema,
)

from src.multi_agent_analyst.db.connection import get_conn
from src.multi_agent_analyst.utils.utils import object_store

def make_sql_query_tool():
    """Factory: returns a SQL query execution tool."""

    def sql_query(query: str):
        conn = get_conn()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return object_store.save(df)

    return StructuredTool.from_function(
        func=sql_query,
        name="sql_query",
        description="Executes an SQL query on company_data.db and returns the result.",
        args_schema=SQLQuerySchema,
    )


def make_select_columns_tool():
    """Factory: returns a column-selection tool."""

    def select_columns(table_id: str, columns: list):
        df = object_store.get(table_id)
        result = df[columns]
        return object_store.save(result)

    return StructuredTool.from_function(
        func=select_columns,
        name="select_columns",
        description="Select specific columns from a table referenced by ID.",
        args_schema=SelectColumnsSchema,
    )


def make_merge_tool():
    """Factory: returns a dataframe merge tool."""

    def merge_tables(left_id: str, right_id: str, on: str, how: str = "inner"):
        left = object_store.get(left_id)
        right = object_store.get(right_id)

        merged = left.merge(right, on=on, how=how)
        return object_store.save(merged)

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