from uuid import UUID
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Column, Relationship, DateTime, func

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.messages import Message


class APIKey(Base, table=True):
    __tablename__ = "api_keys"

    id: int | None = Field(default=None, primary_key=True, nullable=False)

    name: str | None = Field(default=None, nullable=True)
    key_hash: str = Field(index=True, unique=True, nullable=False)
    prefix: str = Field(index=True, nullable=False)

    is_active: bool | None = Field(default=True, nullable=False)
    created_at: datetime | None = Field(
        default_factory=utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )

    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
        )
    )

    last_used_at: datetime | None = Field(default=None)
    expire_time: timedelta | None = Field(default=None, nullable=True)
    expires_at: datetime | None = Field(default=None, nullable=True)

    user_id: UUID | None = Field(foreign_key="users.id", index=True)
    user: Optional["User"] = Relationship(back_populates="api_keys")

    messages: list["Message"] = Relationship(back_populates="api_key")