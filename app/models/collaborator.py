from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BoardCollaborator(Base):
    __tablename__ = "board_collaborators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("boards.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="EDITOR", nullable=False)  # 'OWNER', 'EDITOR', 'VIEWER'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_collaborator"),
    )

    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="collaborations")
