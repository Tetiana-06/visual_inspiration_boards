from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CanvasElement(Base):
    __tablename__ = "canvas_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("boards.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    element_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'image', 'note', 'palette', 'sticker', 'text'
    
    # 2D Canvas positioning & bounding box
    x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    width: Mapped[float] = mapped_column(Float, default=260.0, nullable=False)
    height: Mapped[float] = mapped_column(Float, default=260.0, nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Flexible visual payload (colors, text notes, typography, image URLs)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="elements")
