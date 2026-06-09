import json
import time
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.conversions import convert_request
from app.core.config import get_settings
from app.deps import ApiKeyPrincipalDep, SessionDep
from app.models import GatewayLog
from app.redaction import request_meta, response_meta
from app.upstream import mock_response, mock_stream, post_upstream, stream_upstream


def target_provider(body: dict[str, Any], header_provider: str | None) -> str:
    raw_gateway = body.get("gateway")
    gateway: dict[str, Any] = raw_gateway if isinstance(raw_gateway, dict) else {}
    return (header_provider or gateway.get("provider") or get_settings().default_provider).lower()


def target_interface(source: str, header_target: str | None) -> str:
    configured = header_target or get_settings().default_target_interface
    if configured == "same":
        return source
    return configured.lower()


def log_gateway_request(
    session: SessionDep,
    principal: ApiKeyPrincipalDep,
    request: Request,
    provider: str,
    source: str,
    target: str,
    status_code: int,
    started: float,
    body: dict[str, Any],
    response_body: Any,
    error: str | None = None,
) -> None:
    user, api_key = principal
    log = GatewayLog(
        user_id=user.id,
        api_key_id=api_key.id,
        api_key_prefix=api_key.key_prefix,
        route=request.url.path,
        provider=provider,
        source_interface=source,
        target_interface=target,
        status_code=status_code,
        duration_ms=int((time.perf_counter() - started) * 1000),
        request_meta=json.dumps(request_meta(body, request.headers), ensure_ascii=False),
        response_meta=json.dumps(response_meta(response_body), ensure_ascii=False),
        error=error,
    )
    session.add(log)
    session.commit()


async def handle_gateway_request(
    request: Request,
    session: SessionDep,
    principal: ApiKeyPrincipalDep,
    source_interface: str,
    x_gateway_provider: str | None,
    x_gateway_target_interface: str | None,
) -> Response:
    started = time.perf_counter()
    body = await request.json()
    provider = target_provider(body, x_gateway_provider)
    target = target_interface(source_interface, x_gateway_target_interface)
    converted = convert_request(body, source_interface, target)
    stream = bool(converted.get("stream"))

    try:
        if provider == "mock":
            if stream:
                log_gateway_request(
                    session,
                    principal,
                    request,
                    provider,
                    source_interface,
                    target,
                    200,
                    started,
                    body,
                    {},
                )
                return StreamingResponse(mock_stream(target), media_type="text/event-stream")
            payload = mock_response(target, converted)
            log_gateway_request(
                session,
                principal,
                request,
                provider,
                source_interface,
                target,
                200,
                started,
                body,
                payload,
            )
            return JSONResponse(payload)

        if stream:
            log_gateway_request(
                session,
                principal,
                request,
                provider,
                source_interface,
                target,
                200,
                started,
                body,
                {},
            )
            return StreamingResponse(
                stream_upstream(provider, target, converted),
                media_type="text/event-stream",
            )

        status_code, payload = await post_upstream(provider, target, converted)
        log_gateway_request(
            session,
            principal,
            request,
            provider,
            source_interface,
            target,
            status_code,
            started,
            body,
            payload,
            error=json.dumps(payload) if status_code >= 400 else None,
        )
        return JSONResponse(payload, status_code=status_code)
    except Exception as exc:
        error = str(exc)
        log_gateway_request(
            session,
            principal,
            request,
            provider,
            source_interface,
            target,
            500,
            started,
            body,
            {},
            error,
        )
        raise
