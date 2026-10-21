import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/work", summary="Синтетичний запит для експериментів балансування (Lab 3)")
async def work(cpu_ms: int = 0, db: AsyncSession = Depends(get_db)):
    """Імітує корисну роботу: cpu_ms мілісекунд обчислень + один запит до спільної БД."""
    deadline = time.perf_counter() + cpu_ms / 1000
    while time.perf_counter() < deadline:  # CPU-навантаження (займає ядро вузла)
        pass
    await db.execute(text("SELECT 1"))  # звернення до спільного сховища
    return {"instance_id": settings.INSTANCE_ID}
