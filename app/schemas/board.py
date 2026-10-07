from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.canvas_element import CanvasElementRead
from app.schemas.collaborator import CollaboratorRead


class BoardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    background_color: str = Field(default="#FAF7F2", max_length=50)
    grid_type: str = Field(default="freeform", max_length=50)
    width: int = Field(default=2400, ge=400, le=10000)
    height: int = Field(default=1600, ge=400, le=10000)


class BoardCreate(BoardBase):
    owner_id: int = Field(default=1, description="User ID of board owner")


class BoardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    background_color: Optional[str] = None
    grid_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    expected_version: Optional[int] = Field(
        None, 
        description="Version expected by client for optimistic concurrency control"
    )


class BoardRead(BoardBase):
    id: int
    version: int
    owner_id: int
    elements_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardDetailRead(BoardRead):
    elements: List[CanvasElementRead] = []
    collaborators: List[CollaboratorRead] = []
