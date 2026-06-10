import json
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response
from httpx import ASGITransport, AsyncClient

from app.routers.ui.templates import templates

router = APIRouter(prefix="/ui")


@router.post("/gateway-test", response_class=HTMLResponse)
async def gateway_test(
    request: Request,
    api_key: str = Form(),
    interface: str = Form(),
    prompt: str = Form(),
    provider: str | None = Form(default=None),
) -> Response:
    path = {
        "chat": "/v1/chat/completions",
        "responses": "/v1/responses",
        "anthropic": "/v1/messages",
    }[interface]
    payload: dict[str, Any] = {
        "model": "mock-model",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128,
    }
    if interface == "responses":
        payload = {"model": "mock-model", "input": prompt, "max_output_tokens": 128}
    elif interface == "anthropic":
        payload = {
            "model": "mock-model",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 128,
        }
    headers = {"Authorization": f"Bearer {api_key}"}
    if provider:
        headers["X-Gateway-Provider"] = provider
    async with AsyncClient(
        transport=ASGITransport(app=request.app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            path,
            json=payload,
            headers=headers,
        )
    return templates.TemplateResponse(
        request,
        "partials/gateway_result.html",
        {
            "status": response.status_code,
            "body": json.dumps(response.json(), indent=2),
        },
    )
