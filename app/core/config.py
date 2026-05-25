from typing import Literal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_mode: Literal["dev", "prod"] = "dev"

    openai_api_key: str = "example-api-key"
    database_url: str = "sqlite+aiosqlite:///db.sqlite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()