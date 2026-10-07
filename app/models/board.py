from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    background_color: Mapped[str] = mapped_column(String(50), default="#FAF7F2")
    grid_type: Mapped[str] = mapped_column(String(50), default="freeform")
    width: Mapped[int] = mapped_column(Integer, default=2400)
    height: Mapped[int] = mapped_column(Integer, default=1600)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic Concurrency Control

    owner_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="boards")
    elements: Mapped[list["CanvasElement"]] = relationship(
        "CanvasElement", 
        back_populates="board", 
        cascade="all, delete-orphan",
        order_by="CanvasElement.z_index"
    )
    collaborators: Mapped[list["BoardCollaborator"]] = relationship(
        "BoardCollaborator", 
        back_populates="board", 
        cascade="all, delete-orphan"
    )
