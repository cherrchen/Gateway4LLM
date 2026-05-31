import secrets
from uuid import UUID
from datetime import datetime, timedelta

from pydantic import BaseModel, Field


def default_apikey_name() -> str:
    return secrets.token_hex(4)

class TokenPayload(BaseModel):
    sub: str
    exp: int | None = None

class APIKeyCreate(BaseModel):
    name: str | None = Field(default_factory=default_apikey_name, min_length=1, max_length=50)
    expire_time: int | None = None

class APIKeyCreatedResponse(BaseModel):
    id: int
    name: str
    api_key: str
    prefix: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None

    user_id: UUID

class APIKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
    user_id: UUID