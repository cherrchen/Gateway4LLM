from fastapi import Depends
from app.core.config import Settings, get_settings
from app.services.llm_service.llm_service import LLMService

def get_openai_provider(settings: Settings = Depends(get_settings)):
    if settings.app_mode == "prod":
        from app.providers.openai import OpenAIProvider
        return OpenAIProvider(api_key=settings.openai_api_key)
    else:
        from app.providers.mock_openai import MockOpenAIProvider
        return MockOpenAIProvider()

def get_llm_service(provider = Depends(get_openai_provider)) -> LLMService:
    return LLMService(openai_provider=provider)