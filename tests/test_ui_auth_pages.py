from fastapi.testclient import TestClient


def test_login_and_register_pages_render_auth_forms(client: TestClient) -> None:
    for path in ("/login", "/register"):
        response = client.get(path)

        assert response.status_code == 200
        assert "Gateway4LLM" in response.text
        assert 'method="post" action="/ui/login"' in response.text
        assert 'method="post" action="/ui/register"' in response.text


def test_authenticated_login_and_register_pages_redirect_home(client: TestClient) -> None:
    response = client.post(
        "/ui/register",
        data={"email": "owner@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    for path in ("/login", "/register"):
        response = client.get(path, follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"


def test_ui_login_hx_request_sets_cookie_and_redirect_header(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "password123"},
    )
    assert response.status_code == 201

    response = client.post(
        "/ui/login",
        data={"email": "owner@example.com", "password": "password123"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/"
    assert "access_token" in response.cookies

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text


def test_ui_register_hx_request_sets_cookie_and_redirect_header(client: TestClient) -> None:
    response = client.post(
        "/ui/register",
        data={"email": "owner@example.com", "password": "password123"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/"
    assert "access_token" in response.cookies

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text
