from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-5-mini"
    messages: list[ChatMessage]
    temperature: None | float = 1

class ChatResponse(BaseModel):
    id: str
    provider: str
    model: str
    content: str
    usage: dict[str, int]