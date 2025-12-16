from dataclasses import dataclass
from typing import Literal
import redis
import time

SessionStatus = Literal["active", "waiting", "completed", "aborted"]

@dataclass
class SessionState:
    thread_id: str
    session_id: str
    canonical_query: str
    status: SessionStatus

class RedisSessionStore:
    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    def _session_key(self, thread_id: str, session_id: str) -> str:
        return f"thread:{thread_id}:session:{session_id}"

    def create_session(self, thread_id: str, session_id: str, initial_query: str):
        now = int(time.time())
        self.r.hset(
            self._session_key(thread_id, session_id),
            mapping={
                "canonical_query": initial_query.strip(),
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        )

    def get_session(self, thread_id: str, session_id: str) -> SessionState:
        data = self.r.hgetall(self._session_key(thread_id, session_id))
        if not data:
            raise KeyError(f"Session {session_id} not found")

        return SessionState(
            thread_id=thread_id,
            session_id=session_id,
            canonical_query=data["canonical_query"],
            status=data["status"],
        )

    def append_clarification(self, thread_id: str, session_id: str, clarification: str):
        clarification = clarification.strip()
        if not clarification:
            return

        key = self._session_key(thread_id, session_id)
        current = self.r.hget(key, "canonical_query") or ""
        new_query = f"{current} {clarification}".strip()

        self.r.hset(
            key,
            mapping={
                "canonical_query": new_query,
                "updated_at": int(time.time()),
            },
        )

    def mark_waiting(self, thread_id: str, session_id: str):
        self.r.hset(
            self._session_key(thread_id, session_id),
            mapping={
                "status": "waiting",
                "updated_at": int(time.time()),
            },
        )

    def mark_completed(self, thread_id: str, session_id: str):
        self.r.hset(
            self._session_key(thread_id, session_id),
            mapping={
                "status": "completed",
                "updated_at": int(time.time()),
            },
        )

class RedisThreadMeta:
    def __init__(self, redis_client):
        self.r = redis_client

    def _key(self, thread_id: str):
        return f"thread:{thread_id}"

    def set_active_session(self, thread_id: str, session_id: str):
        self.r.hset(self._key(thread_id), "active_session_id", session_id)

    def get_active_session(self, thread_id: str) -> str | None:
        return self.r.hget(self._key(thread_id), "active_session_id")

    def clear_active_session(self, thread_id: str):
        self.r.hdel(self._key(thread_id), "active_session_id")