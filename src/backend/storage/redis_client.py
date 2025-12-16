import os
import redis

# -----------------------------------------------------------------------------
# Redis connection
# -----------------------------------------------------------------------------
# Keep this file DUMB on purpose.
# No business logic. No thread logic. Just connection.
# -----------------------------------------------------------------------------

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB_THREAD_STORE = int(os.getenv("REDIS_DB_THREAD_STORE", "0"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB_THREAD_STORE,
    decode_responses=True,  # IMPORTANT: always work with strings, not bytes
)

def ping() -> bool:
    """Simple health check."""
    return bool(redis_client.ping())
