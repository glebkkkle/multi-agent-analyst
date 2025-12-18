# src/backend/storage/conversation_store.py
from typing import List, Dict
from datetime import datetime
from src.multi_agent_analyst.db.db_core import get_conn  # reuse your helper

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
        limit: int = 6,
    ) -> List[Dict]:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content
                    FROM thread_messages
                    WHERE thread_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (thread_id, limit),
                )
                rows = cur.fetchall()

        # reverse → chronological order
        return [
            {"role": role, "content": content}
            for role, content in reversed(rows)
        ]

    def clear(self, thread_id: str):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM thread_messages WHERE thread_id = %s",
                    (thread_id,),
                )
            conn.commit()
