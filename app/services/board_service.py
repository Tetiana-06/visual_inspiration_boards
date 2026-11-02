import logging
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.models.collaborator import BoardCollaborator
from app.models.canvas_element import CanvasElement
from app.schemas.board import BoardCreate, BoardUpdate, BoardDetailRead
from app.core.exceptions import NotFoundError, ConcurrencyConflictError
from app.core.config import settings
from app.core.redis import cache, board_cache_key

logger = logging.getLogger(__name__)


class BoardService:
    @staticmethod
    async def get_boards(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        owner_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[dict]:
        query = select(Board).options(selectinload(Board.elements))
        
        if owner_id is not None:
            query = query.where(Board.owner_id == owner_id)
        if search:
            query = query.where(Board.title.ilike(f"%{search}%"))

        query = query.offset(skip).limit(limit).order_by(Board.updated_at.desc())
        result = await db.execute(query)
        boards = result.scalars().all()

        response = []
        for b in boards:
            b_dict = {
                "id": b.id,
                "title": b.title,
                "description": b.description,
                "background_color": b.background_color,
                "grid_type": b.grid_type,
                "width": b.width,
                "height": b.height,
                "version": b.version,
                "owner_id": b.owner_id,
                "elements_count": len(b.elements),
                "created_at": b.created_at,
                "updated_at": b.updated_at,
            }
            response.append(b_dict)
        return response

    @staticmethod
    async def get_board_by_id(db: AsyncSession, board_id: int) -> Board:
        query = (
            select(Board)
            .where(Board.id == board_id)
            .options(
                selectinload(Board.elements),
                selectinload(Board.collaborators).selectinload(BoardCollaborator.user),
            )
        )
        result = await db.execute(query)
        board = result.scalar_one_or_none()
        if not board:
            raise NotFoundError("Board", board_id)
        return board

    @staticmethod
    async def get_board_detail_cached(db: AsyncSession, board_id: int) -> tuple[dict, str]:
        """Lab 4: Cache-Aside. Повертає (дані дошки, "HIT" | "MISS")."""
        key = board_cache_key(board_id)
        cached = await cache.get_json(key)  # 1. Key Lookup
        if cached is not None:
            logger.info(f"CACHE HIT {key}")
            return cached, "HIT"  # 2. Cache Hit: без звернення до БД

        # 3. Cache Miss: читаємо з БД, кладемо в кеш з TTL, повертаємо
        board = await BoardService.get_board_by_id(db, board_id)
        data = BoardDetailRead.model_validate(board).model_dump(mode="json")
        await cache.set_json(key, data, ttl=settings.BOARD_CACHE_TTL)
        logger.info(f"CACHE MISS {key}")
        return data, "MISS"

    @staticmethod
    async def create_board(db: AsyncSession, board_in: BoardCreate) -> Board:
        board = Board(
            title=board_in.title,
            description=board_in.description,
            background_color=board_in.background_color,
            grid_type=board_in.grid_type,
            width=board_in.width,
            height=board_in.height,
            version=1,
            owner_id=board_in.owner_id,
        )
        db.add(board)
        await db.flush()

        # Add owner as OWNER collaborator
        collab = BoardCollaborator(
            board_id=board.id,
            user_id=board.owner_id,
            role="OWNER"
        )
        db.add(collab)
        await db.commit()
        await db.refresh(board)
        return await BoardService.get_board_by_id(db, board.id)

    @staticmethod
    async def update_board(
        db: AsyncSession, 
        board_id: int, 
        board_in: BoardUpdate
    ) -> Board:
        board = await BoardService.get_board_by_id(db, board_id)

        # Optimistic Concurrency Control check
        if board_in.expected_version is not None:
            if board.version != board_in.expected_version:
                raise ConcurrencyConflictError(
                    current_version=board.version,
                    provided_version=board_in.expected_version,
                )

        update_data = board_in.model_dump(exclude_unset=True, exclude={"expected_version"})
        for field, value in update_data.items():
            setattr(board, field, value)

        board.version += 1
        await db.commit()
        await db.refresh(board)

        # Invalidate cache
        await cache.delete(board_cache_key(board_id))
        return await BoardService.get_board_by_id(db, board.id)

    @staticmethod
    async def delete_board(db: AsyncSession, board_id: int) -> bool:
        board = await BoardService.get_board_by_id(db, board_id)
        await db.delete(board)
        await db.commit()
        await cache.delete(board_cache_key(board_id))
        return True

    @staticmethod
    async def export_board(db: AsyncSession, board_id: int) -> dict:
        board = await BoardService.get_board_by_id(db, board_id)
        
        type_counts: dict[str, int] = {}
        for el in board.elements:
            type_counts[el.element_type] = type_counts.get(el.element_type, 0) + 1

        summary = {
            "total_elements": len(board.elements),
            "element_breakdown": type_counts,
            "canvas_dimensions": f"{board.width}x{board.height}",
            "grid_type": board.grid_type,
            "collaborators_count": len(board.collaborators),
        }

        # Build clean export dictionary
        elements_data = [
            {
                "id": el.id,
                "board_id": el.board_id,
                "element_type": el.element_type,
                "x": el.x,
                "y": el.y,
                "width": el.width,
                "height": el.height,
                "z_index": el.z_index,
                "content": el.content,
                "created_at": el.created_at,
                "updated_at": el.updated_at,
            }
            for el in board.elements
        ]

        board_data = {
            "id": board.id,
            "title": board.title,
            "description": board.description,
            "background_color": board.background_color,
            "grid_type": board.grid_type,
            "width": board.width,
            "height": board.height,
            "version": board.version,
            "owner_id": board.owner_id,
            "elements_count": len(board.elements),
            "created_at": board.created_at,
            "updated_at": board.updated_at,
        }

        from datetime import datetime, timezone
        return {
            "export_version": "1.0",
            "exported_at": datetime.now(timezone.utc),
            "board": board_data,
            "elements": elements_data,
            "summary": summary,
        }
