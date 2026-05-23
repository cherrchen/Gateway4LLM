from openai import AsyncOpenAI
from app.models.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from app.core.config import get_settings

class OpenAIProvider:
    def __init__(self, api_key) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key,
        )

    async def send_chat_request(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        raw_messages = [
            msg.model_dump() for msg in payload.messages
        ]

        response = await self.client.chat.completions.create(
            model=payload.model,
            messages=raw_messages,
            temperature=payload.temperature,
        )

        return ChatCompletionResponse(**response.model_dump())