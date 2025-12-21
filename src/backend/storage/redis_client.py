import os
import redis
from langgraph.checkpoint.redis import RedisSaver

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# App Redis (Valkey)
REDIS_APP_PORT = int(os.getenv("REDIS_APP_PORT", "6379"))
REDIS_DB_THREAD_STORE = int(os.getenv("REDIS_DB_THREAD_STORE", "0"))

# LangGraph Redis Stack (🚨 MUST be DB 0)
REDIS_CHECKPOINTER_PORT = int(os.getenv("REDIS_CHECKPOINTER_PORT", "6380"))
REDIS_DB_CHECKPOINTER = 0  # ← THIS is the fix

# App Redis (you manage this)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_APP_PORT,
    db=REDIS_DB_THREAD_STORE,
    decode_responses=True,
)

# LangGraph checkpointer
REDIS_CHECKPOINTER_URL = f"redis://{REDIS_HOST}:{REDIS_CHECKPOINTER_PORT}/{REDIS_DB_CHECKPOINTER}"
checkpointer = RedisSaver(REDIS_CHECKPOINTER_URL)

def ping() -> bool:
    return bool(redis_client.ping())
