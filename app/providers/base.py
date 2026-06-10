import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from app.models import ModelConfig, ProviderConfig

GatewayInterface = str


@dataclass(frozen=True)
class ProviderResponse:
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str] | None = None


class GatewayProvider(ABC):
    name: str
    display_name: str
    supported_interfaces: set[GatewayInterface]
    supports_streaming: bool = True

    def validate_config(self, config: ProviderConfig) -> None:
        if config.provider_type != self.name:
            detail = (
                f"Provider config '{config.name}' uses type "
                f"'{config.provider_type}', not '{self.name}'"
            )
            raise HTTPException(
                status_code=400,
                detail=detail,
            )

    def resolve_api_key(self, config: ProviderConfig) -> str | None:
        for value in (config.api_key_secret_ref, config.api_key_env_var):
            if not value:
                continue
            if value.startswith("env:"):
                return os.getenv(value.split(":", 1)[1])
            env_value = os.getenv(value)
            if env_value:
                return env_value
            if value.startswith("sk-"):
                return value
        return None

    @abstractmethod
    async def send(
        self,
        interface: GatewayInterface,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        interface: GatewayInterface,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError
