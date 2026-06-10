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
    default_provider: str | None = None
    default_model: str | None = None
    allowed_models: list[str] | None = None


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    default_provider: str | None = None
    default_model: str | None = None
    allowed_models: list[str] | None = None


class ApiKeyRead(BaseModel):
    id: int
    name: str
    key_prefix: str
    default_provider: str | None = None
    default_model: str | None = None
    allowed_models: list[str] | None = None
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


class ProviderConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    display_name: str | None = None
    provider_type: str = Field(min_length=1, max_length=80)
    base_url: str | None = None
    api_key_env_var: str | None = None
    api_key_secret_ref: str | None = Field(default=None, repr=False)
    default_target_interface: str = "same"
    default_model_name: str | None = None
    supports_streaming: bool = True
    timeout_seconds: float = Field(default=60.0, gt=0)
    is_enabled: bool = True
    is_default: bool = False


class ProviderConfigUpdate(BaseModel):
    display_name: str | None = None
    base_url: str | None = None
    api_key_env_var: str | None = None
    api_key_secret_ref: str | None = Field(default=None, repr=False)
    default_target_interface: str | None = None
    default_model_name: str | None = None
    supports_streaming: bool | None = None
    timeout_seconds: float | None = Field(default=None, gt=0)
    is_enabled: bool | None = None
    is_default: bool | None = None


class ProviderConfigRead(BaseModel):
    id: int
    name: str
    display_name: str
    provider_type: str
    base_url: str | None
    api_key_env_var: str | None
    api_key_configured: bool
    default_target_interface: str
    default_model_name: str | None
    supports_streaming: bool
    timeout_seconds: float
    is_enabled: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ProviderTypeRead(BaseModel):
    name: str
    display_name: str
    supported_interfaces: list[str]
    supports_streaming: bool
    config_requirements: dict[str, Any]


class ProviderTestResult(BaseModel):
    ok: bool
    message: str


class ModelConfigCreate(BaseModel):
    provider_config_id: int
    public_model_name: str = Field(min_length=1, max_length=160)
    upstream_model_name: str = Field(min_length=1, max_length=160)
    supported_interfaces: list[str] = Field(default_factory=lambda: ["chat"])
    supports_streaming: bool = True
    default_target_interface: str = "same"
    default_parameters: dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True
    is_default: bool = False
    notes: str | None = None


class ModelConfigUpdate(BaseModel):
    public_model_name: str | None = None
    upstream_model_name: str | None = None
    supported_interfaces: list[str] | None = None
    supports_streaming: bool | None = None
    default_target_interface: str | None = None
    default_parameters: dict[str, Any] | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    notes: str | None = None


class ModelConfigRead(BaseModel):
    id: int
    provider_config_id: int
    public_model_name: str
    upstream_model_name: str
    supported_interfaces: list[str]
    supports_streaming: bool
    default_target_interface: str
    default_parameters: dict[str, Any]
    is_enabled: bool
    is_default: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RoutingSettingsRead(BaseModel):
    default_provider: str | None
    default_model: str | None
    default_target_interface: str
    environment_default_provider: str
    environment_default_model: str
    environment_default_target_interface: str


class RoutingSettingsUpdate(BaseModel):
    default_provider: str | None = None
    default_model: str | None = None
    default_target_interface: str | None = None
