from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.redis import cache
from app.core.exceptions import DomainException
from app.services.init_db import init_database
from app.api.v1.api import api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database schema & Redis connection
    logger.info("Starting up Visual Inspiration Boards platform...")
    await init_database()
    await cache.connect()
    yield
    # Shutdown: Clean up connections
    logger.info("Shutting down Visual Inspiration Boards platform...")
    await cache.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## Платформа інтерактивних дошок візуального натхнення (Collaborative Moodboard Canvas Platform)
    
    Архітектурний каркас (MVP) для Лабораторної роботи №1:
    * **Доменні сутності:** User, Board, CanvasElement, BoardCollaborator.
    * **Бізнес-орієнтовані операції:** CRUD дощок, додавання стікерів/картинок/палітр, масовий batch update з Optimistic Concurrency Control, експорт дошки (High-Load scenario).
    * **Персистентність:** PostgreSQL (реляційна цілісність + JSONB поля для гнучкого контенту).
    * **Кешування та стан:** Redis клієнт для збереження знімків дощок.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom domain exception handler
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static files and UI
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Welcome to Visual Inspiration Boards API. Visit /docs for OpenAPI specs."}
else:
    @app.get("/", include_in_schema=False)
    async def serve_fallback():
        return {"message": "Welcome to Visual Inspiration Boards API. Visit /docs for OpenAPI specs."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
