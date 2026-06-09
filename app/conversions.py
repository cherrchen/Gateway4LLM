from copy import deepcopy
from typing import Any

OPENAI_CHAT_FIELDS = {
    "model",
    "messages",
    "temperature",
    "top_p",
    "max_tokens",
    "max_completion_tokens",
    "stream",
    "stop",
    "tools",
    "tool_choice",
    "response_format",
    "metadata",
    "reasoning_effort",
    "parallel_tool_calls",
    "presence_penalty",
    "frequency_penalty",
    "seed",
    "user",
}

RESPONSES_FIELDS = {
    "model",
    "input",
    "instructions",
    "temperature",
    "top_p",
    "max_output_tokens",
    "stream",
    "tools",
    "tool_choice",
    "text",
    "metadata",
    "reasoning",
    "parallel_tool_calls",
    "previous_response_id",
    "truncation",
    "prompt",
}

ANTHROPIC_FIELDS = {
    "model",
    "messages",
    "system",
    "max_tokens",
    "temperature",
    "top_p",
    "top_k",
    "stream",
    "stop_sequences",
    "tools",
    "tool_choice",
    "metadata",
    "thinking",
}


def _extras(body: dict[str, Any], known: set[str], source: str) -> dict[str, Any]:
    return {f"{source}_extra": {k: deepcopy(v) for k, v in body.items() if k not in known}}


def _text_from_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") in {"text", "input_text", "output_text"}:
                    parts.append(str(item.get("text", "")))
                elif item.get("type") == "tool_result":
                    parts.append(str(item.get("content", "")))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def _metadata_with_extras(body: dict[str, Any], known: set[str], source: str) -> dict[str, Any]:
    metadata = deepcopy(body.get("metadata") or {})
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}
    metadata.update(_extras(body, known, source))
    return metadata


def chat_to_responses(body: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "model": body.get("model"),
        "input": deepcopy(body.get("messages", [])),
    }
    system_parts = [
        _text_from_content(message.get("content"))
        for message in body.get("messages", [])
        if isinstance(message, dict) and message.get("role") in {"system", "developer"}
    ]
    if system_parts:
        result["instructions"] = "\n\n".join(system_parts)
        result["input"] = [
            msg for msg in result["input"] if msg.get("role") not in {"system", "developer"}
        ]
    for old, new in (
        ("temperature", "temperature"),
        ("top_p", "top_p"),
        ("stream", "stream"),
        ("tools", "tools"),
        ("tool_choice", "tool_choice"),
        ("parallel_tool_calls", "parallel_tool_calls"),
    ):
        if old in body:
            result[new] = deepcopy(body[old])
    if "max_completion_tokens" in body:
        result["max_output_tokens"] = body["max_completion_tokens"]
    elif "max_tokens" in body:
        result["max_output_tokens"] = body["max_tokens"]
    if "response_format" in body:
        result["text"] = {"format": deepcopy(body["response_format"])}
    if "reasoning_effort" in body:
        result["reasoning"] = {"effort": body["reasoning_effort"]}
    result["metadata"] = _metadata_with_extras(body, OPENAI_CHAT_FIELDS, "openai_chat")
    return {k: v for k, v in result.items() if v is not None}


def responses_to_chat(body: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"model": body.get("model"), "messages": []}
    if body.get("instructions"):
        result["messages"].append({"role": "system", "content": body["instructions"]})
    input_value = deepcopy(body.get("input", []))
    if isinstance(input_value, str):
        result["messages"].append({"role": "user", "content": input_value})
    elif isinstance(input_value, list):
        for item in input_value:
            if isinstance(item, dict) and "role" in item:
                role = "assistant" if item.get("role") == "assistant" else "user"
                result["messages"].append({"role": role, "content": item.get("content", item)})
            else:
                result["messages"].append({"role": "user", "content": item})
    for old, new in (
        ("temperature", "temperature"),
        ("top_p", "top_p"),
        ("stream", "stream"),
        ("tools", "tools"),
        ("tool_choice", "tool_choice"),
        ("parallel_tool_calls", "parallel_tool_calls"),
    ):
        if old in body:
            result[new] = deepcopy(body[old])
    if "max_output_tokens" in body:
        result["max_completion_tokens"] = body["max_output_tokens"]
    if isinstance(body.get("text"), dict) and "format" in body["text"]:
        result["response_format"] = deepcopy(body["text"]["format"])
    if isinstance(body.get("reasoning"), dict) and "effort" in body["reasoning"]:
        result["reasoning_effort"] = body["reasoning"]["effort"]
    result["metadata"] = _metadata_with_extras(body, RESPONSES_FIELDS, "openai_responses")
    return {k: v for k, v in result.items() if v is not None}


def chat_to_anthropic(body: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "model": body.get("model"),
        "messages": [],
        "max_tokens": body.get("max_tokens") or body.get("max_completion_tokens") or 1024,
    }
    system_parts: list[str] = []
    for message in body.get("messages", []):
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role in {"system", "developer"}:
            system_parts.append(_text_from_content(message.get("content")))
        elif role == "tool":
            result["messages"].append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.get("tool_call_id"),
                            "content": _text_from_content(message.get("content")),
                        }
                    ],
                }
            )
        else:
            result["messages"].append(
                {
                    "role": "assistant" if role == "assistant" else "user",
                    "content": deepcopy(message.get("content", "")),
                }
            )
    if system_parts:
        result["system"] = "\n\n".join(system_parts)
    for old, new in (
        ("temperature", "temperature"),
        ("top_p", "top_p"),
        ("stream", "stream"),
        ("tools", "tools"),
        ("tool_choice", "tool_choice"),
    ):
        if old in body:
            result[new] = deepcopy(body[old])
    if "stop" in body:
        result["stop_sequences"] = (
            body["stop"] if isinstance(body["stop"], list) else [body["stop"]]
        )
    if "reasoning_effort" in body:
        result["thinking"] = {
            "type": "enabled",
            "gateway_reasoning_effort": body["reasoning_effort"],
        }
    result["metadata"] = _metadata_with_extras(body, OPENAI_CHAT_FIELDS, "openai_chat")
    return {k: v for k, v in result.items() if v is not None}


def anthropic_to_chat(body: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"model": body.get("model"), "messages": []}
    if body.get("system"):
        result["messages"].append({"role": "system", "content": body["system"]})
    for message in body.get("messages", []):
        if not isinstance(message, dict):
            continue
        content = deepcopy(message.get("content", ""))
        role = "assistant" if message.get("role") == "assistant" else "user"
        if isinstance(content, list):
            tool_results = [
                item
                for item in content
                if isinstance(item, dict) and item.get("type") == "tool_result"
            ]
            if tool_results:
                for item in tool_results:
                    result["messages"].append(
                        {
                            "role": "tool",
                            "tool_call_id": item.get("tool_use_id"),
                            "content": _text_from_content(item.get("content")),
                        }
                    )
                text = _text_from_content([item for item in content if item not in tool_results])
                if text:
                    result["messages"].append({"role": role, "content": text})
            else:
                result["messages"].append({"role": role, "content": content})
        else:
            result["messages"].append({"role": role, "content": content})
    for old, new in (
        ("temperature", "temperature"),
        ("top_p", "top_p"),
        ("stream", "stream"),
        ("tools", "tools"),
        ("tool_choice", "tool_choice"),
    ):
        if old in body:
            result[new] = deepcopy(body[old])
    if "max_tokens" in body:
        result["max_completion_tokens"] = body["max_tokens"]
    if "stop_sequences" in body:
        result["stop"] = deepcopy(body["stop_sequences"])
    if "thinking" in body:
        result["metadata"] = {"anthropic_thinking": deepcopy(body["thinking"])}
    result["metadata"] = {
        **result.get("metadata", {}),
        **_metadata_with_extras(body, ANTHROPIC_FIELDS, "anthropic"),
    }
    return {k: v for k, v in result.items() if v is not None}


def responses_to_anthropic(body: dict[str, Any]) -> dict[str, Any]:
    return chat_to_anthropic(responses_to_chat(body))


def anthropic_to_responses(body: dict[str, Any]) -> dict[str, Any]:
    return chat_to_responses(anthropic_to_chat(body))


def convert_request(body: dict[str, Any], source: str, target: str) -> dict[str, Any]:
    if source == target:
        return deepcopy(body)
    converters = {
        ("chat", "responses"): chat_to_responses,
        ("responses", "chat"): responses_to_chat,
        ("chat", "anthropic"): chat_to_anthropic,
        ("anthropic", "chat"): anthropic_to_chat,
        ("responses", "anthropic"): responses_to_anthropic,
        ("anthropic", "responses"): anthropic_to_responses,
    }
    return converters[(source, target)](body)
