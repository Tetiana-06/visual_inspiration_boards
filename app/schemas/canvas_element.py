from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CanvasElementBase(BaseModel):
    element_type: str = Field(..., description="Element type: note, image, palette, sticker, text")
    x: float = Field(default=0.0, description="X coordinate on canvas")
    y: float = Field(default=0.0, description="Y coordinate on canvas")
    width: float = Field(default=260.0, description="Width of bounding box")
    height: float = Field(default=260.0, description="Height of bounding box")
    z_index: int = Field(default=1, description="Layer stack index")
    content: Dict[str, Any] = Field(default_factory=dict, description="JSON payload (text, color, url, font)")


class CanvasElementCreate(CanvasElementBase):
    pass


class CanvasElementUpdate(BaseModel):
    element_type: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    z_index: Optional[int] = None
    content: Optional[Dict[str, Any]] = None


class CanvasElementRead(CanvasElementBase):
    id: int
    board_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchElementItem(BaseModel):
    id: Optional[int] = Field(None, description="Existing element ID to update, or None to create new")
    element_type: str = Field(default="note")
    x: float
    y: float
    width: float = 260.0
    height: float = 260.0
    z_index: int = 1
    content: Dict[str, Any] = Field(default_factory=dict)


class BatchCanvasElementUpdate(BaseModel):
    expected_board_version: Optional[int] = Field(
        None, 
        description="Current board version for optimistic concurrency control"
    )
    elements: List[BatchElementItem] = Field(..., description="List of elements to batch create or update")


class BatchCanvasElementResponse(BaseModel):
    updated_count: int
    new_board_version: int
    elements: List[CanvasElementRead]
