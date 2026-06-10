from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.models import ModelConfig, ProviderConfig
from app.providers.base import GatewayProvider, ProviderResponse


class OpenAIProvider(GatewayProvider):
    name = "openai"
    display_name = "OpenAI"
    supported_interfaces = {"chat", "responses"}
    supports_streaming = True

    def validate_config(self, config: ProviderConfig) -> None:
        super().validate_config(config)
        if not self._api_key(config):
            raise HTTPException(status_code=503, detail="OpenAI provider key is not configured")

    async def send(
        self,
        interface: str,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> ProviderResponse:
        self.validate_config(config)
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(
                self._url(config, interface),
                headers=self._headers(config),
                json=body,
            )
        try:
            payload = response.json()
        except ValueError:
            payload = {"text": response.text}
        return ProviderResponse(status_code=response.status_code, body=payload)

    def stream(
        self,
        interface: str,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> AsyncIterator[bytes]:
        self.validate_config(config)

        async def iterator() -> AsyncIterator[bytes]:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    self._url(config, interface),
                    headers=self._headers(config),
                    json=body,
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

        return iterator()

    def _url(self, config: ProviderConfig, interface: str) -> str:
        base_url = (config.base_url or get_settings().openai_base_url).rstrip("/")
        path = "responses" if interface == "responses" else "chat/completions"
        return f"{base_url}/{path}"

    def _headers(self, config: ProviderConfig) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key(config)}",
            "Content-Type": "application/json",
        }

    def _api_key(self, config: ProviderConfig) -> str | None:
        return self.resolve_api_key(config) or get_settings().openai_api_key
