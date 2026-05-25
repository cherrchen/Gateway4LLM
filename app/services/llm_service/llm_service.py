from app.providers.openai import OpenAIProvider
from app.schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse

class LLMService:
    def __init__(self, openai_provider: OpenAIProvider) -> None:
        self.openai_provider = openai_provider
    
    async def handle_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        if request.provider == "openai":
            raw_res = await self.openai_provider.send_chat_request(request)
        else:
            raise ValueError(f"Unsupported provider: {request.provider}")
        
        return raw_res