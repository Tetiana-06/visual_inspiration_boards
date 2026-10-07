import logging
from typing import AsyncGenerator
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
        connect_args = {}
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining database session in FastAPI endpoints."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
