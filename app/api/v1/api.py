from fastapi import APIRouter
from app.api.v1.endpoints import boards, elements, collaborators, users, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Status"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(boards.router, prefix="/boards", tags=["Boards"])
api_router.include_router(elements.router, prefix="/boards", tags=["Canvas Elements"])
api_router.include_router(collaborators.router, prefix="/boards", tags=["Collaborators"])
