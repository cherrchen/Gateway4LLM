import asyncio

from app.models.chat import ChatRequest

class MockOpenAIResponse:
    def __init__(self, content: str, model: str):
        self.id = "openai-mock"
        self.model = model
        self.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": content})})()
        ]
        self.usage = type("Usage", (), {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20})()

class MockOpenAIProvider:
    def __init__(self) -> None:
        pass

    async def send_chat_request(self, payload: ChatRequest) -> MockOpenAIResponse:
        await asyncio.sleep(0.5)
        mock_content = "Hello! This is a simple mock response from your local LLM Gateway."
        return MockOpenAIResponse(content=mock_content, model=payload.model)