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
    clarification_count: int


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
                "clarification_count": 0,
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
            canonical_query=data.get("canonical_query", ""),
            status=data.get("status", "active"),
            clarification_count=int(data.get("clarification_count", 0)),
        )

    def append_clarification(self, thread_id: str, session_id: str, clarification: str) -> int:
        clarification = clarification.strip()
        if not clarification:
            return self.get_session(thread_id, session_id).clarification_count

        key = self._session_key(thread_id, session_id)
        now = int(time.time())

        pipe = self.r.pipeline()
        pipe.hget(key, "canonical_query")
        pipe.hincrby(key, "clarification_count", 1)
        current_query, new_count = pipe.execute()

        new_query = f"{current_query or ''} {clarification}".strip()

        self.r.hset(
            key,
            mapping={
                "canonical_query": new_query,
                "updated_at": now,
            },
        )

        return int(new_count)


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
    def mark_aborted(self, thread_id: str, session_id: str):
        self.r.hset(
            self._session_key(thread_id, session_id),
            mapping={
                "status": "aborted",
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