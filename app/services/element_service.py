import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.models.canvas_element import CanvasElement
from app.schemas.canvas_element import (
    CanvasElementCreate,
    CanvasElementUpdate,
    BatchCanvasElementUpdate,
    BatchCanvasElementResponse,
)
from app.core.exceptions import NotFoundError, ConcurrencyConflictError
from app.core.redis import cache, board_cache_key

logger = logging.getLogger(__name__)


class ElementService:
    @staticmethod
    async def get_elements_by_board(
        db: AsyncSession, board_id: int
    ) -> List[CanvasElement]:
        # Verify board exists
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        query = (
            select(CanvasElement)
            .where(CanvasElement.board_id == board_id)
            .order_by(CanvasElement.z_index.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_element_by_id(
        db: AsyncSession, board_id: int, element_id: int
    ) -> CanvasElement:
        query = select(CanvasElement).where(
            CanvasElement.id == element_id,
            CanvasElement.board_id == board_id,
        )
        result = await db.execute(query)
        element = result.scalar_one_or_none()
        if not element:
            raise NotFoundError("CanvasElement", element_id)
        return element

    @staticmethod
    async def create_element(
        db: AsyncSession, board_id: int, element_in: CanvasElementCreate
    ) -> CanvasElement:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        element = CanvasElement(
            board_id=board_id,
            element_type=element_in.element_type,
            x=element_in.x,
            y=element_in.y,
            width=element_in.width,
            height=element_in.height,
            z_index=element_in.z_index,
            content=element_in.content,
        )
        db.add(element)
        board.version += 1
        await db.commit()
        await db.refresh(element)

        await cache.delete(board_cache_key(board_id))
        return element

    @staticmethod
    async def update_element(
        db: AsyncSession,
        board_id: int,
        element_id: int,
        element_in: CanvasElementUpdate,
    ) -> CanvasElement:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        element = await ElementService.get_element_by_id(db, board_id, element_id)
        update_data = element_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(element, field, value)

        board.version += 1
        await db.commit()
        await db.refresh(element)

        await cache.delete(board_cache_key(board_id))
        return element

    @staticmethod
    async def delete_element(
        db: AsyncSession, board_id: int, element_id: int
    ) -> bool:
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        element = await ElementService.get_element_by_id(db, board_id, element_id)
        await db.delete(element)
        board.version += 1
        await db.commit()

        await cache.delete(board_cache_key(board_id))
        return True

    @staticmethod
    async def batch_update_elements(
        db: AsyncSession,
        board_id: int,
        batch_in: BatchCanvasElementUpdate,
    ) -> BatchCanvasElementResponse:
        """
        Batch update/create elements with optimistic concurrency control.
        Critical high-throughput business logic endpoint for canvas drag-and-drop sync.
        """
        board = await db.get(Board, board_id)
        if not board:
            raise NotFoundError("Board", board_id)

        # Optimistic locking check
        if batch_in.expected_board_version is not None:
            if board.version != batch_in.expected_board_version:
                raise ConcurrencyConflictError(
                    current_version=board.version,
                    provided_version=batch_in.expected_board_version,
                )

        # Fetch existing elements for this board
        existing_elements_query = select(CanvasElement).where(
            CanvasElement.board_id == board_id
        )
        result = await db.execute(existing_elements_query)
        existing_dict = {el.id: el for el in result.scalars().all()}

        saved_elements: List[CanvasElement] = []

        for item in batch_in.elements:
            if item.id and item.id in existing_dict:
                # Update existing element
                target = existing_dict[item.id]
                target.element_type = item.element_type
                target.x = item.x
                target.y = item.y
                target.width = item.width
                target.height = item.height
                target.z_index = item.z_index
                if item.content:
                    target.content = item.content
                saved_elements.append(target)
            else:
                # Create new element
                new_el = CanvasElement(
                    board_id=board_id,
                    element_type=item.element_type,
                    x=item.x,
                    y=item.y,
                    width=item.width,
                    height=item.height,
                    z_index=item.z_index,
                    content=item.content,
                )
                db.add(new_el)
                saved_elements.append(new_el)

        board.version += 1
        await db.commit()

        # Refresh instances
        for el in saved_elements:
            await db.refresh(el)

        # Invalidate cache
        await cache.delete(board_cache_key(board_id))

        return BatchCanvasElementResponse(
            updated_count=len(saved_elements),
            new_board_version=board.version,
            elements=saved_elements,
        )
