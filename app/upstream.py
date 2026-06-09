from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings


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


def _upstream_url(settings: Settings, provider: str, interface: str) -> str:
    if provider == "openai":
        path = "responses" if interface == "responses" else "chat/completions"
        return f"{settings.openai_base_url.rstrip('/')}/{path}"
    if provider == "anthropic":
        return f"{settings.anthropic_base_url.rstrip('/')}/messages"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported provider: {provider}",
    )


def _headers(settings: Settings, provider: str) -> dict[str, str]:
    if provider == "openai":
        if not settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OpenAI upstream key is not configured")
        return {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise HTTPException(status_code=503, detail="Anthropic upstream key is not configured")
        return {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": settings.anthropic_version,
            "Content-Type": "application/json",
        }
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported provider: {provider}",
    )


async def post_upstream(
    provider: str,
    interface: str,
    body: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
        response = await client.post(
            _upstream_url(settings, provider, interface),
            headers=_headers(settings, provider),
            json=body,
        )
    try:
        payload = response.json()
    except ValueError:
        payload = {"text": response.text}
    return response.status_code, payload


async def stream_upstream(
    provider: str,
    interface: str,
    body: dict[str, Any],
) -> AsyncIterator[bytes]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            _upstream_url(settings, provider, interface),
            headers=_headers(settings, provider),
            json=body,
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk
