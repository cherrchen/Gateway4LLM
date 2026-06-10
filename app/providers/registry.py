from fastapi import HTTPException, status

from app.providers.base import GatewayProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, GatewayProvider] = {}

    def register(self, provider: GatewayProvider, *, replace: bool = False) -> None:
        name = provider.name.lower()
        if name in self._providers and not replace:
            raise ValueError(f"Provider already registered: {name}")
        self._providers[name] = provider

    def get(self, name: str) -> GatewayProvider:
        provider = self._providers.get(name.lower())
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider type is not registered: {name}",
            )
        return provider

    def list(self) -> list[GatewayProvider]:
        return list(self._providers.values())

    def clear(self) -> None:
        self._providers.clear()


provider_registry = ProviderRegistry()
