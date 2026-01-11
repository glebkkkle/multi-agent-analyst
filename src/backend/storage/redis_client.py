# In src/backend/storage/redis_client.py (or wherever you have this)

import redis
from langgraph.checkpoint.redis import RedisSaver
from src.backend.config import settings

# Regular Redis for app data (sessions, execution state, etc.)
redis_client = redis.Redis(
    host=settings.redis_app_host,
    port=settings.redis_app_port,
    db=settings.redis_app_db,
    decode_responses=True,
)

REDIS_CHECKPOINTER_URL = (
    f"redis://{settings.redis_checkpointer_host}:"
    f"{settings.redis_checkpointer_port}/" 
    f"{settings.redis_checkpointer_db}"
)

checkpointer = RedisSaver(REDIS_CHECKPOINTER_URL)