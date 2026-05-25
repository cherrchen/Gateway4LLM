from typing import Literal, Union, Any
from pydantic import BaseModel, Field, AnyUrl, BeforeValidator

from app.schemas.base import DataUrl

class ContextManagement(BaseModel):
    type: str
    compact_threshold: int | None = Field(None, ge=1000)

class ResponseConversationParam(BaseModel):
    id: str

ResponseIncludable = Literal[
    "file_search_call.results", 
    "web_search_call.results", 
    "web_search_call.action.sources",
    "message.input_image.image_url", 
    "computer_call_output.output.image_url", 
    "code_interpreter_call.outputs", 
    "reasoning.encrypted_content", 
    "message.output_text.logprobs", 
]

class ResponseInputText(BaseModel):
    text: str
    type: str = "input_text"

class ResponseInputImage(BaseModel):
    detail: Literal["low", "high", "auto", "original"] = "auto"
    type: str = "input_image"
    file_id: str | None = None
    image_url: AnyUrl | DataUrl | None = None

class ResponseInputFile(BaseModel):
    type: str = "input_file"
    detail: Literal["low", "high"] | None = None

    file_data: str | None = None
    file_id: str | None = None

    file_url: AnyUrl | None = None
    filename: str | None = None

ResponseInputMessageContentList = list[ResponseInputText | ResponseInputImage | ResponseInputFile]

# Input

class EasyInputMessage(BaseModel):
    content: str | ResponseInputMessageContentList
    role: Literal["user", "assistant", "system", "developer"]
    phase: Literal["commentary", "final_answer"] | None = None
    type: str | None = "message"

class Message(BaseModel):
    content: ResponseInputMessageContentList
    role: Literal["user", "system", "developer"]
    status: Literal["in_progress", "completed", "incomplete"] | None = None
    type: str | None = "message"

class ResponseOutputText(BaseModel):
    annotations: list[dict]
    logprobs: list[dict]
    text: str
    type: str = "output_text"

class ResponseOutputRefusal(BaseModel):
    refusal: str
    type: str = "refusal"

class ResponseOutputMessage(BaseModel):
    id: str
    content: list[ResponseOutputText | ResponseOutputRefusal]
    role: str = "assistant"
    status: Literal["in_progress", "completed", "incomplete"]
    type: str = "message"
    phase: Literal["commentary", "final_answer"] | None = None

class FileSearchCall(BaseModel):
    pass

class ComputerCall(BaseModel):
    pass

class ComputerCallOutput(BaseModel):
    pass

class WebSearchCall(BaseModel):
    pass

class FunctionCall(BaseModel):
    pass

class FunctionCallOutput(BaseModel):
    pass

class ToolSearchCall(BaseModel):
    pass

class ToolSearchOutput(BaseModel):
    pass

class Reasoning(BaseModel):
    pass

class Compaction(BaseModel):
    pass

class ImageGenerationCall(BaseModel):
    pass

class CodeInterpreterCall(BaseModel):
    pass

class LocalShellCall(BaseModel):
    pass

class LocalShellCallOutput(BaseModel):
    pass

class ShellCall(BaseModel):
    pass

class ShellCallOutput(BaseModel):
    pass

class ApplyPatchCall(BaseModel):
    pass

class ApplyPatchCallOutput(BaseModel):
    pass

class McpListTools(BaseModel):
    pass

class McpApprovalRequest(BaseModel):
    pass

class McpApprovalResponse(BaseModel):
    pass

class McpCall(BaseModel):
    pass

class CustomToolCallOutput(BaseModel):
    pass

class CustomToolCall(BaseModel):
    pass

class CompactionTrigger(BaseModel):
    pass

class ItemReference(BaseModel):
    pass

InputItemList = list[
    Union[
        EasyInputMessage,
        Message,
        ResponseOutputMessage,
        FileSearchCall,
        ComputerCall,
        ComputerCallOutput,
        WebSearchCall,
        FunctionCall,
        FunctionCallOutput,
        ToolSearchCall,
        ToolSearchOutput,
        Reasoning,
        Compaction,
        ImageGenerationCall,
        CodeInterpreterCall,
        LocalShellCall,
        LocalShellCallOutput,
        ShellCall,
        ShellCallOutput,
        ApplyPatchCall,
        ApplyPatchCallOutput,
        McpListTools,
        McpApprovalRequest,
        McpApprovalResponse,
        McpCall,
        CustomToolCallOutput,
        CustomToolCall,
        CompactionTrigger,
        ItemReference,
    ]
]

# prompt
class ResponsePrompt(BaseModel):
    id: str
    variables: str | ResponseInputText | ResponseInputImage | ResponseInputFile | None = None
    version: str | None = None

# Reasoning
class Reasoning(BaseModel):
    effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = None
    generate_summary: Literal["auto", "concise", "detailed"] | None = Field(None, description="Deprecated")
    summary: Literal["auto", "concise", "detailed"] | None = None

# StreamOptions
class StreamOptions(BaseModel):
    include_obfuscation: bool | None = None

# ResponseTextConfig
class ResponseTextConfig(BaseModel):
    format: dict[str, Any] ## unset
    verbosity: Literal["low", "medium", "high"]