from fastapi.testclient import TestClient

from tests.test_auth_keys_gateway import register_and_login


def test_htmx_provider_list_create_update_and_test(client: TestClient) -> None:
    register_and_login(client)

    response = client.get("/ui/providers")
    assert response.status_code == 200
    assert "mock" in response.text

    created = client.post(
        "/ui/providers",
        data={
            "name": "mock-ui",
            "provider_type": "mock",
            "display_name": "Mock UI",
            "default_target_interface": "same",
            "timeout_seconds": "60",
            "supports_streaming": "true",
            "is_enabled": "true",
        },
    )
    assert created.status_code == 200
    assert "mock-ui" in created.text

    providers = client.get("/api/providers", headers=_jwt_header(client)).json()
    provider_id = next(item["id"] for item in providers if item["name"] == "mock-ui")
    updated = client.post(
        f"/ui/providers/{provider_id}",
        data={
            "display_name": "Mock UI Disabled",
            "default_target_interface": "same",
            "timeout_seconds": "60",
        },
    )
    assert updated.status_code == 200
    assert "Mock UI Disabled" in updated.text
    assert "禁用" in updated.text

    tested = client.post(f"/ui/providers/{provider_id}/test")
    assert tested.status_code == 200
    assert "mock-ui" in tested.text
    assert "is ready" in tested.text


def test_htmx_model_list_create_update(client: TestClient) -> None:
    register_and_login(client)
    headers = _jwt_header(client)
    providers = client.get("/api/providers", headers=headers).json()
    provider = next(item for item in providers if item["name"] == "mock")

    response = client.get("/ui/models")
    assert response.status_code == 200
    assert "mock-model" in response.text

    created = client.post(
        "/ui/models",
        data={
            "provider_config_id": str(provider["id"]),
            "public_model_name": "ui-model",
            "upstream_model_name": "ui-upstream",
            "supported_interfaces": ["chat", "responses"],
            "default_target_interface": "same",
            "default_parameters": '{"temperature":0.1}',
            "supports_streaming": "true",
            "is_enabled": "true",
            "notes": "from ui",
        },
    )
    assert created.status_code == 200
    assert "ui-model" in created.text

    models = client.get("/api/models", headers=headers).json()
    model = next(item for item in models if item["public_model_name"] == "ui-model")
    updated = client.post(
        f"/ui/models/{model['id']}",
        data={
            "public_model_name": "ui-model",
            "upstream_model_name": "ui-upstream-2",
            "supported_interfaces": ["chat"],
            "default_target_interface": "chat",
            "default_parameters": "{}",
        },
    )
    assert updated.status_code == 200
    assert "ui-upstream-2" in updated.text
    assert "禁用" in updated.text


def test_htmx_provider_model_catalog_create_and_sync(client: TestClient) -> None:
    register_and_login(client)
    headers = _jwt_header(client)
    providers = client.get("/api/providers", headers=headers).json()
    provider = next(item for item in providers if item["name"] == "mock")

    response = client.get("/ui/provider-models")
    assert response.status_code == 200
    assert "mock-model" in response.text
    assert "需要后端补充" not in response.text

    created = client.post(
        "/ui/provider-models",
        data={
            "provider_config_id": str(provider["id"]),
            "upstream_model_name": "ui-provider-model",
            "display_name": "UI Provider Model",
            "supported_interfaces": ["chat", "responses"],
            "default_target_interface": "same",
            "capabilities": "json, tools",
            "health_status": "healthy",
            "supports_streaming": "true",
            "is_enabled": "true",
        },
    )
    assert created.status_code == 200
    assert "ui-provider-model" in created.text
    assert "json" in created.text

    updated_mapping = client.post(
        "/ui/models",
        data={
            "provider_config_id": str(provider["id"]),
            "public_model_name": "ui-synced-public",
            "upstream_model_name": "ui-synced-upstream",
            "supported_interfaces": ["chat"],
            "default_target_interface": "same",
            "default_parameters": "{}",
            "is_enabled": "true",
        },
    )
    assert updated_mapping.status_code == 200

    synced = client.post(f"/ui/providers/{provider['id']}/provider-models/sync")
    assert synced.status_code == 200
    assert "ui-synced-upstream" in synced.text
    assert "ui-synced-public" in synced.text


def test_htmx_routing_rules_create_update(client: TestClient) -> None:
    register_and_login(client)
    headers = _jwt_header(client)
    provider_models = client.get("/api/provider-models", headers=headers).json()
    provider_model = next(
        item for item in provider_models if item["upstream_model_name"] == "mock-model"
    )

    response = client.get("/ui/routing-rules")
    assert response.status_code == 200
    assert "需要后端补充" not in response.text
    assert "Create Routing Rule" in response.text

    created = client.post(
        "/ui/routing-rules",
        data={
            "name": "UI fixed route",
            "public_model_name": "ui-route-public",
            "strategy": "fixed",
            "provider_model_id": str(provider_model["id"]),
            "fallback_provider_model_ids": "",
            "weight_config": "{}",
            "custom_config": "{}",
            "default_parameters": "{}",
            "priority": "20",
            "is_enabled": "true",
        },
    )
    assert created.status_code == 200
    assert "UI fixed route" in created.text
    assert "ui-route-public" in created.text

    rules = client.get("/api/routing-rules", headers=headers).json()
    rule = next(item for item in rules if item["public_model_name"] == "ui-route-public")
    updated = client.post(
        f"/ui/routing-rules/{rule['id']}",
        data={
            "name": "UI fixed route updated",
            "public_model_name": "ui-route-public",
            "strategy": "fixed",
            "provider_model_id": str(provider_model["id"]),
            "fallback_provider_model_ids": "",
            "weight_config": "{}",
            "custom_config": "{}",
            "default_parameters": '{"top_p": 1}',
            "priority": "10",
        },
    )
    assert updated.status_code == 200
    assert "UI fixed route updated" in updated.text
    assert "disabled / 禁用" in updated.text


def _jwt_header(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("access_token")
    return {"Authorization": f"Bearer {token}"}
