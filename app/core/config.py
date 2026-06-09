from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="G4L_", env_file=".env", extra="ignore")

    app_name: str = "Gateway4LLM"
    database_url: str = "sqlite:///./gateway4llm.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12
    api_key_hash_secret: str = "change-me-api-key-pepper"
    default_provider: str = "mock"
    default_target_interface: str = "same"
    upstream_timeout_seconds: float = 60.0
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    anthropic_version: str = "2023-06-01"


@lru_cache
def get_settings() -> Settings:
    return Settings()
