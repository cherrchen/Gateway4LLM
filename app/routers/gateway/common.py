import json
import time
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

import app.providers  # noqa: F401
from app.conversions import convert_request
from app.deps import ApiKeyPrincipalDep, SessionDep
from app.models import GatewayLog
from app.providers.registry import provider_registry
from app.redaction import request_meta, response_meta
from app.services.provider_configs import (
    prepare_upstream_body,
    resolve_model_config,
    resolve_provider_config,
    resolve_routing_rule_config,
    resolve_target_interface,
    validate_gateway_resolution,
)


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
    _, api_key = principal
    provider_name = x_gateway_provider or ""
    target = x_gateway_target_interface or ""

    try:
        routed_config = resolve_routing_rule_config(session, body, api_key, x_gateway_provider)
        if routed_config:
            provider_config, model_config = routed_config
        else:
            provider_config = resolve_provider_config(session, body, api_key, x_gateway_provider)
            model_config = resolve_model_config(session, body, api_key, provider_config)
        provider_name = provider_config.name
        target = resolve_target_interface(
            body,
            source_interface,
            x_gateway_target_interface,
            provider_config,
            model_config,
        )
        upstream_body = prepare_upstream_body(body, model_config)
        converted = convert_request(upstream_body, source_interface, target)
        stream = bool(converted.get("stream"))
        validate_gateway_resolution(provider_config, model_config, source_interface, target, stream)
        provider = provider_registry.get(provider_config.provider_type)

        if stream:
            log_gateway_request(
                session,
                principal,
                request,
                provider_name,
                source_interface,
                target,
                200,
                started,
                body,
                {},
            )
            return StreamingResponse(
                provider.stream(target, converted, provider_config, model_config),
                media_type="text/event-stream",
            )

        result = await provider.send(target, converted, provider_config, model_config)
        log_gateway_request(
            session,
            principal,
            request,
            provider_name,
            source_interface,
            target,
            result.status_code,
            started,
            body,
            result.body,
            error=json.dumps(result.body) if result.status_code >= 400 else None,
        )
        return JSONResponse(result.body, status_code=result.status_code)
    except Exception as exc:
        error = str(exc)
        log_gateway_request(
            session,
            principal,
            request,
            provider_name or "unknown",
            source_interface,
            target or source_interface,
            getattr(exc, "status_code", 500),
            started,
            body,
            {},
            error,
        )
        raise
