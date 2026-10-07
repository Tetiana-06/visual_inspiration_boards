import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def get_users(db: AsyncSession) -> List[User]:
        result = await db.execute(select(User).order_by(User.id.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        # Check email uniqueness
        existing_result = await db.execute(
            select(User).where(User.email == user_in.email)
        )
        if existing_result.scalar_one_or_none():
            raise ValidationError(f"User with email '{user_in.email}' already exists.")

        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            avatar_url=user_in.avatar_url,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
