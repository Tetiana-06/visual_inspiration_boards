from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.board import BoardCreate, BoardUpdate, BoardRead, BoardDetailRead
from app.schemas.common import BoardExportResponse
from app.services.board_service import BoardService

router = APIRouter()


@router.get("", response_model=List[BoardRead], summary="Отримати список дощок")
async def get_boards(
    skip: int = Query(0, ge=0, description="Пагінація: зміщення"),
    limit: int = Query(50, ge=1, le=100, description="Пагінація: ліміт записів"),
    owner_id: Optional[int] = Query(None, description="Фільтр за ID власника"),
    search: Optional[str] = Query(None, description="Пошук за назвою дошки"),
    db: AsyncSession = Depends(get_db),
):
    """Повертає список дощок користувачів із кількістю елементів та параметрами оформлення."""
    return await BoardService.get_boards(
        db=db, skip=skip, limit=limit, owner_id=owner_id, search=search
    )


@router.post("", response_model=BoardDetailRead, status_code=status.HTTP_201_CREATED, summary="Створити нову дошку")
async def create_board(
    board_in: BoardCreate,
    db: AsyncSession = Depends(get_db),
):
    """Створює нову віртуальну дошку натхнення та призначає користувача OWNER."""
    return await BoardService.create_board(db=db, board_in=board_in)


@router.get("/{board_id}", response_model=BoardDetailRead, summary="Отримати детальну інформацію про дошку")
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Повертає повні дані дошки разом із усіма елементами канвасу та списком співавторів."""
    return await BoardService.get_board_by_id(db=db, board_id=board_id)


@router.patch("/{board_id}", response_model=BoardDetailRead, summary="Оновити параметри дошки (Optimistic Locking)")
async def update_board(
    board_id: int,
    board_in: BoardUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Оновлює властивості дошки (заголовок, опис, фон, розмір).
    Якщо передано expected_version, перевіряється відсутність конфліктів паралельного редагування (HTTP 409).
    """
    return await BoardService.update_board(db=db, board_id=board_id, board_in=board_in)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити дошку")
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Видаляє дошку та каскадно всі її елементи."""
    await BoardService.delete_board(db=db, board_id=board_id)
    return None


@router.get("/{board_id}/export", response_model=BoardExportResponse, summary="Експорт дошки та елементів (High-Load Scenario)")
async def export_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Генерує повний агрегований знімок дошки для експорту або архівації.
    Слугує прикладом ресурсомісткої операції серіалізації/читання в системі.
    """
    return await BoardService.export_board(db=db, board_id=board_id)
