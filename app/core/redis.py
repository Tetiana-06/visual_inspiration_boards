import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


def board_cache_key(board_id: int) -> str:
    """Lab 4: ключ кешу деталей дошки. Шаблон: <app>:<entity>:<id>:<view>."""
    return f"vib:board:{board_id}:detail"


class CacheClient:
    """
    Клієнт спільного Redis для всіх backend-інстансів.
    Fallback (Lab 4): якщо Redis недоступний, кожен метод повертає None / нічого не робить —
    запит обслуговується напряму з БД (Graceful Degradation). Локальної пам'яті немає,
    інакше вузли бачили б різні дані.
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        if not settings.REDIS_ENABLED:
            return
        # Клієнт підключається ліниво й сам перепідключається, коли Redis повертається
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.5,  # не чекаємо мертвий Redis довше 0.5 с
            socket_timeout=0.5,
        )
        if await self.ping():
            logger.info("Connected to Redis successfully.")
        else:
            logger.warning("Redis unavailable. Working directly with the database.")

    async def close(self):
        if self._redis:
            await self._redis.aclose()

    async def get_json(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        try:
            val = await self._redis.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"CACHE BYPASS get {key}: Redis unavailable ({e})")
            return None

    async def set_json(self, key: str, value: Any, ttl: int):
        if not self._redis:
            return
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)  # ex = TTL у секундах
        except Exception as e:
            logger.warning(f"CACHE BYPASS set {key}: Redis unavailable ({e})")

    async def delete(self, key: str):
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
            logger.info(f"CACHE INVALIDATE {key}")
        except Exception as e:
            logger.warning(f"CACHE BYPASS delete {key}: Redis unavailable ({e})")

    async def ping(self) -> bool:
        if not self._redis:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            return False


cache = CacheClient()
