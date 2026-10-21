import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Visual Inspiration Boards (Collaborative Moodboard Platform)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/visual_boards"
    )
    # Fallback to SQLite if PostgreSQL is not available locally for offline testing
    SQLITE_FALLBACK_URL: str = "sqlite+aiosqlite:///./visual_boards.db"
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = True
    
    # Instance identification for stateless multi-node scaling (Lab 2)
    INSTANCE_ID: str = os.getenv("INSTANCE_ID", "backend-local")

    # Lab 3: штучна затримка кожного запиту (мс) — імітація "повільного" вузла
    ARTIFICIAL_DELAY_MS: int = 0

    # Lab 4: TTL кешу деталей дошки (с). Свіжість гарантує інвалідація, TTL — страховка
    BOARD_CACHE_TTL: int = 300
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
