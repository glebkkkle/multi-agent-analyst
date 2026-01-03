from __future__ import annotations

import time
import json
from typing import Optional, Dict, Any
import redis


class RedisExecutionStore:
    """
    Redis-backed execution state for UI polling.

    This store is:
    - ephemeral
    - UI-facing
    - NOT used for durability or replay
    - intentionally simple and strict

    Redis schema (hash):
      execution:{session_id} -> {
        session_id: str
        status: str
        final_response: str
        final_obj_id: str
        final_table_shape: str
        milestones: JSON list
        next_seq: int
        updated_at: float
      }
    """

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    # ---------- internal helpers ----------

    def _key(self, session_id: str) -> str:
        return f"execution:{session_id}"

    @staticmethod
    def _safe_str(value: Optional[Any]) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    # ---------- lifecycle ----------

    def init_session(self, session_id: str) -> None:
        now = time.time()

        self.r.hset(
            self._key(session_id),
            mapping={
                "session_id": session_id,
                "status": "running",
                "final_response": "",
                "final_obj_id": "",
                "final_table_shape": "",
                "milestones": "[]",
                "next_seq": 1,
                "started_at": now,
                "updated_at": now,
            },
        )

    # ---------- milestones ----------

    def add_milestone(self, session_id: str, label: str) -> Optional[int]:
        label = label.strip()
        if not label:
            return None

        key = self._key(session_id)
        now = time.time()

        pipe = self.r.pipeline()
        pipe.hget(key, "milestones")
        pipe.hget(key, "next_seq")
        milestones_json, next_seq = pipe.execute()

        if next_seq is None:
            return None

        seq = int(next_seq)
        milestones = json.loads(milestones_json or "[]")

        milestones.append(
            {
                "seq": seq,
                "label": label,
                "ts": now,
            }
        )

        self.r.hset(
            key,
            mapping={
                "milestones": json.dumps(milestones),
                "next_seq": seq + 1,
                "updated_at": now,
            },
        )

        return seq

    # ---------- state transitions ----------

    def mark_running(self, session_id: str, reset_clock: bool = False) -> None:
        now = time.time()

        mapping = {
            "status": "running",
            "final_response": "",
            "updated_at": now,
        }

        if reset_clock:
            mapping["started_at"] = now   # ⏱️ reset execution timer

        self.r.hset(self._key(session_id), mapping=mapping)


    def mark_waiting(self, session_id: str, prompt: Optional[str]) -> None:
        self.r.hset(
            self._key(session_id),
            mapping={
                "status": "waiting",
                "final_response": self._safe_str(prompt),
                "final_obj_id": "",
                "final_table_shape": "",
                "updated_at": time.time(),
            },

        )

    def mark_done(self, session_id: str, final_payload: Dict[str, Any]) -> None:
        self.r.hset(
            self._key(session_id),
            mapping={
                "status": "completed",
                "final_response": self._safe_str(final_payload.get("final_response")),
                "final_obj_id": self._safe_str(final_payload.get("final_obj_id")),
                "final_table_shape": self._safe_str(final_payload.get("final_table_shape")),
                "updated_at": time.time(),
            },
        )

    def mark_failed(self, session_id: str, error: str) -> None:
        self.r.hset(
            self._key(session_id),
            mapping={
                "status": "failed",
                "final_response": f"Internal error: {error}",
                "final_obj_id": "",
                "final_table_shape": "",
                "updated_at": time.time(),
            },
        )

    def mark_aborted(self, session_id: str, message: str) -> None:
        self.r.hset(
            self._key(session_id),
            mapping={
                "status": "aborted",
                "final_response": self._safe_str(message),
                "final_obj_id": "",
                "final_table_shape": "",
                "updated_at": time.time(),
            },
        )

    def get_snapshot(self, session_id: str, after_seq: int = 0) -> Optional[Dict[str, Any]]:
        data = self.r.hgetall(self._key(session_id))
        if not data:
            return None

        milestones = json.loads(data.get("milestones", "[]"))
        new_milestones = [m for m in milestones if m["seq"] > after_seq]

        return {
            "session_id": data.get("session_id", session_id),
            "status": data.get("status", ""),
            "final_response": data.get("final_response", ""),
            "final_obj_id": data.get("final_obj_id", ""),
            "final_table_shape": data.get("final_table_shape", ""),
            "milestones": new_milestones,
            "started_at": float(data.get("started_at", 0)),  # ✅ ADD
            "updated_at": float(data.get("updated_at", 0)),
        }
