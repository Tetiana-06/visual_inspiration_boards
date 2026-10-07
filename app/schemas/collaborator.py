from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CollaboratorBase(BaseModel):
    user_id: int
    role: str = Field(default="EDITOR", pattern="^(OWNER|EDITOR|VIEWER)$")


class CollaboratorCreate(CollaboratorBase):
    pass


class CollaboratorRead(BaseModel):
    id: int
    board_id: int
    user_id: int
    role: str
    created_at: datetime
    user_name: str | None = None
    user_email: str | None = None

    model_config = ConfigDict(from_attributes=True)
