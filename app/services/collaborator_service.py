import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.models.collaborator import BoardCollaborator
from app.models.user import User
from app.schemas.collaborator import CollaboratorCreate, CollaboratorRead
from app.core.exceptions import NotFoundError, ValidationError
from app.core.redis import cache, board_cache_key

logger = logging.getLogger(__name__)


class CollaboratorService:
    @staticmethod
    async def get_collaborators(
        db: AsyncSession, board_id: int
    ) -> List[CollaboratorRead]:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        query = (
            select(BoardCollaborator)
            .where(BoardCollaborator.board_id == board_id)
            .options(selectinload(BoardCollaborator.user))
        )
        result = await db.execute(query)
        collabs = result.scalars().all()

        return [
            CollaboratorRead(
                id=c.id,
                board_id=c.board_id,
                user_id=c.user_id,
                role=c.role,
                created_at=c.created_at,
                user_name=c.user.full_name if c.user else None,
                user_email=c.user.email if c.user else None,
            )
            for c in collabs
        ]

    @staticmethod
    async def add_collaborator(
        db: AsyncSession, board_id: int, collab_in: CollaboratorCreate
    ) -> CollaboratorRead:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        user = await db.get(User, collab_in.user_id)
        if not user:
            raise NotFoundError("User", collab_in.user_id)

        # Check existing
        existing_query = select(BoardCollaborator).where(
            BoardCollaborator.board_id == board_id,
            BoardCollaborator.user_id == collab_in.user_id,
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        if existing:
            existing.role = collab_in.role
            await db.commit()
            await cache.delete(board_cache_key(board_id))  # співавтори входять у кеш дошки
            await db.refresh(existing)
            return CollaboratorRead(
                id=existing.id,
                board_id=existing.board_id,
                user_id=existing.user_id,
                role=existing.role,
                created_at=existing.created_at,
                user_name=user.full_name,
                user_email=user.email,
            )

        collab = BoardCollaborator(
            board_id=board_id,
            user_id=collab_in.user_id,
            role=collab_in.role,
        )
        db.add(collab)
        await db.commit()
        await cache.delete(board_cache_key(board_id))
        await db.refresh(collab)

        return CollaboratorRead(
            id=collab.id,
            board_id=collab.board_id,
            user_id=collab.user_id,
            role=collab.role,
            created_at=collab.created_at,
            user_name=user.full_name,
            user_email=user.email,
        )

    @staticmethod
    async def remove_collaborator(
        db: AsyncSession, board_id: int, user_id: int
    ) -> bool:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        if board.owner_id == user_id:
            raise ValidationError("Cannot remove the board owner from collaborators.")

        query = select(BoardCollaborator).where(
            BoardCollaborator.board_id == board_id,
            BoardCollaborator.user_id == user_id,
        )
        result = await db.execute(query)
        collab = result.scalar_one_or_none()
        if not collab:
            raise NotFoundError("Collaborator", user_id)

        await db.delete(collab)
        await db.commit()
        await cache.delete(board_cache_key(board_id))
        return True
