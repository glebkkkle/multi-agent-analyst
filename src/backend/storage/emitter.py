from contextvars import ContextVar
from typing import Callable, Optional

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