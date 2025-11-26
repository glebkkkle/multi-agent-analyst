import pandas as pd
from typing import Dict
def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """
    Infer PostgreSQL-compatible column types from a pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    Dict[str, str]
        Mapping: {column_name: pg_type}
    """

    schema = {}

    for col in df.columns:
        dtype = df[col].dtype

        # INT
        if pd.api.types.is_integer_dtype(dtype):
            schema[col] = "INTEGER"

        # FLOAT
        elif pd.api.types.is_float_dtype(dtype):
            schema[col] = "DOUBLE PRECISION"

        # BOOL
        elif pd.api.types.is_bool_dtype(dtype):
            schema[col] = "BOOLEAN"

        # DATETIME
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            schema[col] = "TIMESTAMP"

        # OBJECT = TEXT (fallback)
        else:
            schema[col] = "TEXT"

    print(schema)
    return schema


