import pandas as pd
from typing import Dict


def generate_create_table(table_name: str, schema: Dict[str, str]) -> str:
    """
    Generate a PostgreSQL CREATE TABLE statement.

    Parameters
    ----------
    table_name : str
        Name of the table to create.

    schema : Dict[str, str]
        Mapping of column_name -> PostgreSQL type.

    Returns
    -------
    str : CREATE TABLE SQL string
    """

    cols = []
    for col, pg_type in schema.items():
        cols.append(f'    "{col}" {pg_type}')

    columns_sql = ",\n".join(cols)

    create_stmt = f'CREATE TABLE "{table_name}" (\n{columns_sql}\n);\n\n'
    return create_stmt


def generate_copy_statement(table_name: str, df: pd.DataFrame) -> str:
    """
    Generates the COPY header for PostgreSQL.

    Example:
    COPY my_table (col1, col2) FROM STDIN WITH (FORMAT csv, HEADER true);
    """

    cols = ", ".join([f'"{c}"' for c in df.columns])
    return (
        f'COPY "{table_name}" ({cols}) '
        f'FROM STDIN WITH (FORMAT csv, HEADER true);\n'
    )


def dataframe_to_csv_block(df: pd.DataFrame) -> str:
    """
    Convert DataFrame to CSV text (no index) compatible with COPY.

    Returns
    -------
    str : CSV-formatted string
    """

    # DataFrame → CSV text
    csv_text = df.to_csv(index=False)
    return csv_text


def write_sql_file(output_path: str, table_name: str, df: pd.DataFrame, schema: Dict[str, str]):
    """
    Generate a full PostgreSQL .sql file containing:
    - CREATE TABLE
    - COPY ... FROM STDIN ...
    - CSV data
    - \.

    Parameters
    ----------
    output_path : str
        Path to the .sql file to generate.

    table_name : str
        Name of the table.

    df : pd.DataFrame
        DataFrame to export.

    schema : Dict[str, str]
        Column type mapping.
    """

    create_stmt = generate_create_table(table_name, schema)
    copy_stmt = generate_copy_statement(table_name, df)
    csv_block = dataframe_to_csv_block(df)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(create_stmt)
        f.write(copy_stmt)
        f.write(csv_block)
        f.write("\n\\.\n")

    print(f"[✔] SQL file generated at: {output_path}")
