import pandas as pd
from typing import Dict

def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    schema = {}

    for col in df.columns:
        series = df[col]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]

        dtype = series.dtype

        if pd.api.types.is_integer_dtype(dtype):
            schema[col] = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            schema[col] = "DOUBLE PRECISION"
        elif pd.api.types.is_bool_dtype(dtype):
            schema[col] = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            schema[col] = "TIMESTAMP"
        else:
            schema[col] = "TEXT"

    return schema
