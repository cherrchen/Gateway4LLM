from datetime import datetime, timezone
import secrets

from sqlmodel import SQLModel, Field, Column, DateTime, func


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_default_username() -> str:
    return f"User{secrets.token_hex(6)}"


class Base(SQLModel):
    pass


class TimeStampMixin(SQLModel):
    created_at: datetime | None = Field(
        default_factory=utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    updated_at: datetime | None = Field(
        default_factory=utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            onupdate=func.now(),
        ),
    )


class SoftDeleteTimeStampMixin(SQLModel):
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
        ),
    )
