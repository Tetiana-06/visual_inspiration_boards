from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.canvas_element import (
    CanvasElementCreate,
    CanvasElementUpdate,
    CanvasElementRead,
    BatchCanvasElementUpdate,
    BatchCanvasElementResponse,
)
from app.services.element_service import ElementService

router = APIRouter()


@router.get("/{board_id}/elements", response_model=List[CanvasElementRead], summary="Отримати всі елементи дошки")
async def get_elements(
    board_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Повертає всі елементи канвасу для зазначеної дошки, відсортовані за z-index."""
    return await ElementService.get_elements_by_board(db=db, board_id=board_id)


@router.post(
    "/{board_id}/elements",
    response_model=CanvasElementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Додати новий елемент на дошку",
)
async def create_element(
    board_id: int,
    element_in: CanvasElementCreate,
    db: AsyncSession = Depends(get_db),
):
    """Додає новий візуальний блок (стікер, зображення, палітру) на канвас дошки."""
    return await ElementService.create_element(
        db=db, board_id=board_id, element_in=element_in
    )


@router.get(
    "/{board_id}/elements/{element_id}",
    response_model=CanvasElementRead,
    summary="Отримати конкретний елемент",
)
async def get_element(
    board_id: int,
    element_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Повертає деталі конкретного елемента за його ID."""
    return await ElementService.get_element_by_id(
        db=db, board_id=board_id, element_id=element_id
    )


@router.put(
    "/{board_id}/elements/{element_id}",
    response_model=CanvasElementRead,
    summary="Оновити координати або контент елемента",
)
async def update_element(
    board_id: int,
    element_id: int,
    element_in: CanvasElementUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Оновлює параметри позиціонування або контент (JSON) окремого елемента."""
    return await ElementService.update_element(
        db=db, board_id=board_id, element_id=element_id, element_in=element_in
    )


@router.delete(
    "/{board_id}/elements/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити елемент із канвасу",
)
async def delete_element(
    board_id: int,
    element_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Видаляє елемент із дошки."""
    await ElementService.delete_element(
        db=db, board_id=board_id, element_id=element_id
    )
    return None


@router.post(
    "/{board_id}/elements/batch",
    response_model=BatchCanvasElementResponse,
    summary="Пакетна синхронізація елементів (Batch Operations / Drag & Drop)",
)
async def batch_sync_elements(
    board_id: int,
    batch_in: BatchCanvasElementUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Масове оновлення/створення елементів на канвасі в рамках однієї транзакції.
    Використовується фронтендом під час drag-and-drop переміщення або одночасного редагування,
    здійснюючи перевірку optimistic locking (expected_board_version).
    """
    return await ElementService.batch_update_elements(
        db=db, board_id=board_id, batch_in=batch_in
    )
