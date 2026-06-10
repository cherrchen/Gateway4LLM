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
    default_provider: str | None = None
    default_model: str | None = None
    allowed_models: str | None = None
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=now_utc)
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


class ProviderConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    display_name: str
    provider_type: str = Field(index=True)
    base_url: str | None = None
    api_key_env_var: str | None = None
    api_key_secret_ref: str | None = Field(default=None, repr=False)
    default_target_interface: str = "same"
    default_model_name: str | None = None
    supports_streaming: bool = True
    timeout_seconds: float = 60.0
    is_enabled: bool = True
    is_default: bool = False
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class ModelConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    provider_config_id: int = Field(foreign_key="providerconfig.id", index=True)
    public_model_name: str = Field(index=True)
    upstream_model_name: str
    supported_interfaces: str = '["chat","responses","anthropic"]'
    supports_streaming: bool = True
    default_target_interface: str = "same"
    default_parameters: str = "{}"
    is_enabled: bool = True
    is_default: bool = False
    notes: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


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
