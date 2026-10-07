import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connected: bool = False
        self._in_memory_fallback: dict[str, str] = {}

    async def connect(self):
        if not settings.REDIS_ENABLED:
            return
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1.5,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(
                f"Redis unavailable ({e}). Using in-memory fallback for caching."
            )
            self._connected = False

    async def close(self):
        if self._redis and self._connected:
            await self._redis.close()

    async def get_json(self, key: str) -> Optional[Any]:
        try:
            if self._connected and self._redis:
                val = await self._redis.get(key)
            else:
                val = self._in_memory_fallback.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.error(f"Error reading cache key {key}: {e}")
        return None

    async def set_json(self, key: str, value: Any, ttl: int = 300):
        try:
            serialized = json.dumps(value, default=str)
            if self._connected and self._redis:
                await self._redis.set(key, serialized, ex=ttl)
            else:
                self._in_memory_fallback[key] = serialized
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")

    async def delete(self, key: str):
        try:
            if self._connected and self._redis:
                await self._redis.delete(key)
            else:
                self._in_memory_fallback.pop(key, None)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")

    async def ping(self) -> bool:
        try:
            if self._connected and self._redis:
                return await self._redis.ping()
            return False
        except Exception:
            return False


cache = CacheClient()
