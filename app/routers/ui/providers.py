import json
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response

from app.deps import SessionDep, get_current_user
from app.routers.ui.templates import templates
from app.schemas import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ProviderConfigCreate,
    ProviderConfigUpdate,
    ProviderModelCreate,
    ProviderModelUpdate,
    RoutingRuleCreate,
    RoutingRuleUpdate,
)
from app.services.provider_configs import (
    create_model_config,
    create_provider_config,
    create_provider_model,
    create_routing_rule,
    list_model_configs,
    list_provider_configs,
    list_provider_models,
    list_routing_rules,
    sync_provider_models,
    test_provider_config,
    test_provider_model,
    update_model_config,
    update_provider_config,
    update_provider_model,
    update_routing_rule,
)

router = APIRouter(prefix="/ui")


def _require_user(request: Request, session: SessionDep) -> None:
    get_current_user(session, access_token=request.cookies.get("access_token"))


def _split_csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _split_int_csv(value: str | None) -> list[int]:
    return [int(item) for item in _split_csv(value)]


def _parse_weight_config(value: str | None) -> dict[str, float]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        return {}
    return {str(key): float(item) for key, item in parsed.items()}


@router.get("/providers", response_class=HTMLResponse)
def providers(
    request: Request,
    session: SessionDep,
    search: str | None = None,
    provider_type: str | None = None,
    status: str | None = None,
) -> Response:
    _require_user(request, session)
    rows = list_provider_configs(session)
    if search:
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle in row.name.lower()
            or needle in row.display_name.lower()
            or needle in (row.base_url or "").lower()
        ]
    if provider_type:
        rows = [row for row in rows if row.provider_type == provider_type]
    if status == "enabled":
        rows = [row for row in rows if row.is_enabled]
    elif status == "disabled":
        rows = [row for row in rows if not row.is_enabled]
    return templates.TemplateResponse(
        request,
        "partials/providers.html",
        {
            "providers": rows,
            "search": search or "",
            "provider_type": provider_type or "",
            "status": status or "",
        },
    )


@router.post("/providers", response_class=HTMLResponse)
def create_provider(
    request: Request,
    session: SessionDep,
    name: Annotated[str, Form()],
    provider_type: Annotated[str, Form()],
    display_name: Annotated[str | None, Form()] = None,
    base_url: Annotated[str | None, Form()] = None,
    api_key_env_var: Annotated[str | None, Form()] = None,
    default_target_interface: Annotated[str, Form()] = "same",
    default_model_name: Annotated[str | None, Form()] = None,
    supports_streaming: Annotated[bool, Form()] = False,
    timeout_seconds: Annotated[float, Form()] = 60.0,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        create_provider_config(
            session,
            ProviderConfigCreate(
                name=name,
                provider_type=provider_type,
                display_name=display_name,
                base_url=base_url,
                api_key_env_var=api_key_env_var,
                default_target_interface=default_target_interface,
                default_model_name=default_model_name,
                supports_streaming=supports_streaming,
                timeout_seconds=timeout_seconds,
                is_enabled=is_enabled,
                is_default=is_default,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return templates.TemplateResponse(
        request,
        "partials/providers.html",
        {"providers": list_provider_configs(session), "error": error},
    )


@router.post("/providers/{provider_id}", response_class=HTMLResponse)
def update_provider(
    request: Request,
    provider_id: int,
    session: SessionDep,
    display_name: Annotated[str | None, Form()] = None,
    base_url: Annotated[str | None, Form()] = None,
    api_key_env_var: Annotated[str | None, Form()] = None,
    default_target_interface: Annotated[str, Form()] = "same",
    default_model_name: Annotated[str | None, Form()] = None,
    supports_streaming: Annotated[bool, Form()] = False,
    timeout_seconds: Annotated[float, Form()] = 60.0,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        update_provider_config(
            session,
            provider_id,
            ProviderConfigUpdate(
                display_name=display_name,
                base_url=base_url,
                api_key_env_var=api_key_env_var,
                default_target_interface=default_target_interface,
                default_model_name=default_model_name,
                supports_streaming=supports_streaming,
                timeout_seconds=timeout_seconds,
                is_enabled=is_enabled,
                is_default=is_default,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return templates.TemplateResponse(
        request,
        "partials/providers.html",
        {"providers": list_provider_configs(session), "error": error},
    )


@router.post("/providers/{provider_id}/test", response_class=HTMLResponse)
def test_provider(request: Request, provider_id: int, session: SessionDep) -> Response:
    _require_user(request, session)
    result = test_provider_config(session, provider_id)
    return templates.TemplateResponse(
        request,
        "partials/provider_test_result.html",
        {"result": result, "provider_id": provider_id},
    )


@router.get("/provider-models", response_class=HTMLResponse)
def provider_models(
    request: Request,
    session: SessionDep,
    search: str | None = None,
    provider_id: int | None = None,
    status: str | None = None,
    health_status: str | None = None,
) -> Response:
    _require_user(request, session)
    providers = list_provider_configs(session)
    rows = list_provider_models(session, provider_id)
    if search:
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle in row.upstream_model_name.lower()
            or needle in (row.display_name or "").lower()
            or needle in (row.notes or "").lower()
            or any(needle in item.lower() for item in row.capabilities)
        ]
    if status == "enabled":
        rows = [row for row in rows if row.is_enabled]
    elif status == "disabled":
        rows = [row for row in rows if not row.is_enabled]
    if health_status:
        rows = [row for row in rows if row.health_status == health_status]
    return templates.TemplateResponse(
        request,
        "partials/provider_models.html",
        {
            "provider_models": rows,
            "providers": providers,
            "provider_names": {provider.id: provider.name for provider in providers},
            "search": search or "",
            "provider_id": provider_id or "",
            "status": status or "",
            "health_status": health_status or "",
        },
    )


@router.post("/provider-models", response_class=HTMLResponse)
def create_provider_model_route(
    request: Request,
    session: SessionDep,
    provider_config_id: Annotated[int, Form()],
    upstream_model_name: Annotated[str, Form()],
    supported_interfaces: Annotated[list[str], Form()],
    display_name: Annotated[str | None, Form()] = None,
    capabilities: Annotated[str | None, Form()] = None,
    health_status: Annotated[str, Form()] = "unknown",
    default_target_interface: Annotated[str, Form()] = "same",
    input_price_per_million_tokens: Annotated[float | None, Form()] = None,
    output_price_per_million_tokens: Annotated[float | None, Form()] = None,
    supports_streaming: Annotated[bool, Form()] = False,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        create_provider_model(
            session,
            ProviderModelCreate(
                provider_config_id=provider_config_id,
                upstream_model_name=upstream_model_name,
                display_name=display_name,
                supported_interfaces=supported_interfaces,
                supports_streaming=supports_streaming,
                default_target_interface=default_target_interface,
                input_price_per_million_tokens=input_price_per_million_tokens,
                output_price_per_million_tokens=output_price_per_million_tokens,
                capabilities=_split_csv(capabilities),
                health_status=health_status,
                is_enabled=is_enabled,
                is_default=is_default,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _provider_models_partial(request, session, error)


@router.post("/provider-models/{provider_model_id}", response_class=HTMLResponse)
def update_provider_model_route(
    request: Request,
    provider_model_id: int,
    session: SessionDep,
    upstream_model_name: Annotated[str, Form()],
    supported_interfaces: Annotated[list[str], Form()],
    display_name: Annotated[str | None, Form()] = None,
    capabilities: Annotated[str | None, Form()] = None,
    health_status: Annotated[str, Form()] = "unknown",
    default_target_interface: Annotated[str, Form()] = "same",
    input_price_per_million_tokens: Annotated[float | None, Form()] = None,
    output_price_per_million_tokens: Annotated[float | None, Form()] = None,
    supports_streaming: Annotated[bool, Form()] = False,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        update_provider_model(
            session,
            provider_model_id,
            ProviderModelUpdate(
                upstream_model_name=upstream_model_name,
                display_name=display_name,
                supported_interfaces=supported_interfaces,
                supports_streaming=supports_streaming,
                default_target_interface=default_target_interface,
                input_price_per_million_tokens=input_price_per_million_tokens,
                output_price_per_million_tokens=output_price_per_million_tokens,
                capabilities=_split_csv(capabilities),
                health_status=health_status,
                is_enabled=is_enabled,
                is_default=is_default,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _provider_models_partial(request, session, error)


@router.post("/provider-models/{provider_model_id}/test", response_class=HTMLResponse)
def test_provider_model_route(
    request: Request,
    provider_model_id: int,
    session: SessionDep,
) -> Response:
    _require_user(request, session)
    result = test_provider_model(session, provider_model_id)
    return templates.TemplateResponse(
        request,
        "partials/provider_test_result.html",
        {"result": result, "provider_id": provider_model_id},
    )


@router.post("/providers/{provider_id}/provider-models/sync", response_class=HTMLResponse)
def sync_provider_models_route(
    request: Request,
    provider_id: int,
    session: SessionDep,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        sync_provider_models(session, provider_id)
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _provider_models_partial(request, session, error)


@router.get("/models", response_class=HTMLResponse)
def models(
    request: Request,
    session: SessionDep,
    search: str | None = None,
    provider_id: int | None = None,
    status: str | None = None,
) -> Response:
    _require_user(request, session)
    providers = list_provider_configs(session)
    rows = list_model_configs(session, provider_id)
    if search:
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle in row.public_model_name.lower()
            or needle in row.upstream_model_name.lower()
            or needle in (row.notes or "").lower()
        ]
    if status == "enabled":
        rows = [row for row in rows if row.is_enabled]
    elif status == "disabled":
        rows = [row for row in rows if not row.is_enabled]
    return templates.TemplateResponse(
        request,
        "partials/models.html",
        {
            "models": rows,
            "providers": providers,
            "provider_names": {provider.id: provider.name for provider in providers},
            "search": search or "",
            "provider_id": provider_id or "",
            "status": status or "",
        },
    )


@router.post("/models", response_class=HTMLResponse)
def create_model(
    request: Request,
    session: SessionDep,
    provider_config_id: Annotated[int, Form()],
    public_model_name: Annotated[str, Form()],
    upstream_model_name: Annotated[str, Form()],
    supported_interfaces: Annotated[list[str], Form()],
    default_parameters: Annotated[str, Form()] = "{}",
    default_target_interface: Annotated[str, Form()] = "same",
    supports_streaming: Annotated[bool, Form()] = False,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        create_model_config(
            session,
            ModelConfigCreate(
                provider_config_id=provider_config_id,
                public_model_name=public_model_name,
                upstream_model_name=upstream_model_name,
                supported_interfaces=supported_interfaces,
                supports_streaming=supports_streaming,
                default_target_interface=default_target_interface,
                default_parameters=json.loads(default_parameters or "{}"),
                is_enabled=is_enabled,
                is_default=is_default,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _models_partial(request, session, error)


@router.post("/models/{model_id}", response_class=HTMLResponse)
def update_model(
    request: Request,
    model_id: int,
    session: SessionDep,
    public_model_name: Annotated[str, Form()],
    upstream_model_name: Annotated[str, Form()],
    supported_interfaces: Annotated[list[str], Form()],
    default_parameters: Annotated[str, Form()] = "{}",
    default_target_interface: Annotated[str, Form()] = "same",
    supports_streaming: Annotated[bool, Form()] = False,
    is_enabled: Annotated[bool, Form()] = False,
    is_default: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        update_model_config(
            session,
            model_id,
            ModelConfigUpdate(
                public_model_name=public_model_name,
                upstream_model_name=upstream_model_name,
                supported_interfaces=supported_interfaces,
                supports_streaming=supports_streaming,
                default_target_interface=default_target_interface,
                default_parameters=json.loads(default_parameters or "{}"),
                is_enabled=is_enabled,
                is_default=is_default,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _models_partial(request, session, error)


@router.get("/routing-rules", response_class=HTMLResponse)
def routing_rules(
    request: Request,
    session: SessionDep,
    search: str | None = None,
    strategy: str | None = None,
    status: str | None = None,
) -> Response:
    _require_user(request, session)
    rules = list_routing_rules(session)
    if search:
        needle = search.lower()
        rules = [
            rule
            for rule in rules
            if needle in rule.name.lower()
            or needle in rule.public_model_name.lower()
            or needle in (rule.notes or "").lower()
        ]
    if strategy:
        rules = [rule for rule in rules if rule.strategy == strategy]
    if status == "enabled":
        rules = [rule for rule in rules if rule.is_enabled]
    elif status == "disabled":
        rules = [rule for rule in rules if not rule.is_enabled]
    return _routing_rules_template(
        request,
        session,
        rules=rules,
        search=search or "",
        strategy=strategy or "",
        status=status or "",
    )


@router.post("/routing-rules", response_class=HTMLResponse)
def create_routing_rule_route(
    request: Request,
    session: SessionDep,
    name: Annotated[str, Form()],
    public_model_name: Annotated[str, Form()],
    strategy: Annotated[str, Form()] = "fixed",
    provider_model_id: Annotated[int | None, Form()] = None,
    fallback_provider_model_ids: Annotated[str | None, Form()] = None,
    weight_config: Annotated[str | None, Form()] = None,
    custom_config: Annotated[str, Form()] = "{}",
    default_parameters: Annotated[str, Form()] = "{}",
    priority: Annotated[int, Form()] = 100,
    is_enabled: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        create_routing_rule(
            session,
            RoutingRuleCreate(
                name=name,
                public_model_name=public_model_name,
                strategy=strategy,
                provider_model_id=provider_model_id,
                fallback_provider_model_ids=_split_int_csv(fallback_provider_model_ids),
                weight_config=_parse_weight_config(weight_config),
                custom_config=json.loads(custom_config or "{}"),
                default_parameters=json.loads(default_parameters or "{}"),
                priority=priority,
                is_enabled=is_enabled,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _routing_rules_partial(request, session, error)


@router.post("/routing-rules/{rule_id}", response_class=HTMLResponse)
def update_routing_rule_route(
    request: Request,
    rule_id: int,
    session: SessionDep,
    name: Annotated[str, Form()],
    public_model_name: Annotated[str, Form()],
    strategy: Annotated[str, Form()] = "fixed",
    provider_model_id: Annotated[int | None, Form()] = None,
    fallback_provider_model_ids: Annotated[str | None, Form()] = None,
    weight_config: Annotated[str | None, Form()] = None,
    custom_config: Annotated[str, Form()] = "{}",
    default_parameters: Annotated[str, Form()] = "{}",
    priority: Annotated[int, Form()] = 100,
    is_enabled: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> Response:
    _require_user(request, session)
    error = None
    try:
        update_routing_rule(
            session,
            rule_id,
            RoutingRuleUpdate(
                name=name,
                public_model_name=public_model_name,
                strategy=strategy,
                provider_model_id=provider_model_id,
                fallback_provider_model_ids=_split_int_csv(fallback_provider_model_ids),
                weight_config=_parse_weight_config(weight_config),
                custom_config=json.loads(custom_config or "{}"),
                default_parameters=json.loads(default_parameters or "{}"),
                priority=priority,
                is_enabled=is_enabled,
                notes=notes,
            ),
        )
    except Exception as exc:
        error = str(getattr(exc, "detail", exc))
    return _routing_rules_partial(request, session, error)


def _provider_models_partial(
    request: Request,
    session: SessionDep,
    error: str | None = None,
) -> Response:
    providers = list_provider_configs(session)
    return templates.TemplateResponse(
        request,
        "partials/provider_models.html",
        {
            "provider_models": list_provider_models(session),
            "providers": providers,
            "provider_names": {provider.id: provider.name for provider in providers},
            "error": error,
            "search": "",
            "provider_id": "",
            "status": "",
            "health_status": "",
        },
    )


def _models_partial(request: Request, session: SessionDep, error: str | None = None) -> Response:
    providers = list_provider_configs(session)
    return templates.TemplateResponse(
        request,
        "partials/models.html",
        {
            "models": list_model_configs(session),
            "providers": providers,
            "provider_names": {provider.id: provider.name for provider in providers},
            "error": error,
            "search": "",
            "provider_id": "",
            "status": "",
        },
    )


def _routing_rules_partial(
    request: Request,
    session: SessionDep,
    error: str | None = None,
) -> Response:
    return _routing_rules_template(
        request,
        session,
        rules=list_routing_rules(session),
        search="",
        strategy="",
        status="",
        error=error,
    )


def _routing_rules_template(
    request: Request,
    session: SessionDep,
    *,
    rules,
    search: str,
    strategy: str,
    status: str,
    error: str | None = None,
) -> Response:
    providers = list_provider_configs(session)
    provider_models = list_provider_models(session)
    provider_names = {provider.id: provider.name for provider in providers}
    provider_model_labels = {
        model.id: f"{provider_names.get(model.provider_config_id, model.provider_config_id)} / "
        f"{model.upstream_model_name}"
        for model in provider_models
    }
    return templates.TemplateResponse(
        request,
        "partials/routing_rules.html",
        {
            "rules": rules,
            "provider_models": provider_models,
            "provider_model_labels": provider_model_labels,
            "error": error,
            "search": search,
            "strategy": strategy,
            "status": status,
        },
    )
