from typing import Literal, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.chat_completion.component import (
    ChatCompletionMessageParam, 
    ChatCompletionAudioParam, 
    ChatCompletionFuntionCallOption, 
    ChatCompletionFunction, 
    ChatCompletionModalities, 
    ChatCompletionPredictionContent, 
    ReasoningEffort, 
    ResponseFormat, 
    ChatCompletionStreamOptions, 
    ChatCompletionToolChoiceOption, 
    ChatCompletionTool, 
    )

Messages = list[ChatCompletionMessageParam]

class ChatCompletionRequest(BaseModel):
    provider: str = "openai"
    
    messages: list[ChatCompletionMessageParam]
    model: str = "gpt-5-mini"
    audio: ChatCompletionAudioParam | None = None

    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0)

    function_call: Literal["none", "auto"] | ChatCompletionFuntionCallOption | None = None
    functions: list[ChatCompletionFunction] | None = None

    logit_bias: dict[str, float] | None = None
    logprobs: bool | None = None

    max_completion_tokens: int | None = None
    max_tokens: int | None = None

    metadata: dict[str, Any] | None = None
    
    modalities: list[ChatCompletionModalities] | None = None
    n: int | None = Field(None, ge=1, le=128)
    parallel_tool_calls: bool | None = None
    prediction: ChatCompletionPredictionContent | None = None

    presence_penalty: float | None = Field(None, ge=-2, le=2)
    prompt_cache_key: str | None = None

    prompt_cache_retention: Literal["in_memory", "24h"] | None = None
    reasoning_effort: ReasoningEffort | None = None

    response_format: ResponseFormat | None = None
    safety_ifentifier: str | None = Field(None, max_length=64)

    seed: int | None = Field(None, ge=-9223372036854776000, le=9223372036854776000)

    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None

    stop: str | list[str] | None = None
    store: bool | None = None

    stream: bool | None = None
    stream_options: ChatCompletionStreamOptions | None = None
    @model_validator(mode="after")
    def validate_stream_option(self):
        if self.stream in (False, None) and self.stream_options is not None:
            raise ValueError("stream_options should only be set when you set stream as true.")
        return self

    temperature: float | None = Field(None, ge=0, le=2)

    tool_choice: ChatCompletionToolChoiceOption | None = None
    tools: list[ChatCompletionTool] | None = None

    top_logprobs: int | None = Field(None,ge=0, le=20)
    @model_validator(mode="after")
    def validate_logprobs(self):
        if self.logprobs == False and self.top_logprobs is not None:
            raise ValueError("top_logbrobs should only be used when logprobs is set to true.")
        return self
    
    top_p: float | None = Field(None, ge=0, le=1)

    verbosity: Literal["low", "medium", "high"] | None = None

    web_search_options: dict | None = None

