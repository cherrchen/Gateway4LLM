import pytest
from fastapi import HTTPException

from app.providers.mock import MockProvider
from app.providers.registry import ProviderRegistry


def test_registry_register_get_and_list() -> None:
    registry = ProviderRegistry()
    provider = MockProvider()

    registry.register(provider)

    assert registry.get("mock") is provider
    assert registry.list() == [provider]


def test_registry_unregistered_provider_raises_clear_error() -> None:
    registry = ProviderRegistry()

    with pytest.raises(HTTPException) as exc:
        registry.get("missing")

    assert exc.value.status_code == 400
    assert "not registered" in str(exc.value.detail)


def test_registry_duplicate_provider_is_explicit() -> None:
    registry = ProviderRegistry()
    registry.register(MockProvider())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(MockProvider())
