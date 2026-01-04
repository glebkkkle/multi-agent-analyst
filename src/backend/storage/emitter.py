from contextvars import ContextVar
from typing import Callable, Optional, Dict, Any
from src.multi_agent_analyst.db.loaders import load_user_tables

MilestoneEmitter = Callable[[str], None]

_current_emitter: ContextVar[Optional[MilestoneEmitter]] = ContextVar(
    "current_milestone_emitter",
    default=None,
)

def set_emitter(emitter: MilestoneEmitter) -> None:
    _current_emitter.set(emitter)


def clear_emitter() -> None:
    _current_emitter.set(None)


def emit(msg: str) -> None:
    emitter = _current_emitter.get()
    if emitter is not None:
        emitter(msg)


ThreadTables = Dict[str, object]

_current_thread_tables: ContextVar[Optional[ThreadTables]] = ContextVar(
    "current_thread_tables",
    default=None
)

def init_thread_tables(thread_id: str):
    tables = load_user_tables(thread_id)
    _current_thread_tables.set(tables)

def get_current_tables() -> ThreadTables:
    tables = _current_thread_tables.get()
    return tables


def refresh_thread_tables(thread_id: str):
    tables = _current_thread_tables.get()
    if tables is None:
        return  

    updated = load_user_tables(thread_id)
 
    tables.clear()
    tables.update(updated)


current_thread_id: ContextVar[str] = ContextVar("current_thread_id")