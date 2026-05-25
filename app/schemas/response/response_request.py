from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.response.component import (
    ContextManagement,
    ResponseConversationParam,
    ResponseIncludable,
    InputItemList,
    ResponsePrompt,
    Reasoning,
    StreamOptions,
    ResponseTextConfig,
)


class ResponseRequest(BaseModel):
    background: bool | None = None
    context_management: list[ContextManagement] | None = None

    conversation: str | ResponseConversationParam | None = None
    include: list[ResponseIncludable] | None = None

    input: str | InputItemList
    instructions: str | None = None

    max_output_tokens: int | None = Field(None, ge=16)
    max_tool_calls: int | None = None
    metadata: dict[str, Any] | None = None

    parallel_tool_calls: bool | None = None
    previous_response_id: str | None = None

    prompt: ResponsePrompt | None = None

    prompt_cache_key: str | None = None
    prompt_cache_retention: Literal["in_memory", "24h"] | None = None
    reasoning: Reasoning | None = None

    safety_identifier: str | None = Field(None, max_length=64)
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None

    store: bool | None = None

    stream: bool | None = None
    stream_options: StreamOptions | None = None

    @model_validator(mode="after")
    def validate_stream_option(self):
        if self.stream in (False, None) and self.stream_options is not None:
            raise ValueError("stream_options should only be set when you set stream as true.")
        return self

    temperature: float | None = Field(None, ge=0, le=2)

    text: ResponseTextConfig | None = None

    tool_choice: None  ## unset
    tools: None        ## unset

    top_logprobs: float | None = Field(None, ge=0, le=2)
    top_p: float | None = Field(None, ge=0, le=1)

    truncation: Literal["auto", "disabled"] | None = None
    user: str | None = Field(None, description="Deprecated")

