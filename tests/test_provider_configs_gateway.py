from fastapi.testclient import TestClient

from tests.test_auth_keys_gateway import register_and_login


def _auth(client: TestClient) -> tuple[dict[str, str], str]:
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    api_key = client.post("/api/keys", json={"name": "demo"}, headers=headers).json()["api_key"]
    return headers, api_key


def test_provider_config_api_hides_secret_and_can_disable(client: TestClient) -> None:
    headers, api_key = _auth(client)

    types = client.get("/api/provider-types", headers=headers)
    assert types.status_code == 200
    assert {"mock", "openai", "anthropic"}.issubset({item["name"] for item in types.json()})

    response = client.post(
        "/api/providers",
        json={
            "name": "mock-alt",
            "provider_type": "mock",
            "display_name": "Mock Alt",
            "api_key_secret_ref": "sk-hidden",
            "is_enabled": True,
        },
        headers=headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["api_key_configured"] is True
    assert "api_key_secret_ref" not in payload
    assert "sk-hidden" not in str(payload)

    detail = client.get(f"/api/providers/{payload['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "mock-alt"

    disabled = client.patch(
        f"/api/providers/{payload['id']}",
        json={"is_enabled": False},
        headers=headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_enabled"] is False

    enabled = client.post(f"/api/providers/{payload['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["is_enabled"] is True

    defaulted = client.post(f"/api/providers/{payload['id']}/set-default", headers=headers)
    assert defaulted.status_code == 200
    assert defaulted.json()["is_default"] is True

    delete_attempt = client.delete(f"/api/providers/{payload['id']}", headers=headers)
    assert delete_attempt.status_code == 405
    assert "Disable it instead" in delete_attempt.json()["detail"]

    disabled = client.post(f"/api/providers/{payload['id']}/disable", headers=headers)
    assert disabled.status_code == 200

    gateway = client.post(
        "/v1/responses",
        json={"model": "mock-model", "input": "hello"},
        headers={"Authorization": f"Bearer {api_key}", "X-Gateway-Provider": "mock-alt"},
    )
    assert gateway.status_code == 400
    assert "disabled" in gateway.json()["detail"]


def test_model_config_api_maps_model_and_blocks_disabled(client: TestClient) -> None:
    headers, api_key = _auth(client)
    providers = client.get("/api/providers", headers=headers).json()
    provider = next(item for item in providers if item["name"] == "mock")

    created = client.post(
        "/api/models",
        json={
            "provider_config_id": provider["id"],
            "public_model_name": "public-test",
            "upstream_model_name": "upstream-test",
            "supported_interfaces": ["chat", "responses", "anthropic"],
        },
        headers=headers,
    )
    assert created.status_code == 201
    detail = client.get(f"/api/models/{created.json()['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["public_model_name"] == "public-test"

    duplicate = client.post(
        "/api/models",
        json={
            "provider_config_id": provider["id"],
            "public_model_name": "public-test",
            "upstream_model_name": "upstream-other",
            "supported_interfaces": ["chat"],
        },
        headers=headers,
    )
    assert duplicate.status_code == 409

    response = client.post(
        "/v1/chat/completions",
        json={"model": "public-test", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {api_key}", "X-Gateway-Provider": "mock"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "upstream-test"

    disabled = client.patch(
        f"/api/models/{created.json()['id']}",
        json={"is_enabled": False},
        headers=headers,
    )
    assert disabled.status_code == 200
    enabled = client.post(f"/api/models/{created.json()['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["is_enabled"] is True
    defaulted = client.post(f"/api/models/{created.json()['id']}/set-default", headers=headers)
    assert defaulted.status_code == 200
    assert defaulted.json()["is_default"] is True
    delete_attempt = client.delete(f"/api/models/{created.json()['id']}", headers=headers)
    assert delete_attempt.status_code == 405

    disabled = client.post(f"/api/models/{created.json()['id']}/disable", headers=headers)
    assert disabled.status_code == 200
    response = client.post(
        "/v1/chat/completions",
        json={"model": "public-test", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {api_key}", "X-Gateway-Provider": "mock"},
    )
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_gateway_provider_selection_errors_and_interface_validation(client: TestClient) -> None:
    headers, api_key = _auth(client)
    providers = client.get("/api/providers", headers=headers).json()
    openai = next(item for item in providers if item["name"] == "openai")
    patched = client.patch(
        f"/api/providers/{openai['id']}",
        json={"is_enabled": True, "api_key_secret_ref": "sk-test"},
        headers=headers,
    )
    assert patched.status_code == 200
    model = client.post(
        "/api/models",
        json={
            "provider_config_id": openai["id"],
            "public_model_name": "gpt-test",
            "upstream_model_name": "gpt-test-upstream",
            "supported_interfaces": ["chat", "responses", "anthropic"],
        },
        headers=headers,
    )
    assert model.status_code == 201

    missing_provider = client.post(
        "/v1/responses",
        json={"model": "mock-model", "input": "hello"},
        headers={"Authorization": f"Bearer {api_key}", "X-Gateway-Provider": "missing"},
    )
    assert missing_provider.status_code == 400
    assert "not configured" in missing_provider.json()["detail"]

    missing_model = client.post(
        "/v1/responses",
        json={"model": "not-configured", "input": "hello"},
        headers={"Authorization": f"Bearer {api_key}", "X-Gateway-Provider": "mock"},
    )
    assert missing_model.status_code == 400
    assert "not configured" in missing_model.json()["detail"]

    unsupported = client.post(
        "/v1/chat/completions",
        json={"model": "gpt-test", "messages": [{"role": "user", "content": "hello"}]},
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Gateway-Provider": "openai",
            "X-Gateway-Target-Interface": "anthropic",
        },
    )
    assert unsupported.status_code == 400
    assert "does not support target interface" in unsupported.json()["detail"]


def test_gateway_body_provider_and_streaming_mock_interfaces(client: TestClient) -> None:
    _, api_key = _auth(client)
    headers = {"Authorization": f"Bearer {api_key}"}

    responses = client.post(
        "/v1/responses",
        json={"model": "mock-model", "input": "hello", "gateway": {"provider": "mock"}},
        headers=headers,
    )
    assert responses.status_code == 200
    assert responses.json()["output"][0]["content"][0]["text"] == "Mock gateway response"

    anthropic = client.post(
        "/v1/messages",
        json={
            "model": "mock-model",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10,
            "stream": True,
            "gateway": {"provider": "mock"},
        },
        headers=headers,
    )
    assert anthropic.status_code == 200
    assert "message_start" in anthropic.text


def test_routing_settings_api_updates_configured_defaults(client: TestClient) -> None:
    headers, _ = _auth(client)
    current = client.get("/api/settings/routing", headers=headers)
    assert current.status_code == 200
    assert current.json()["environment_default_provider"] == "mock"

    updated = client.patch(
        "/api/settings/routing",
        json={
            "default_provider": "mock",
            "default_model": "mock-model",
            "default_target_interface": "same",
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["default_provider"] == "mock"
