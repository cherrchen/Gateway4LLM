from fastapi.testclient import TestClient


def register_and_login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    response = client.post(
        "/api/auth/login",
        data={"username": "owner@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_user_auth_and_api_key_lifecycle(client: TestClient) -> None:
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/keys", json={"name": "demo"}, headers=headers)
    assert response.status_code == 201
    created = response.json()
    assert created["api_key"].startswith("g4l_live_")
    assert created["key_prefix"] in created["api_key"]

    response = client.get("/api/keys", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["allowed_models"] is None

    response = client.patch(
        f"/api/keys/{created['id']}",
        json={
            "name": "demo policy",
            "default_provider": "mock",
            "default_model": "mock-model",
            "allowed_models": ["mock-model"],
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["default_provider"] == "mock"
    assert response.json()["allowed_models"] == ["mock-model"]

    response = client.post(f"/api/keys/{created['id']}/revoke", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_revoked"] is True

    response = client.patch(
        f"/api/keys/{created['id']}",
        json={"default_model": "other"},
        headers=headers,
    )
    assert response.status_code == 400

    response = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {created['api_key']}"},
    )
    assert response.status_code == 401


def test_gateway_mock_request_records_redacted_log(client: TestClient) -> None:
    token = register_and_login(client)
    auth_headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/keys", json={"name": "demo"}, headers=auth_headers).json()

    response = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {created['api_key']}", "X-Gateway-Provider": "mock"},
    )
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "Mock gateway response"

    logs = client.get("/api/logs", headers=auth_headers).json()
    assert len(logs) == 1
    assert logs[0]["status_code"] == 200
    assert logs[0]["provider"] == "mock"
    assert created["api_key"] not in str(logs[0])
    assert "Authorization" not in str(logs[0])
    assert "x-api-key" not in str(logs[0]).lower()


def test_api_key_allowed_models_policy_is_enforced(client: TestClient) -> None:
    token = register_and_login(client)
    auth_headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/keys",
        json={"name": "limited", "allowed_models": ["mock-model"]},
        headers=auth_headers,
    ).json()

    response = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {created['api_key']}", "X-Gateway-Provider": "mock"},
    )
    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"]


def test_missing_or_invalid_business_key_rejected(client: TestClient) -> None:
    response = client.post(
        "/v1/responses",
        json={"model": "mock", "input": "hello"},
    )
    assert response.status_code == 401

    response = client.post(
        "/v1/responses",
        json={"model": "mock", "input": "hello"},
        headers={"Authorization": "Bearer nope"},
    )
    assert response.status_code == 401
