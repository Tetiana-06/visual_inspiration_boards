from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=List[UserRead], summary="Отримати список користувачів")
async def get_users(
    db: AsyncSession = Depends(get_db),
):
    """Повертає список зареєстрованих користувачів платформи."""
    return await UserService.get_users(db=db)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Створити нового користувача")
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Реєстрація нового користувача (профілю)."""
    return await UserService.create_user(db=db, user_in=user_in)


@router.get("/{user_id}", response_model=UserRead, summary="Отримати профіль користувача")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Повертає профіль користувача за його ідентифікатором."""
    return await UserService.get_user_by_id(db=db, user_id=user_id)
