from typing import Literal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_mode: Literal["dev", "prod"] = "dev"

    openai_api_key: str = "example-api-key"
    database_url: str = "sqlite+aiosqlite:///db.sqlite"

    jwt_secret_key: str = "set-as-random-key-in-your-environment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    api_key_provider_note: str = "gate"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()