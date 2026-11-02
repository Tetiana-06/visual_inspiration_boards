import logging
from typing import AsyncGenerator
from fastapi import HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        # If running outside docker and postgres isn't running or db url is sqlite
        connect_args = {"timeout": 2}  # Lab 6: не чекати довго, якщо вузол БД впав
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}

        try:
            _engine = create_async_engine(
                db_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
        except Exception as e:
            logger.warning(
                f"Failed to create primary engine with {db_url}: {e}. Falling back to SQLite."
            )
            _engine = create_async_engine(
                settings.SQLITE_FALLBACK_URL,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False},
            )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


# =====================================================================
# Lab 6: Read/Write Separation (Multi-Pool Manager)
#   - пул "primary": усі записи + критичні (strict) читання
#   - пул "replica": некритичні (eventual) читання
# Кожен ендпоінт сам обирає залежність: get_db (Primary) або get_read_db (Replica).
# =====================================================================

STICKY_COOKIE = "rw_sticky"  # ставиться після запису (див. app/main.py), живе STICKY_TTL_SEC секунд

READ_ONLY_MESSAGE = (
    "Primary DB is unavailable: the system is in Read-Only mode. "
    "Writes and strictly consistent reads are temporarily blocked."
)

_replica_factory: async_sessionmaker[AsyncSession] | None = None


def get_replica_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Пул з'єднань до Replica. None => репліка вимкнена (Single Primary Topology)."""
    global _replica_factory
    if not (settings.USE_REPLICA and settings.DATABASE_REPLICA_URL):
        return None
    if _replica_factory is None:
        engine = create_async_engine(
            settings.DATABASE_REPLICA_URL,
            pool_pre_ping=True,
            connect_args={"timeout": 2},
        )
        _replica_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )
    return _replica_factory


async def _connect_first_alive(nodes, response: Response) -> AsyncSession | None:
    """Пробує вузли по черзі й повертає сесію до першого живого (це і є Failover/Fallback)."""
    for name, factory in nodes:
        session = factory()
        try:
            await session.connection()  # реальне підключення: відмова вузла ловиться тут
        except (SQLAlchemyError, OSError) as e:
            logger.warning(f"DB node '{name}' is unavailable: {type(e).__name__}")
            await session.close()
            continue
        response.headers["X-DB-Node"] = name  # видно в curl, який вузол обслужив запит
        return session
    return None


async def get_db(response: Response) -> AsyncGenerator[AsyncSession, None]:
    """Primary: записи та Strictly Consistent читання (Explicit Primary Routing)."""
    session = await _connect_first_alive([("primary", get_session_factory())], response)
    if session is None:
        # Primary впав => записи блокуються контрольованою помилкою, бекенд НЕ падає
        raise HTTPException(status_code=503, detail=READ_ONLY_MESSAGE)
    async with session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_read_db(request: Request, response: Response) -> AsyncGenerator[AsyncSession, None]:
    """
    Eventual Consistent читання. Порядок вибору вузла:
      1. репліка вимкнена           -> Primary
      2. є cookie rw_sticky         -> Primary (Read-After-Write: користувач щойно щось записав)
      3. інакше                     -> Replica, а якщо вона впала -> Primary (Primary Fallback)
    """
    primary = ("primary", get_session_factory())
    replica_factory = get_replica_session_factory()

    if replica_factory is None:
        nodes = [primary]
    elif request.cookies.get(STICKY_COOKIE):
        nodes = [primary, ("replica", replica_factory)]
    else:
        nodes = [("replica", replica_factory), primary]

    session = await _connect_first_alive(nodes, response)
    if session is None:
        raise HTTPException(status_code=503, detail="No database node is available.")
    async with session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
