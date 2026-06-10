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
)
from app.services.provider_configs import (
    create_model_config,
    create_provider_config,
    list_model_configs,
    list_provider_configs,
    test_provider_config,
    update_model_config,
    update_provider_config,
)

router = APIRouter(prefix="/ui")


def _require_user(request: Request, session: SessionDep) -> None:
    get_current_user(session, access_token=request.cookies.get("access_token"))


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
