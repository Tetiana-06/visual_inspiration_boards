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


# ---------------- Lab 6: стан реплікації та Replication Lag ----------------
from app.core.database import get_session_factory, get_replica_session_factory  # noqa: E402


@router.get("/replication", summary="Стан реплікації Primary -> Replica (Lab 6)")
async def replication_status():
    """
    primary.replicas  — які репліки підключені до Primary і наскільки відстають
                        (lag_bytes — скільки байт WAL ще не застосовано, replay_lag — час).
    replica           — чи вузол справді в режимі репліки (in_recovery=true) і до якої позиції WAL він дійшов.
    """
    result = {"primary": None, "replica": None}
    try:
        async with get_session_factory()() as s:
            lsn = (await s.execute(text("SELECT pg_current_wal_lsn()::text"))).scalar()
            rows = (await s.execute(text(
                "SELECT client_addr::text, state, sync_state, "
                "pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)::bigint AS lag_bytes, "
                "replay_lag::text FROM pg_stat_replication"
            ))).mappings().all()
            result["primary"] = {"wal_lsn": lsn, "replicas": [dict(r) for r in rows]}
    except Exception as e:
        result["primary"] = f"unavailable: {type(e).__name__}"

    factory = get_replica_session_factory()
    if factory is None:
        result["replica"] = "disabled"
        return result
    try:
        async with factory() as s:
            row = (await s.execute(text(
                "SELECT pg_is_in_recovery() AS in_recovery, "
                "pg_last_wal_replay_lsn()::text AS replayed_lsn, "
                "pg_last_xact_replay_timestamp()::text AS last_replayed_tx_at"
            ))).mappings().one()
            result["replica"] = dict(row)
    except Exception as e:
        result["replica"] = f"unavailable: {type(e).__name__}"
    return result
