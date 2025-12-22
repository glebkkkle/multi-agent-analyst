import redis
from langgraph.checkpoint.redis import RedisSaver
from src.backend.config import settings

redis_client = redis.Redis(
    host=settings.redis_app_host,
    port=settings.redis_app_port,
    db=settings.redis_app_db,
    decode_responses=True,
)

REDIS_CHECKPOINTER_URL = (
    f"redis://{settings.redis_checkpointer_host}:"
    f"{settings.redis_checkpointer_port}/0"
)

checkpointer = RedisSaver(REDIS_CHECKPOINTER_URL)

def ping() -> bool:
    return bool(redis_client.ping())
