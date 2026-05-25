from typing import Literal, Union, TypedDict, Any

from pydantic import BaseModel, Field, ConfigDict

# ChatCompletionContentPart

class ChatCompletionContentPartText(BaseModel):
    text: str
    type: str = "text"

class ChatCompletionContentPartImageURL(BaseModel):
    url: str
    detail: Literal["auto", "low", "high"] | None = None

class ChatCompletionContentPartImage(BaseModel):
    image_url: ChatCompletionContentPartImageURL
    type: str = "image_url"

class ChatCompletionContentPartInputAudioObj(BaseModel):
    data: str
    format: Literal["wav", "mp3"]

class ChatCompletionContentPartInputAudio(BaseModel):
    input_audio: ChatCompletionContentPartInputAudioObj
    type: str = "input_audio"

class FileContentPartObj(BaseModel):
    file_data: str | None = None
    file_id: str | None = None
    filename: str | None = None

class FileContentPart(BaseModel):
    file: FileContentPartObj
    type: str = "file"

class ChatCompletionContentPartRefusal(BaseModel):
    refusal: str
    type: str = "refusal"

ChatCompletionContentPart = Union[ChatCompletionContentPartText, ChatCompletionContentPartImage, ChatCompletionContentPartInputAudio, FileContentPart]

# ChatCompletionMessageParam

class Audio(BaseModel):
    id: str

class ChatCompletionDeveloperMessageParam(BaseModel):
    content: str | list[ChatCompletionContentPartText]
    role: str = "developer"
    name: str | None = None

class ChatCompletionSystemMessageParam(BaseModel):
    content: str | list[ChatCompletionContentPartText]
    role: str = "system"
    name: str | None = None

class ChatCompletionUserMessageParam(BaseModel):
    content: str | list[ChatCompletionContentPart]
    role: str = "user"
    name: str | None = None

## ChatCompletionMessageToolCall

class ChatCompletionMessageFunctionToolCall(BaseModel):
    id: str
    function: dict[str, Any]
    type: str = "function"

class ChatCompletionMessageCustomToolCall(BaseModel):
    id: str
    custom: dict[str, Any]
    type: str = "custom"

ChatCompletionMessageToolCall = Union[ChatCompletionMessageFunctionToolCall, ChatCompletionMessageCustomToolCall]

class ChatCompletionAssistantMessageParam(BaseModel):
    role: str = "assistant"
    audio: Union[Audio, None] = None
    content: Union[str, ChatCompletionContentPartText, ChatCompletionContentPartRefusal, None] = None

    name: str | None = None
    refusal: str | None = None
    tool_calls: list[ChatCompletionMessageToolCall] | None = None

class ChatCompletionToolMessageParam(BaseModel):
    content: str | list[ChatCompletionContentPart]
    role: str = "tool"
    tool_call_id: str

class ChatCompletionFuntionMessageParam(BaseModel):
    content: str
    name: str
    role: str = "function"

ChatCompletionMessageParam = Union[
    ChatCompletionDeveloperMessageParam, 
    ChatCompletionSystemMessageParam, 
    ChatCompletionUserMessageParam, 
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam, 
    ChatCompletionFuntionMessageParam, 
    ]



# ChatCompletionAudioParam

class VoiceID(BaseModel):
    id: str

class ChatCompletionAudioParam(BaseModel):
    format: Literal["wav", "aac", "mp3", "flac", "opus", "pcm16"]
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"], "VoiceID"]

# ChatCompletionFuntionCallOption

class ChatCompletionFuntionCallOption(BaseModel):
    name: str

# ChatCompletionFunction

class ChatCompletionFunction(BaseModel):
    name: str
    description: str | None
    parameters: dict[str, Any]

# ChatCompletionModalities

ChatCompletionModalities = Literal["text", "audio"]

# ChatCompletionPredictionContent

class ChatCompletionPredictionContent(BaseModel):
    content: str | list[ChatCompletionContentPartText]
    type: str = "content"

# ReasoningEffort

ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]

# ResponseFormat

class JSONSchema(BaseModel):
    name: str
    description: str | None = None
    schema_: dict[str, Any] | None = Field(None, alias="schema")
    strict: bool | None = None

    model_config = ConfigDict(populate_by_name=True)

class ResponseFormatText(BaseModel):
    type: str = "text"

class ResponseFormatJSONObject(BaseModel):
    type: str = "json_object"

class ResponseFormatJSONSchema(BaseModel):
    json_schema: JSONSchema
    type: str = "json_schema"

ResponseFormat = Union[
    ResponseFormatText, 
    ResponseFormatJSONObject, 
    ResponseFormatJSONSchema, 
]

# ChatCompletionStreamOptions

class ChatCompletionStreamOptions(BaseModel):
    include_obfuscation: bool | None = None
    include_usage: bool | None = None

# ChatCompletionToolChoiceOption

ToolChoiceMode = Literal["none", "auto", "required"]

class ChatCompletionAllowedTools(BaseModel):
    mode: Literal["auto", "required"]
    tools: dict[str, Any]

class ChatCompletionAllowedToolChoice(BaseModel):
    allowed_tools: ChatCompletionAllowedTools
    type: str = "allowed_tools" 

class ChatCompletionNamedToolChoiceFunction(BaseModel):
    name: str

class ChatCompletionNamedToolChoiceCustomCustom(BaseModel):
    name: str

class ChatCompletionNamedToolChoice(BaseModel):
    function: ChatCompletionNamedToolChoiceFunction
    type: str = "function"

class ChatCompletionNamedToolChoiceCustom(BaseModel):
    custom: ChatCompletionNamedToolChoiceCustomCustom
    type: str = "custom"

ChatCompletionToolChoiceOption = Union[
    ToolChoiceMode, 
    ChatCompletionAllowedToolChoice, 
    ChatCompletionNamedToolChoice, 
    ChatCompletionNamedToolChoiceCustom, 
]

# ChatCompletionTool

class FunctionDefinition(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    strict: bool | None = None

class CustomDefinition(BaseModel):
    name: str
    description: str | None = None
    format: dict[str, Any] | None = None

class ChatCompletionFunctionTool(BaseModel):
    function: FunctionDefinition
    type: str = "function"

class ChatCompletionCustomTool(BaseModel):
    custom: CustomDefinition
    type: str = "custom"

ChatCompletionTool = Union[ChatCompletionFunctionTool, ChatCompletionCustomTool]
