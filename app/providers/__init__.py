from app.providers.anthropic import AnthropicProvider
from app.providers.mock import MockProvider
from app.providers.openai import OpenAIProvider
from app.providers.registry import ProviderRegistry, provider_registry

provider_registry.register(MockProvider())
provider_registry.register(OpenAIProvider())
provider_registry.register(AnthropicProvider())

__all__ = [
    "AnthropicProvider",
    "MockProvider",
    "OpenAIProvider",
    "ProviderRegistry",
    "provider_registry",
]
