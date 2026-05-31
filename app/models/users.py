from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship

from app.models.base import Base, TimeStampMixin, SoftDeleteTimeStampMixin, get_default_username, utcnow

if TYPE_CHECKING:
    from app.models.api_keys import APIKey
    from app.models.messages import Message


class User(Base, TimeStampMixin, SoftDeleteTimeStampMixin, table=True):
    __tablename__ = "users"

    id: UUID | None = Field(default_factory=uuid4, primary_key=True, nullable=False)
    username: str | None = Field(default_factory=get_default_username, nullable=False)
    password: str | None = Field(nullable=False)

    email: EmailStr | None = Field(default=None, nullable=True)

    is_active: bool | None = Field(default=True, nullable=False)

    messages: list["Message"] = Relationship(back_populates="user")
    api_keys: list["APIKey"] = Relationship(back_populates="user")