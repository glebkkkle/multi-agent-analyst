import pandas as pd
from pathlib import Path
from io import BytesIO


class UnsupportedFileTypeError(Exception):
    pass


def read_file(file_input, override_filename: str = None) -> pd.DataFrame:
    """
    Reads CSV or XLSX from either:
    - a file path
    - a BytesIO buffer (FastAPI upload)

    Parameters
    ----------
    file_input : str | BytesIO
        Path or in-memory uploaded file.

    override_filename : str
        Required when using BytesIO to determine the type (.csv or .xlsx)

    Returns
    -------
    pd.DataFrame
    """

    if isinstance(file_input, BytesIO):
        if override_filename is None:
            raise UnsupportedFileTypeError("override_filename required for BytesIO input")

        ext = override_filename.lower().split(".")[-1]

        if ext == "csv":
            df = pd.read_csv(file_input)
        elif ext == "xlsx":
            df = pd.read_excel(file_input)
        else:
            raise UnsupportedFileTypeError("Only .csv and .xlsx supported.")

    else:
        # Normal file path mode
        path = Path(file_input)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_input}")

        ext = path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext == ".xlsx":
            df = pd.read_excel(path)
        else:
            raise UnsupportedFileTypeError("Only .csv and .xlsx supported.")

    # Normalize column names
    df.columns = [
        _normalize_col_name(str(col))
        for col in df.columns
    ]

    return df


def _normalize_col_name(name: str) -> str:
    import re
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    if name == "" or name is None:
        name = "col_unnamed"
    if name[0].isdigit():
        name = "col_" + name
    return name