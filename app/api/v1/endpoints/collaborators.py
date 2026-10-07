from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.collaborator import CollaboratorCreate, CollaboratorRead
from app.services.collaborator_service import CollaboratorService

router = APIRouter()


@router.get(
    "/{board_id}/collaborators",
    response_model=List[CollaboratorRead],
    summary="Список учасників дошки",
)
async def get_collaborators(
    board_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Отримує список користувачів, які мають доступ до дошки (OWNER, EDITOR, VIEWER)."""
    return await CollaboratorService.get_collaborators(db=db, board_id=board_id)


@router.post(
    "/{board_id}/collaborators",
    response_model=CollaboratorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Додати або оновити роль співавтора",
)
async def add_collaborator(
    board_id: int,
    collab_in: CollaboratorCreate,
    db: AsyncSession = Depends(get_db),
):
    """Надає доступ користувачеві до дошки з роллю OWNER, EDITOR або VIEWER."""
    return await CollaboratorService.add_collaborator(
        db=db, board_id=board_id, collab_in=collab_in
    )


@router.delete(
    "/{board_id}/collaborators/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити доступ користувача",
)
async def remove_collaborator(
    board_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Скасовує доступ користувача до дошки."""
    await CollaboratorService.remove_collaborator(
        db=db, board_id=board_id, user_id=user_id
    )
    return None
