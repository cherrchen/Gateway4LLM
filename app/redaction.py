from collections.abc import Mapping
from typing import Any

SENSITIVE_NAMES = {
    "authorization",
    "api_key",
    "apikey",
    "x-api-key",
    "openai_api_key",
    "anthropic_api_key",
    "password",
    "token",
    "access_token",
    "secret",
}


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_")
            sensitive_parts = ("secret", "token", "api_key", "authorization", "password")
            if normalized in SENSITIVE_NAMES or any(part in normalized for part in sensitive_parts):
                clean[key_text] = "[REDACTED]"
            else:
                clean[key_text] = redact(item)
        return clean
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and (
        value.startswith("Bearer ") or value.startswith("sk-") or value.startswith("g4l_live_")
    ):
        return "[REDACTED]"
    return value


def request_meta(body: dict[str, Any], headers: Mapping[str, str]) -> dict[str, Any]:
    return {
        "headers": redact(
            {
                "content-type": headers.get("content-type"),
                "user-agent": headers.get("user-agent"),
                "x-gateway-provider": headers.get("x-gateway-provider"),
                "x-gateway-target-interface": headers.get("x-gateway-target-interface"),
            }
        ),
        "body_keys": sorted(body.keys()),
        "model": body.get("model"),
        "stream": body.get("stream", False),
        "metadata": redact(body.get("metadata") or body.get("gateway") or {}),
    }


def response_meta(body: Any) -> dict[str, Any]:
    if isinstance(body, Mapping):
        return {
            "body_keys": sorted(str(key) for key in body.keys()),
            "id": body.get("id"),
            "model": body.get("model"),
            "usage": redact(body.get("usage")),
        }
    return {"type": type(body).__name__}
