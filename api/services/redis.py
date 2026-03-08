"""
Redis service — async client for ephemeral state (OAuth CSRF, rate limiting).
"""

import redis.asyncio as aioredis

from api.config import settings

_redis: aioredis.Redis | None = None  # type: ignore[type-arg]


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def set_state(state: str, ttl: int) -> None:
    """Store OAuth CSRF state with TTL (one-time-use)."""
    r = await get_redis()
    await r.set(f"oauth:state:{state}", "1", ex=ttl)


async def consume_state(state: str) -> bool:
    """Validate and delete OAuth state atomically. Returns True if valid."""
    r = await get_redis()
    key = f"oauth:state:{state}"
    # Atomic getdel — available in Redis 6.2+
    value = await r.getdel(key)
    return value is not None
