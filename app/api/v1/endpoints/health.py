from datetime import datetime, timezone
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_session_factory, get_replica_session_factory
from app.core.redis import cache
from app.schemas.common import HealthResponse

router = APIRouter()


async def _ping(factory) -> str:
    """SELECT 1 до вузла БД. Lab 6: перевіряємо Primary і Replica окремо."""
    if factory is None:
        return "disabled"
    try:
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return "healthy"
    except Exception as e:
        return f"unavailable: {type(e).__name__}"


@router.get("", response_model=HealthResponse, summary="Перевірка готовності сервісу (Health Check)")
async def health_check(response: Response):
    """
    healthy   — Primary і Replica працюють;
    degraded  — Replica або Redis недоступні (читання йдуть на Primary / без кешу);
    read_only — Primary впав, але Replica жива: читати можна, писати — ні (Lab 6);
    unhealthy — немає жодного вузла БД => 503.
    """
    primary_status = await _ping(get_session_factory())
    replica_status = await _ping(get_replica_session_factory())
    redis_alive = await cache.ping()

    if primary_status != "healthy" and replica_status != "healthy":
        overall_status = "unhealthy"
        response.status_code = 503
    elif primary_status != "healthy":
        overall_status = "read_only"
    elif replica_status.startswith("unavailable") or not redis_alive:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        instance_id=settings.INSTANCE_ID,
        database=primary_status,
        replica=replica_status,
        redis="healthy" if redis_alive else "disconnected (fallback active)",
        timestamp=datetime.now(timezone.utc),
    )
