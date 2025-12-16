from dataclasses import dataclass
from typing import List
import json
import redis

@dataclass
class ThreadState:
    thread_id: str
    canonical_query: str
    history: List[str]

class RedisThreadStore:
    def __init__(self, redis_client: redis.Redis, prefix: str = "thread:"):
        self.r = redis_client
        self.prefix = prefix

    def _key(self, thread_id: str) -> str:
        return f"{self.prefix}{thread_id}"

    def get_or_create(self, thread_id: str) -> ThreadState:
        key = self._key(thread_id)

        if not self.r.exists(key):
            self.r.hset(key, mapping={
                "canonical_query": "",
                "history": json.dumps([]),
            })

        data = self.r.hgetall(key)

        return ThreadState(
            thread_id=thread_id,
            canonical_query=(data.get("canonical_query") or "").strip(),
            history=json.loads(data.get("history") or "[]"),
        )

    def append_query(self, thread_id: str, addition: str) -> ThreadState:
        addition = addition.strip()
        if not addition:
            return self.get_or_create(thread_id)

        state = self.get_or_create(thread_id)

        new_query = (
            f"{state.canonical_query} {addition}".strip()
            if state.canonical_query
            else addition
        )

        new_history = state.history + [f"user: {addition}"]

        self.r.hset(
            self._key(thread_id),
            mapping={
                "canonical_query": new_query,
                "history": json.dumps(new_history[-20:]),  # cap history
            },
        )

        return ThreadState(
            thread_id=thread_id,
            canonical_query=new_query,
            history=new_history[-20:],
        )
