from uuid import uuid4, UUID
from pydantic import EmailStr
from sqlmodel import Field

from app.models.base import Base, TimeStampMixin, SoftDeleteTimeStampMixin, get_default_username


class User(Base, TimeStampMixin, SoftDeleteTimeStampMixin, tabel=True):
    __tablename__ = "users"

    id: UUID | None = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)
    username: str | None = Field(default_factory=get_default_username, nullable=False)
    password: str | None = Field(nullable=False)

    email: EmailStr | None = Field(default=None, nullable=True)

    is_active: bool | None = Field(default=True, nullable=False)