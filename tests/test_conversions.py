from app.conversions import (
    anthropic_to_chat,
    anthropic_to_responses,
    chat_to_anthropic,
    chat_to_responses,
    responses_to_anthropic,
    responses_to_chat,
)


def test_chat_to_responses_preserves_core_fields_and_extras() -> None:
    body = {
        "model": "gpt-test",
        "messages": [
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "hello"},
        ],
        "tools": [{"type": "function", "function": {"name": "lookup"}}],
        "response_format": {"type": "json_object"},
        "reasoning_effort": "low",
        "vendor_only": {"x": 1},
    }
    converted = chat_to_responses(body)
    assert converted["instructions"] == "be brief"
    assert converted["input"] == [{"role": "user", "content": "hello"}]
    assert converted["text"]["format"] == {"type": "json_object"}
    assert converted["reasoning"]["effort"] == "low"
    assert converted["metadata"]["openai_chat_extra"]["vendor_only"] == {"x": 1}


def test_responses_to_chat_round_trip_shape() -> None:
    converted = responses_to_chat(
        {"model": "gpt-test", "instructions": "sys", "input": "hello", "max_output_tokens": 22}
    )
    assert converted["messages"][0] == {"role": "system", "content": "sys"}
    assert converted["messages"][1] == {"role": "user", "content": "hello"}
    assert converted["max_completion_tokens"] == 22


def test_chat_to_anthropic_maps_system_stop_and_tools() -> None:
    converted = chat_to_anthropic(
        {
            "model": "claude-test",
            "messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "hello"},
                {"role": "tool", "tool_call_id": "call_1", "content": "done"},
            ],
            "stop": "END",
            "max_tokens": 10,
        }
    )
    assert converted["system"] == "sys"
    assert converted["stop_sequences"] == ["END"]
    assert converted["messages"][1]["content"][0]["type"] == "tool_result"


def test_anthropic_to_chat_maps_tool_results_and_extras() -> None:
    converted = anthropic_to_chat(
        {
            "model": "claude-test",
            "system": "sys",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "ok"}],
                }
            ],
            "thinking": {"type": "enabled"},
            "beta_flag": True,
        }
    )
    assert converted["messages"][0] == {"role": "system", "content": "sys"}
    assert converted["messages"][1]["role"] == "tool"
    assert converted["metadata"]["anthropic_extra"]["beta_flag"] is True


def test_cross_converters_are_callable() -> None:
    response_body = {"model": "x", "input": "hello"}
    anthropic = responses_to_anthropic(response_body)
    assert anthropic["messages"][0]["role"] == "user"

    responses = anthropic_to_responses(
        {"model": "x", "messages": [{"role": "user", "content": "hi"}]}
    )
    assert responses["input"][0]["role"] == "user"
