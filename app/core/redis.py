from typing import Optional
from redis.asyncio import Redis, from_url
from app.core.config import settings

redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            settings.async_redis_url,
            encoding="utf-8",
            decode_responses=True,
            protocol=2,
        )
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def check_redis_health() -> bool:
    try:
        client = await get_redis()
        pong = await client.ping()
        return pong is True or pong == "PONG" or pong == b"PONG"
    except Exception:
        return False
