import asyncio

from app.models.chat_completion import ChatCompletionRequest, ChatCompletionResponse

mock_response_data = {
    "id": "chatcmpl-9A2b3c4d5e6f7g8h9i0j",
    "provider": "openai",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "logprobs": {
                "content": {
                    "token": "Hello",
                    "bytes": [72, 101, 108, 108, 111],
                    "logprob": -0.15,
                    "top_logprobs": [{"token": "Hi", "logprob": -1.2}]
                }
            },
            "message": {
                "content": "Hello! How can I help you today?",
                "refusal": "",
                "role": "assistant",
                "annotations": [],
                "audio": {
                    "id": "audio-123",
                    "data": "bXkgYXVkaW8gZGF0YQ==",  # Base64 示例
                    "expires_at": 1716480000,
                    "transcript": "Hello! How can I help you today?"
                },
                "function_call": None,
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Tokyo"}'
                        }
                    }
                ]
            }
        }
    ],
    "created": 1716480000,
    "model": "gpt-4o",
    "object": "chat.completion",
    "service_tier": "default",
    "system_fingerprint": "fp_4470942fcb",
    "usage": {
        "completion_tokens": 15,
        "prompt_tokens": 10,
        "total_tokens": 25,
        "completion_tokens_details": {"accepted_prediction_tokens": 0},
        "prompt_tokens_details": {"cached_tokens": 0}
    }
}

MockOpenAIResponse = ChatCompletionResponse(**mock_response_data)

class MockOpenAIProvider:
    def __init__(self) -> None:
        pass

    async def send_chat_request(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        await asyncio.sleep(0.5)
        return MockOpenAIResponse