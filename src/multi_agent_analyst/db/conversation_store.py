# src/backend/storage/conversation_store.py
from typing import List, Dict
from datetime import datetime
from src.multi_agent_analyst.db.db_core import get_conn  # reuse your helper
import time 

class ThreadConversationStore:
    def append(self, thread_id: str, role: str, content: str):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO thread_messages (thread_id, role, content)
                    VALUES (%s, %s, %s)
                    """,
                    (thread_id, role, content),
                )
            conn.commit()

    def get_recent(
        self,
        thread_id: str,
        max_age_seconds: int,
        limit: int = 4,
    ) -> list[dict]:
        cutoff = time.time() - max_age_seconds

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, created_at
                    FROM thread_messages
                    WHERE thread_id = %s
                      AND created_at >= to_timestamp(%s)
                      AND role = 'user'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (thread_id, cutoff, limit),
                )
                rows = cur.fetchall()
        # chronological order
        return [
            {
                "content": content,
                "created_at": created_at.timestamp()
                if hasattr(created_at, "timestamp") else created_at,
            }
            for content, created_at in reversed(rows)
        ]
    def clear(self, thread_id: str):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM thread_messages WHERE thread_id = %s",
                    (thread_id,),
                )
            conn.commit()
