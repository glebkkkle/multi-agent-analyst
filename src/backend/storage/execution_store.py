from __future__ import annotations

from typing import Dict, List, Optional, Any
from threading import Lock
import time
import copy


class ExecutionStateStore:
    """
    In-memory execution state store.

    Invariants:
    - milestones are append-only
    - milestone seq is strictly increasing per session
    - snapshot schema is stable (keys always present)
    - get_snapshot returns a COPY (never internal dict)
    """

    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._lock = Lock()

    def init_session(self, session_id: str) -> None:
        now = time.time()
        with self._lock:
            self._store[session_id] = {
                "session_id": session_id,
                "status": "running",
                "final_response": None,
                "final_obj_id": None,
                "final_table_shape": None,
                "milestones": [],
                "next_seq": 1,
                "updated_at": now,
            }

    def add_milestone(self, session_id: str, label: str) -> Optional[int]:
        now = time.time()
        with self._lock:
            s = self._store.get(session_id)
            if not s:
                return None

            seq = s["next_seq"]
            s["next_seq"] += 1

            s["milestones"].append({"seq": seq, "label": label, "ts": now})
            s["updated_at"] = now
            return seq

    def mark_waiting(self, session_id: str, prompt: str) -> None:
        """
        Pause execution awaiting user clarification.
        final_response carries the prompt shown to the user.
        """
        now = time.time()
        with self._lock:
            s = self._store.get(session_id)
            if not s:
                return
            s["status"] = "waiting"
            s["final_response"] = prompt
            s["updated_at"] = now
            s['final_obj_id']=None
            s["final_table_shape"]=None


    def mark_done(self, session_id: str, final_payload: dict) -> None:
        now = time.time()
        with self._lock:
            s = self._store.get(session_id)
            if not s:
                return
            s["status"] = "completed"
            s["final_response"] = final_payload.get("final_response")
            s["final_obj_id"] = final_payload.get("final_obj_id")
            s["final_table_shape"] = final_payload.get("final_table_shape")
            s["updated_at"] = now


    def mark_aborted(self, session_id: str, message: str) -> None:
        now = time.time()
        with self._lock:
            s = self._store.get(session_id)
            if not s:
                return
            s["status"] = "aborted"
            s["final_response"] = message
            s["updated_at"] = now
            s['final_obj_id']=None
            s["final_table_shape"]=None

    def mark_failed(self, session_id: str, error: str) -> None:
        """
        'failed' is for internal error paths.
        You may choose to map this to 'aborted' for users.
        """
        now = time.time()
        with self._lock:
            s = self._store.get(session_id)
            if not s:
                return
            s["status"] = "failed"
            s["final_response"] = f"Internal error: {error}"
            s["updated_at"] = now
            s['final_obj_id']=None
            s["final_table_shape"]=None
    def get_snapshot(self, session_id: str, after_seq: int = 0):
        with self._lock:
            s = self._store.get(session_id)
            if s is None:
                return None

            milestones = s.get("milestones", [])
            new_milestones = [m for m in milestones if m["seq"] > after_seq]

        return {
        "session_id": session_id,
        "status": s["status"],
        "final_response": s.get("final_response"),
        "final_obj_id": s.get("final_obj_id"),
        "final_table_shape": s.get("final_table_shape"),
        "milestones": new_milestones,
        "updated_at": s["updated_at"],
        }
execution_store = ExecutionStateStore()
