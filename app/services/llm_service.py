from app.providers.openai import OpenAIProvider
from app.models.chat import ChatRequest, ChatResponse

class LLMService:
    def __init__(self, openai_provider: OpenAIProvider) -> None:
        self.openai_provider = openai_provider
    
    async def handle_chat_completion(self, request: ChatRequest) -> ChatResponse:
        if request.provider == "openai":
            raw_res = await self.openai_provider.send_chat_request(request)
        else:
            raise ValueError(f"Unsupport provider: {request.provider}")
        
        choice = raw_res.choices[0]
        return ChatResponse(
            id=raw_res.id,
            provider=request.provider,
            model=raw_res.model,
            content=choice.message.content or "",
            usage={
                "prompt_tokens": raw_res.usage.prompt_tokens,
                "completion_tokens": raw_res.usage.completion_tokens,
                "total_tokens": raw_res.usage.total_tokens,
            }
        )