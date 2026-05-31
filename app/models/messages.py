from uuid import UUID
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, Column, DateTime, func

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.api_keys import APIKey


class Message(Base, table=True):
    __tablename__ = "messages"

    id: int | None = Field(None, primary_key=True, nullable=False)

    user_id: UUID | None = Field(foreign_key="users.id", index=True)
    user: Optional["User"] = Relationship(back_populates="messages")

    api_key_id: int | None = Field(foreign_key="api_keys.id", index=True)
    api_key: Optional["APIKey"] = Relationship(back_populates="messages")

    time: datetime | None = Field(
        default_factory=utcnow,
        sa_column=Column(
            DateTime(timezone=True), 
            server_default=func.now(),
            nullable=False,
        )
    )
    model: str | None = None
    prompt_tokens: int | None = None