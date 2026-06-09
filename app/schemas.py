from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class ApiKeyRead(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_revoked: bool
    created_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None


class ApiKeyCreated(ApiKeyRead):
    api_key: str


class GatewayLogRead(BaseModel):
    id: int
    user_id: int | None
    api_key_id: int | None
    api_key_prefix: str | None
    route: str
    provider: str
    source_interface: str
    target_interface: str
    status_code: int
    duration_ms: int
    request_meta: dict[str, Any]
    response_meta: dict[str, Any]
    error: str | None
    created_at: datetime
