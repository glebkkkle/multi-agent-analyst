import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd 
import uuid
import pickle
from typing import Any
import redis
import traceback
from functools import wraps
from src.multi_agent_analyst.logging import logger
import numpy as np
import pandas as pd
from datetime import datetime
from src.backend.config import settings
import json 
import math 

class RedisObjectStore:
    """
    Redis-backed object store for intermediate artifacts.
    Used for DataFrames, analysis results, visualization specs, etc.
    """
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_app_host,
            port=settings.redis_app_port,
            db=settings.redis_app_db,
            decode_responses=False, 
        )

    def save(self, obj: Any, ttl: int = 3600) -> str:
        """
        Save an object and return its object_id.
        """
        obj_id = f"obj_{uuid.uuid4().hex[:8]}"
        payload = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        self.redis.set(obj_id, payload, ex=ttl)
        return obj_id

    def get(self, obj_id: str) -> Any:
        """
        Retrieve an object by object_id.
        """
        payload = self.redis.get(obj_id)
        if payload is None:
            raise KeyError(f"Object '{obj_id}' not found in Redis")
        return pickle.loads(payload)


object_store = RedisObjectStore()

class CurrentToolContext:
    def __init__(self):
        self.dict={'DataAgent':{}, 'AnalysisAgent':{}, 'VisualizationAgent':{}}

    def set(self,agent, step, data):
        self.dict[agent][step]=data
    
    def get(self,agent, step_id):
        return self.dict[agent][step_id]
    
class ExecutionLogEntry(BaseModel):
    id: str
    agent: str
    sub_query: str
    status: Optional[str]=None  # "success" | "error"
    output_object_id: Optional[str] = None
    error_message: Optional[str] = None

class ExecutionLogList(BaseModel):
    execution_log_list: Dict[str, list[Any]] = {}

execution_list=ExecutionLogList()

context=CurrentToolContext()

current_tables={}

viz_json={}

def load_and_validate_df(data_id):
    try:
        df = object_store.get(data_id)
    except Exception as e:
        return None, f"DATA_ACCESS_ERROR: {e}"

    if df is None:
        return None, f"DATA_NOT_FOUND: object '{data_id}' does not exist"

    if len(df) == 0:
        return None, f"DATA_EMPTY: object '{data_id}' is empty"

    return df, None

def create_log(agent, exception, status, id,output_object_id, sub_query):
    log=ExecutionLogEntry(id=id, agent=agent, sub_query=sub_query, status=status, output_object_id=output_object_id, error_message=exception)
    execution_list.execution_log_list.setdefault(id, []).append(log)
    return log

def generate_data_preview(object_id):
    df, error=load_and_validate_df(object_id)
    if error:
        return {"exception":error}
    
    types_schema=df.dtypes.to_dict()
    sample=df.head(3).to_dict(orient='records')

    return f"Object {object_id} CONTEXT:\nColumns: {types_schema}\nSample: {sample}"


def normalize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in df.columns:
        s = df[col]

        if s.dtype == object:
            try:
                parsed = pd.to_datetime(s, errors="raise", utc=False)
                df[col] = parsed
                continue
            except Exception:
                pass

        if s.dtype == object:
            numeric = pd.to_numeric(s, errors="coerce")
            if not numeric.isna().all():
                df[col] = numeric
                continue

        if pd.api.types.is_integer_dtype(s):
            df[col] = s.astype("Int64")  

        elif pd.api.types.is_float_dtype(s):
            df[col] = s.astype("float64")

        elif s.dtype == object:
            df[col] = s.astype("string")

    return df


def guarded(node_name: str):
    def deco(fn):
        @wraps(fn)
        def wrapper(state, *args, **kwargs):
            try:
                # Clear previous error so it doesn't leak forward
                patch = fn(state, *args, **kwargs)

                # Ensure dict patch
                if patch is None:
                    patch = {}
                elif not isinstance(patch, dict):
                    raise TypeError(f" must return dict patch, got {type(patch)}")

                return patch

            except Exception as e:
                tb = traceback.format_exc()
                logger.exception("Node crashed", extra={"thread_id": getattr(state, "thread_id", None)})

                # Convert crash → error state
                return {
                    "desicion": "error",
                    "has_error": True,
                    "execution_exception": f"{type(e).__name__}: {str(e)}",
                    # optional: keep full traceback in trace/logs only (don't show to users)
                    # "execution_traceback": tb,  # only if your GraphState has it
                }
        return wrapper
    return deco


def agent_error(msg: str, *, object_id=None):
    return {
        "status": "error",
        "object_id": object_id,
        "summary": None,
        "exception": msg,
    }

def agent_success(object_id: str, summary: str):
    return {
        "status": "success",
        "object_id": object_id,
        "summary": summary,
        "exception": None,
    }

def json_safe(obj):
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [json_safe(v) for v in obj]

    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating, float)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val

    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)

    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()

    if obj is pd.NA or obj is None:
        return None

    if isinstance(obj, (int, str)):
        return obj

    return str(obj)

def parse_tool_output(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Tool output is not valid JSON")
    raise TypeError(f"Unexpected tool output type: {type(raw)}")