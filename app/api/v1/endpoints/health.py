from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import cache
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Перевірка готовності сервісу (Health Check)")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Перевіряє доступність СУБД та кешу Redis.
    200 — вузол готовий; 503 — БД недоступна, вузол не повинен отримувати трафік.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    redis_alive = await cache.ping()
    redis_status = "healthy" if redis_alive else "disconnected (fallback active)"

    if db_status != "healthy":
        overall_status = "unhealthy"
        response.status_code = 503  # без БД вузол не може обслуговувати запити
    elif not redis_alive:
        overall_status = "degraded"  # працює без кешу
    else:
        overall_status = "healthy"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        instance_id=settings.INSTANCE_ID,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.now(timezone.utc),
    )
