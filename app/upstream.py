from collections.abc import AsyncIterator
from typing import Any

import app.providers  # noqa: F401
from app.models import ModelConfig, ProviderConfig
from app.providers.registry import provider_registry


def _legacy_config(provider: str) -> tuple[ProviderConfig, ModelConfig]:
    config = ProviderConfig(
        name=provider,
        display_name=provider,
        provider_type=provider,
        default_target_interface="same",
    )
    model = ModelConfig(
        provider_config_id=0,
        public_model_name="legacy",
        upstream_model_name="legacy",
    )
    return config, model


async def post_upstream(
    provider: str,
    interface: str,
    body: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    config, model = _legacy_config(provider)
    result = await provider_registry.get(provider).send(interface, body, config, model)
    return result.status_code, result.body


def stream_upstream(
    provider: str,
    interface: str,
    body: dict[str, Any],
) -> AsyncIterator[bytes]:
    config, model = _legacy_config(provider)
    return provider_registry.get(provider).stream(interface, body, config, model)
