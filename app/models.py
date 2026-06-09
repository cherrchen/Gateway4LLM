from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)


class BusinessApiKey(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    key_hash: str = Field(index=True, unique=True)
    key_prefix: str = Field(index=True)
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=now_utc)
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


class GatewayLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    api_key_id: int | None = Field(default=None, index=True)
    api_key_prefix: str | None = None
    route: str
    provider: str
    source_interface: str
    target_interface: str
    status_code: int
    duration_ms: int
    request_meta: str = "{}"
    response_meta: str = "{}"
    error: str | None = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
