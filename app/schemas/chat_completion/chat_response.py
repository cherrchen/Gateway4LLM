from typing import Literal, Any

from pydantic import BaseModel, Field

class CompletionUsage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    completion_tokens_details: dict[str, Any] | None = None
    prompt_tokens_details: dict[str, Any] | None = None

class ChatCompletionMessageFunctionToolCall(BaseModel):
    id: str
    function: dict
    type: str = "function"

class ChatCompletionMessageCustomToolCall(BaseModel):
    id: str
    custom: dict
    type: str = "custom"

ChatCompletionMessageToolCall = ChatCompletionMessageFunctionToolCall | ChatCompletionMessageCustomToolCall

class ChatCompletionAudio(BaseModel):
    id: str
    data: str
    expires_at: int
    transcript: str

class ChatCompletionMessage(BaseModel):
    content: str
    refusal: str | None = None
    role: str = "assistant"
    annotations: list[dict] | None = None
    audio: ChatCompletionAudio | None = None
    function_call: dict | None = None
    tool_calls: list[ChatCompletionMessageToolCall] | None = None

class ChatCompletionTokenLogprob(BaseModel):
    token: str | None = None
    bytes: list[int] | None = None
    logprob: float | None = None
    top_logprobs: list[dict] | None = None

class ChatCompletionResponseChoicesLogprobs(BaseModel):
    content: list[ChatCompletionTokenLogprob]
    refusal: list[ChatCompletionTokenLogprob]

class ChatCompletionResponseChoices(BaseModel):
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"]
    index: int
    logprobs: ChatCompletionResponseChoicesLogprobs | None = None
    message: ChatCompletionMessage

class ChatCompletionResponse(BaseModel):
    id: str
    provider: str
    choices: list[ChatCompletionResponseChoices]
    created: int
    model: str
    object: str = "chat.completion"
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None
    system_fingerprint: str | None = None
    usage: CompletionUsage | None = None