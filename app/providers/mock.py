from collections.abc import AsyncIterator
from typing import Any

from app.models import ModelConfig, ProviderConfig
from app.providers.base import GatewayProvider, ProviderResponse


class MockProvider(GatewayProvider):
    name = "mock"
    display_name = "Mock"
    supported_interfaces = {"chat", "responses", "anthropic"}
    supports_streaming = True

    async def send(
        self,
        interface: str,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> ProviderResponse:
        self.validate_config(config)
        return ProviderResponse(status_code=200, body=mock_response(interface, body))

    def stream(
        self,
        interface: str,
        body: dict[str, Any],
        config: ProviderConfig,
        model: ModelConfig,
    ) -> AsyncIterator[bytes]:
        self.validate_config(config)
        return mock_stream(interface)


def mock_response(interface: str, body: dict[str, Any]) -> dict[str, Any]:
    model = body.get("model", "mock-model")
    if interface == "responses":
        return {
            "id": "resp_mock",
            "object": "response",
            "status": "completed",
            "model": model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Mock gateway response"}],
                }
            ],
            "usage": {"input_tokens": 1, "output_tokens": 3, "total_tokens": 4},
        }
    if interface == "anthropic":
        return {
            "id": "msg_mock",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": "Mock gateway response"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 1, "output_tokens": 3},
        }
    return {
        "id": "chatcmpl_mock",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Mock gateway response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 3, "total_tokens": 4},
    }


def mock_stream(interface: str) -> AsyncIterator[bytes]:
    async def iterator() -> AsyncIterator[bytes]:
        if interface == "anthropic":
            yield (
                b"event: message_start\n"
                b'data: {"type":"message_start","message":{"id":"msg_mock",'
                b'"type":"message","role":"assistant","content":[]}}\n\n'
            )
            yield (
                b"event: content_block_delta\n"
                b'data: {"type":"content_block_delta","index":0,"delta":'
                b'{"type":"text_delta","text":"Mock gateway response"}}\n\n'
            )
            yield b'event: message_stop\ndata: {"type":"message_stop"}\n\n'
        else:
            yield (
                b'data: {"id":"mock","choices":[{"delta":'
                b'{"content":"Mock gateway response"}}]}\n\n'
            )
            yield b"data: [DONE]\n\n"

    return iterator()
