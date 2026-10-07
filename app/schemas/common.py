from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.board import BoardRead
from app.schemas.canvas_element import CanvasElementRead


class HealthResponse(BaseModel):
    status: str
    version: str
    instance_id: str
    database: str
    redis: str
    timestamp: datetime


class BoardExportResponse(BaseModel):
    export_version: str = "1.0"
    exported_at: datetime
    board: BoardRead
    elements: List[CanvasElementRead]
    summary: Dict[str, Any]
