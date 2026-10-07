from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import cache
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Перевірка працездатності сервісу (Health Check)")
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Перевіряє доступність СУБД (PostgreSQL/SQLite) та кешу Redis.
    Використовується балансувальником Nginx та Docker Healthcheck.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    redis_alive = await cache.ping()
    redis_status = "healthy" if redis_alive else "disconnected (fallback active)"

    overall_status = "healthy" if "healthy" in db_status else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.now(timezone.utc),
    )
