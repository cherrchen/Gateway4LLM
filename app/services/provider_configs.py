import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.orm.session import Session

import app.providers  # noqa: F401
from app.core.config import get_settings
from app.models import (
    BusinessApiKey,
    ModelConfig,
    ProviderConfig,
    ProviderModel,
    RoutingRule,
    now_utc,
)
from app.providers.registry import provider_registry
from app.schemas import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigUpdate,
    ProviderConfigCreate,
    ProviderConfigRead,
    ProviderConfigUpdate,
    ProviderModelCreate,
    ProviderModelRead,
    ProviderModelUpdate,
    ProviderTestResult,
    ProviderTypeRead,
    RoutingRuleCreate,
    RoutingRuleRead,
    RoutingRuleUpdate,
    RoutingSettingsRead,
    RoutingSettingsUpdate,
)

INTERFACES = {"chat", "responses", "anthropic"}
ROUTING_STRATEGIES = {"fixed", "fallback", "weighted", "custom"}
HEALTH_STATUSES = {"unknown", "healthy", "degraded", "unavailable", "deprecated"}


@dataclass(frozen=True)
class GatewayResolution:
    provider_config: ProviderConfig
    model_config: ModelConfig
    provider_type: str
    source_interface: str
    target_interface: str
    upstream_body: dict[str, Any]


def _json_loads_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _json_loads_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _json_loads_int_list(value: str | None) -> list[int]:
    if not value:
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        return []
    return [int(item) for item in parsed]


def _json_loads_float_dict(value: str | None) -> dict[str, float]:
    parsed = _json_loads_dict(value)
    return {str(key): float(item) for key, item in parsed.items()}


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _gateway_options(body: dict[str, Any]) -> dict[str, Any]:
    value = body.get("gateway")
    return value if isinstance(value, dict) else {}


def provider_to_read(config: ProviderConfig) -> ProviderConfigRead:
    return ProviderConfigRead(
        **config.model_dump(exclude={"api_key_secret_ref"}),
        api_key_configured=bool(config.api_key_env_var or config.api_key_secret_ref),
    )


def list_provider_types() -> list[ProviderTypeRead]:
    rows: list[ProviderTypeRead] = []
    for provider in sorted(provider_registry.list(), key=lambda item: item.name):
        requires_key = provider.name != "mock"
        rows.append(
            ProviderTypeRead(
                name=provider.name,
                display_name=provider.display_name,
                supported_interfaces=sorted(provider.supported_interfaces),
                supports_streaming=provider.supports_streaming,
                config_requirements={
                    "api_key": "required" if requires_key else "not_required",
                    "api_key_sources": ["api_key_env_var", "api_key_secret_ref"],
                    "base_url": "optional",
                },
            )
        )
    return rows


def model_to_read(model: ModelConfig) -> ModelConfigRead:
    return ModelConfigRead(
        **model.model_dump(exclude={"supported_interfaces", "default_parameters"}),
        supported_interfaces=_json_loads_list(model.supported_interfaces),
        default_parameters=_json_loads_dict(model.default_parameters),
    )


def provider_model_to_read(session: Session, model: ProviderModel) -> ProviderModelRead:
    mapped = session.exec(
        select(ModelConfig).where(
            ModelConfig.provider_config_id == model.provider_config_id,
            ModelConfig.upstream_model_name == model.upstream_model_name,
        )
    ).all()
    return ProviderModelRead(
        **model.model_dump(exclude={"supported_interfaces", "capabilities"}),
        supported_interfaces=_json_loads_list(model.supported_interfaces),
        capabilities=_json_loads_list(model.capabilities),
        mapped_gateway_models=[row.public_model_name for row in mapped],
    )


def routing_rule_to_read(rule: RoutingRule) -> RoutingRuleRead:
    return RoutingRuleRead(
        **rule.model_dump(
            exclude={
                "fallback_provider_model_ids",
                "weight_config",
                "custom_config",
                "default_parameters",
            }
        ),
        fallback_provider_model_ids=_json_loads_int_list(rule.fallback_provider_model_ids),
        weight_config=_json_loads_float_dict(rule.weight_config),
        custom_config=_json_loads_dict(rule.custom_config),
        default_parameters=_json_loads_dict(rule.default_parameters),
    )


def ensure_default_configs(session: Session) -> None:
    settings = get_settings()
    mock = session.exec(select(ProviderConfig).where(ProviderConfig.name == "mock")).first()
    if not mock:
        mock = ProviderConfig(
            name="mock",
            display_name="Mock",
            provider_type="mock",
            default_target_interface="same",
            default_model_name="mock-model",
            supports_streaming=True,
            is_enabled=True,
            is_default=settings.default_provider == "mock",
        )
        session.add(mock)
        session.commit()
        session.refresh(mock)
    _ensure_provider_model(
        session,
        mock,
        "mock-model",
        display_name="Mock model",
        is_default=True,
        capabilities=["chat", "responses", "anthropic", "streaming"],
    )
    _ensure_model(session, mock, "mock-model", "mock-model", is_default=True)
    _ensure_model(session, mock, "mock", "mock-model", is_default=False)

    for name, display_name, base_url, env_var in (
        ("openai", "OpenAI", settings.openai_base_url, "G4L_OPENAI_API_KEY"),
        ("anthropic", "Anthropic", settings.anthropic_base_url, "G4L_ANTHROPIC_API_KEY"),
    ):
        if not session.exec(select(ProviderConfig).where(ProviderConfig.name == name)).first():
            session.add(
                ProviderConfig(
                    name=name,
                    display_name=display_name,
                    provider_type=name,
                    base_url=base_url,
                    api_key_env_var=env_var,
                    default_target_interface="same" if name == "openai" else "anthropic",
                    supports_streaming=True,
                    is_enabled=False,
                    is_default=settings.default_provider == name,
                )
            )
    session.commit()


def _ensure_provider_model(
    session: Session,
    provider: ProviderConfig,
    upstream_name: str,
    *,
    display_name: str | None = None,
    is_default: bool,
    capabilities: list[str] | None = None,
) -> None:
    existing = session.exec(
        select(ProviderModel).where(
            ProviderModel.provider_config_id == provider.id,
            ProviderModel.upstream_model_name == upstream_name,
        )
    ).first()
    if existing:
        return
    session.add(
        ProviderModel(
            provider_config_id=provider.id or 0,
            upstream_model_name=upstream_name,
            display_name=display_name or upstream_name,
            supported_interfaces=_json_dumps(["chat", "responses", "anthropic"]),
            supports_streaming=True,
            default_target_interface=provider.default_target_interface,
            capabilities=_json_dumps(capabilities or []),
            health_status="healthy" if provider.provider_type == "mock" else "unknown",
            is_enabled=True,
            is_default=is_default,
        )
    )
    session.commit()


def _ensure_model(
    session: Session,
    provider: ProviderConfig,
    public_name: str,
    upstream_name: str,
    *,
    is_default: bool,
) -> None:
    existing = session.exec(
        select(ModelConfig).where(
            ModelConfig.provider_config_id == provider.id,
            ModelConfig.public_model_name == public_name,
        )
    ).first()
    if existing:
        return
    session.add(
        ModelConfig(
            provider_config_id=provider.id or 0,
            public_model_name=public_name,
            upstream_model_name=upstream_name,
            supported_interfaces=_json_dumps(["chat", "responses", "anthropic"]),
            supports_streaming=True,
            default_target_interface="same",
            is_enabled=True,
            is_default=is_default,
        )
    )
    session.commit()


def list_provider_configs(session: Session) -> list[ProviderConfigRead]:
    rows = session.exec(select(ProviderConfig).order_by(ProviderConfig.name)).all()
    return [provider_to_read(row) for row in rows]


def get_provider_config(session: Session, provider_id: int) -> ProviderConfig:
    config = session.get(ProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider config not found")
    return config


def get_provider_config_read(session: Session, provider_id: int) -> ProviderConfigRead:
    return provider_to_read(get_provider_config(session, provider_id))


def get_provider_config_by_name(session: Session, name: str) -> ProviderConfig | None:
    return session.exec(select(ProviderConfig).where(ProviderConfig.name == name.lower())).first()


def create_provider_config(session: Session, payload: ProviderConfigCreate) -> ProviderConfigRead:
    name = payload.name.lower()
    if get_provider_config_by_name(session, name):
        raise HTTPException(status_code=409, detail=f"Provider config already exists: {name}")
    provider_registry.get(payload.provider_type)
    _validate_target_interface(payload.default_target_interface)
    config = ProviderConfig(
        name=name,
        display_name=payload.display_name or name,
        provider_type=payload.provider_type.lower(),
        base_url=payload.base_url or None,
        api_key_env_var=payload.api_key_env_var or None,
        api_key_secret_ref=payload.api_key_secret_ref or None,
        default_target_interface=payload.default_target_interface.lower(),
        default_model_name=payload.default_model_name or None,
        supports_streaming=payload.supports_streaming,
        timeout_seconds=payload.timeout_seconds,
        is_enabled=payload.is_enabled,
        is_default=payload.is_default,
    )
    session.add(config)
    _clear_default_provider(session, config) if config.is_default else None
    session.commit()
    session.refresh(config)
    return provider_to_read(config)


def update_provider_config(
    session: Session, provider_id: int, payload: ProviderConfigUpdate
) -> ProviderConfigRead:
    config = get_provider_config(session, provider_id)
    values = payload.model_dump(exclude_unset=True)
    if "default_target_interface" in values and values["default_target_interface"]:
        _validate_target_interface(values["default_target_interface"])
    for key, value in values.items():
        if isinstance(value, str):
            value = value.strip() or None
        if key == "default_target_interface" and value:
            value = value.lower()
        setattr(config, key, value)
    config.updated_at = now_utc()
    session.add(config)
    _clear_default_provider(session, config) if config.is_default else None
    session.commit()
    session.refresh(config)
    return provider_to_read(config)


def set_provider_enabled(session: Session, provider_id: int, enabled: bool) -> ProviderConfigRead:
    config = get_provider_config(session, provider_id)
    config.is_enabled = enabled
    config.updated_at = now_utc()
    session.add(config)
    session.commit()
    session.refresh(config)
    return provider_to_read(config)


def set_default_provider(session: Session, provider_id: int) -> ProviderConfigRead:
    config = get_provider_config(session, provider_id)
    if not config.is_enabled:
        raise HTTPException(status_code=400, detail="Disabled provider cannot be set as default")
    config.is_default = True
    config.updated_at = now_utc()
    session.add(config)
    _clear_default_provider(session, config)
    session.commit()
    session.refresh(config)
    return provider_to_read(config)


def reject_provider_delete(provider_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Provider config {provider_id} cannot be hard-deleted. "
            "Disable it instead to preserve model, policy, and log history."
        ),
    )


def _clear_default_provider(session: Session, selected: ProviderConfig) -> None:
    rows = session.exec(select(ProviderConfig).where(ProviderConfig.id != selected.id)).all()
    for row in rows:
        if row.is_default:
            row.is_default = False
            row.updated_at = now_utc()
            session.add(row)


def list_model_configs(session: Session, provider_id: int | None = None) -> list[ModelConfigRead]:
    query = select(ModelConfig).order_by(ModelConfig.public_model_name)
    if provider_id is not None:
        query = query.where(ModelConfig.provider_config_id == provider_id)
    rows = session.exec(query).all()
    return [model_to_read(row) for row in rows]


def get_model_config(session: Session, model_id: int) -> ModelConfig:
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model config not found")
    return model


def get_model_config_read(session: Session, model_id: int) -> ModelConfigRead:
    return model_to_read(get_model_config(session, model_id))


def create_model_config(session: Session, payload: ModelConfigCreate) -> ModelConfigRead:
    provider = get_provider_config(session, payload.provider_config_id)
    _validate_interfaces(payload.supported_interfaces)
    _validate_target_interface(payload.default_target_interface)
    if not payload.upstream_model_name.strip():
        raise HTTPException(status_code=400, detail="upstream_model_name is required")
    existing = session.exec(
        select(ModelConfig).where(
            ModelConfig.provider_config_id == provider.id,
            ModelConfig.public_model_name == payload.public_model_name,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Model config already exists for provider")
    model = ModelConfig(
        provider_config_id=provider.id or 0,
        public_model_name=payload.public_model_name,
        upstream_model_name=payload.upstream_model_name,
        supported_interfaces=_json_dumps(payload.supported_interfaces),
        supports_streaming=payload.supports_streaming,
        default_target_interface=payload.default_target_interface.lower(),
        default_parameters=_json_dumps(payload.default_parameters),
        is_enabled=payload.is_enabled,
        is_default=payload.is_default,
        notes=payload.notes,
    )
    session.add(model)
    _clear_default_model(session, model) if model.is_default else None
    session.commit()
    session.refresh(model)
    return model_to_read(model)


def update_model_config(
    session: Session,
    model_id: int,
    payload: ModelConfigUpdate,
) -> ModelConfigRead:
    model = get_model_config(session, model_id)
    values = payload.model_dump(exclude_unset=True)
    if "supported_interfaces" in values and values["supported_interfaces"] is not None:
        _validate_interfaces(values["supported_interfaces"])
        values["supported_interfaces"] = _json_dumps(values["supported_interfaces"])
    if "public_model_name" in values and values["public_model_name"] is not None:
        duplicate = session.exec(
            select(ModelConfig).where(
                ModelConfig.provider_config_id == model.provider_config_id,
                ModelConfig.public_model_name == values["public_model_name"],
                ModelConfig.id != model.id,
            )
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Model config already exists for provider")
    if "upstream_model_name" in values and values["upstream_model_name"] is not None:
        if not values["upstream_model_name"].strip():
            raise HTTPException(status_code=400, detail="upstream_model_name is required")
    if "default_parameters" in values and values["default_parameters"] is not None:
        values["default_parameters"] = _json_dumps(values["default_parameters"])
    if "default_target_interface" in values and values["default_target_interface"]:
        _validate_target_interface(values["default_target_interface"])
        values["default_target_interface"] = values["default_target_interface"].lower()
    for key, value in values.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(model, key, value)
    model.updated_at = now_utc()
    session.add(model)
    _clear_default_model(session, model) if model.is_default else None
    session.commit()
    session.refresh(model)
    return model_to_read(model)


def set_model_enabled(session: Session, model_id: int, enabled: bool) -> ModelConfigRead:
    model = get_model_config(session, model_id)
    model.is_enabled = enabled
    model.updated_at = now_utc()
    session.add(model)
    session.commit()
    session.refresh(model)
    return model_to_read(model)


def set_default_model(session: Session, model_id: int) -> ModelConfigRead:
    model = get_model_config(session, model_id)
    if not model.is_enabled:
        raise HTTPException(status_code=400, detail="Disabled model cannot be set as default")
    model.is_default = True
    model.updated_at = now_utc()
    session.add(model)
    _clear_default_model(session, model)
    session.commit()
    session.refresh(model)
    return model_to_read(model)


def reject_model_delete(model_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Model config {model_id} cannot be hard-deleted. "
            "Disable it instead to preserve routing, policy, and log history."
        ),
    )


def _clear_default_model(session: Session, selected: ModelConfig) -> None:
    rows = session.exec(
        select(ModelConfig).where(
            ModelConfig.provider_config_id == selected.provider_config_id,
            ModelConfig.id != selected.id,
        )
    ).all()
    for row in rows:
        if row.is_default:
            row.is_default = False
            row.updated_at = now_utc()
            session.add(row)


def list_provider_models(
    session: Session,
    provider_id: int | None = None,
) -> list[ProviderModelRead]:
    query = select(ProviderModel).order_by(ProviderModel.upstream_model_name)
    if provider_id is not None:
        query = query.where(ProviderModel.provider_config_id == provider_id)
    rows = session.exec(query).all()
    return [provider_model_to_read(session, row) for row in rows]


def get_provider_model(session: Session, provider_model_id: int) -> ProviderModel:
    model = session.get(ProviderModel, provider_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Provider model not found")
    return model


def get_provider_model_read(session: Session, provider_model_id: int) -> ProviderModelRead:
    return provider_model_to_read(session, get_provider_model(session, provider_model_id))


def create_provider_model(session: Session, payload: ProviderModelCreate) -> ProviderModelRead:
    provider = get_provider_config(session, payload.provider_config_id)
    _validate_interfaces(payload.supported_interfaces)
    _validate_target_interface(payload.default_target_interface)
    _validate_health_status(payload.health_status)
    upstream_name = payload.upstream_model_name.strip()
    duplicate = session.exec(
        select(ProviderModel).where(
            ProviderModel.provider_config_id == provider.id,
            ProviderModel.upstream_model_name == upstream_name,
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Provider model already exists for provider")
    model = ProviderModel(
        provider_config_id=provider.id or 0,
        upstream_model_name=upstream_name,
        display_name=(payload.display_name or "").strip() or upstream_name,
        supported_interfaces=_json_dumps(payload.supported_interfaces),
        supports_streaming=payload.supports_streaming,
        default_target_interface=payload.default_target_interface.lower(),
        input_price_per_million_tokens=payload.input_price_per_million_tokens,
        output_price_per_million_tokens=payload.output_price_per_million_tokens,
        capabilities=_json_dumps(payload.capabilities),
        health_status=payload.health_status,
        is_enabled=payload.is_enabled,
        is_default=payload.is_default,
        notes=payload.notes,
    )
    session.add(model)
    _clear_default_provider_model(session, model) if model.is_default else None
    session.commit()
    session.refresh(model)
    return provider_model_to_read(session, model)


def update_provider_model(
    session: Session,
    provider_model_id: int,
    payload: ProviderModelUpdate,
) -> ProviderModelRead:
    model = get_provider_model(session, provider_model_id)
    values = payload.model_dump(exclude_unset=True)
    if "supported_interfaces" in values and values["supported_interfaces"] is not None:
        _validate_interfaces(values["supported_interfaces"])
        values["supported_interfaces"] = _json_dumps(values["supported_interfaces"])
    if "default_target_interface" in values and values["default_target_interface"]:
        _validate_target_interface(values["default_target_interface"])
        values["default_target_interface"] = values["default_target_interface"].lower()
    if "health_status" in values and values["health_status"]:
        _validate_health_status(values["health_status"])
    if "capabilities" in values and values["capabilities"] is not None:
        values["capabilities"] = _json_dumps(values["capabilities"])
    if "upstream_model_name" in values and values["upstream_model_name"] is not None:
        upstream_name = values["upstream_model_name"].strip()
        duplicate = session.exec(
            select(ProviderModel).where(
                ProviderModel.provider_config_id == model.provider_config_id,
                ProviderModel.upstream_model_name == upstream_name,
                ProviderModel.id != model.id,
            )
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Provider model already exists for provider",
            )
        values["upstream_model_name"] = upstream_name
    for key, value in values.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(model, key, value)
    model.updated_at = now_utc()
    session.add(model)
    _clear_default_provider_model(session, model) if model.is_default else None
    session.commit()
    session.refresh(model)
    return provider_model_to_read(session, model)


def set_provider_model_enabled(
    session: Session,
    provider_model_id: int,
    enabled: bool,
) -> ProviderModelRead:
    model = get_provider_model(session, provider_model_id)
    model.is_enabled = enabled
    model.updated_at = now_utc()
    session.add(model)
    session.commit()
    session.refresh(model)
    return provider_model_to_read(session, model)


def set_default_provider_model(session: Session, provider_model_id: int) -> ProviderModelRead:
    model = get_provider_model(session, provider_model_id)
    if not model.is_enabled:
        raise HTTPException(status_code=400, detail="Disabled provider model cannot be default")
    model.is_default = True
    model.updated_at = now_utc()
    session.add(model)
    _clear_default_provider_model(session, model)
    session.commit()
    session.refresh(model)
    return provider_model_to_read(session, model)


def sync_provider_models(session: Session, provider_id: int) -> list[ProviderModelRead]:
    provider = get_provider_config(session, provider_id)
    upstream_names = {
        model.upstream_model_name
        for model in session.exec(
            select(ModelConfig).where(ModelConfig.provider_config_id == provider.id)
        ).all()
    }
    if provider.default_model_name:
        upstream_names.add(provider.default_model_name)
    for upstream_name in sorted(upstream_names):
        _ensure_provider_model(
            session,
            provider,
            upstream_name,
            display_name=upstream_name,
            is_default=False,
        )
    return list_provider_models(session, provider.id)


def test_provider_model(session: Session, provider_model_id: int) -> ProviderTestResult:
    model = get_provider_model(session, provider_model_id)
    provider = get_provider_config(session, model.provider_config_id)
    try:
        if not provider.is_enabled:
            raise HTTPException(status_code=400, detail=f"Provider is disabled: {provider.name}")
        if not model.is_enabled:
            raise HTTPException(
                status_code=400,
                detail=f"Provider model is disabled: {model.upstream_model_name}",
            )
        provider_registry.get(provider.provider_type).validate_config(provider)
    except HTTPException as exc:
        model.health_status = "unavailable"
        model.updated_at = now_utc()
        session.add(model)
        session.commit()
        return ProviderTestResult(ok=False, message=str(exc.detail))
    model.health_status = "healthy"
    model.updated_at = now_utc()
    session.add(model)
    session.commit()
    return ProviderTestResult(
        ok=True,
        message=f"ProviderModel '{model.upstream_model_name}' is ready",
    )


def reject_provider_model_delete(provider_model_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Provider model {provider_model_id} cannot be hard-deleted. "
            "Disable it instead to preserve gateway mappings and routing rules."
        ),
    )


def _clear_default_provider_model(session: Session, selected: ProviderModel) -> None:
    rows = session.exec(
        select(ProviderModel).where(
            ProviderModel.provider_config_id == selected.provider_config_id,
            ProviderModel.id != selected.id,
        )
    ).all()
    for row in rows:
        if row.is_default:
            row.is_default = False
            row.updated_at = now_utc()
            session.add(row)


def list_routing_rules(
    session: Session,
    public_model_name: str | None = None,
) -> list[RoutingRuleRead]:
    query = select(RoutingRule).order_by(RoutingRule.priority, RoutingRule.id)
    if public_model_name:
        query = query.where(RoutingRule.public_model_name == public_model_name)
    rows = session.exec(query).all()
    return [routing_rule_to_read(row) for row in rows]


def get_routing_rule(session: Session, rule_id: int) -> RoutingRule:
    rule = session.get(RoutingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Routing rule not found")
    return rule


def get_routing_rule_read(session: Session, rule_id: int) -> RoutingRuleRead:
    return routing_rule_to_read(get_routing_rule(session, rule_id))


def create_routing_rule(session: Session, payload: RoutingRuleCreate) -> RoutingRuleRead:
    _validate_routing_strategy(payload.strategy)
    _validate_routing_rule_provider_models(
        session,
        payload.strategy,
        payload.provider_model_id,
        payload.fallback_provider_model_ids,
        payload.weight_config,
    )
    rule = RoutingRule(
        name=payload.name.strip(),
        public_model_name=payload.public_model_name.strip(),
        strategy=payload.strategy.lower(),
        provider_model_id=payload.provider_model_id,
        fallback_provider_model_ids=_json_dumps(payload.fallback_provider_model_ids),
        weight_config=_json_dumps(payload.weight_config),
        custom_config=_json_dumps(payload.custom_config),
        default_parameters=_json_dumps(payload.default_parameters),
        priority=payload.priority,
        is_enabled=payload.is_enabled,
        notes=payload.notes,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return routing_rule_to_read(rule)


def update_routing_rule(
    session: Session,
    rule_id: int,
    payload: RoutingRuleUpdate,
) -> RoutingRuleRead:
    rule = get_routing_rule(session, rule_id)
    values = payload.model_dump(exclude_unset=True)
    strategy = str(values.get("strategy") or rule.strategy).lower()
    has_fallback_ids = (
        "fallback_provider_model_ids" in values
        and values["fallback_provider_model_ids"] is not None
    )
    fallback_ids = (
        values["fallback_provider_model_ids"]
        if has_fallback_ids
        else _json_loads_int_list(rule.fallback_provider_model_ids)
    )
    weights = (
        values["weight_config"]
        if "weight_config" in values and values["weight_config"] is not None
        else _json_loads_float_dict(rule.weight_config)
    )
    provider_model_id = (
        values["provider_model_id"]
        if "provider_model_id" in values
        else rule.provider_model_id
    )
    _validate_routing_strategy(strategy)
    _validate_routing_rule_provider_models(
        session,
        strategy,
        provider_model_id,
        fallback_ids,
        weights,
    )
    for key, value in values.items():
        if key == "strategy" and value is not None:
            value = value.lower()
        elif key in {
            "fallback_provider_model_ids",
            "weight_config",
            "custom_config",
            "default_parameters",
        }:
            value = _json_dumps(value)
        elif isinstance(value, str):
            value = value.strip() or None
        setattr(rule, key, value)
    rule.updated_at = now_utc()
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return routing_rule_to_read(rule)


def set_routing_rule_enabled(session: Session, rule_id: int, enabled: bool) -> RoutingRuleRead:
    rule = get_routing_rule(session, rule_id)
    rule.is_enabled = enabled
    rule.updated_at = now_utc()
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return routing_rule_to_read(rule)


def reject_routing_rule_delete(rule_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Routing rule {rule_id} cannot be hard-deleted. "
            "Disable it instead to preserve routing history."
        ),
    )


def _validate_interfaces(values: list[str]) -> None:
    if not values:
        raise HTTPException(status_code=400, detail="supported_interfaces cannot be empty")
    invalid = [value for value in values if value not in INTERFACES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported interfaces: {', '.join(invalid)}")


def _validate_target_interface(value: str) -> None:
    target = value.lower()
    if target != "same" and target not in INTERFACES:
        raise HTTPException(status_code=400, detail=f"Unsupported target interface: {value}")


def _validate_health_status(value: str) -> None:
    if value not in HEALTH_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported health status: {value}")


def _validate_routing_strategy(value: str) -> None:
    if value.lower() not in ROUTING_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Unsupported routing strategy: {value}")


def _validate_routing_rule_provider_models(
    session: Session,
    strategy: str,
    provider_model_id: int | None,
    fallback_provider_model_ids: list[int],
    weight_config: dict[str, float],
) -> None:
    candidate_ids = set(fallback_provider_model_ids)
    if provider_model_id is not None:
        candidate_ids.add(provider_model_id)
    try:
        for key in weight_config:
            candidate_ids.add(int(key))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Routing weight keys must be provider model ids",
        ) from exc
    if strategy in {"fixed", "fallback", "weighted"} and not candidate_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Routing strategy '{strategy}' requires at least one provider model",
        )
    for candidate_id in candidate_ids:
        get_provider_model(session, candidate_id)
    if strategy == "weighted" and any(weight <= 0 for weight in weight_config.values()):
        raise HTTPException(status_code=400, detail="Routing weights must be positive")


def get_routing_settings(session: Session) -> RoutingSettingsRead:
    settings = get_settings()
    configured_default = session.exec(
        select(ProviderConfig).where(ProviderConfig.is_default)
    ).first()
    default_model = None
    if configured_default:
        model = session.exec(
            select(ModelConfig).where(
                ModelConfig.provider_config_id == configured_default.id,
                ModelConfig.is_default,
            )
        ).first()
        default_model = model.public_model_name if model else configured_default.default_model_name
    return RoutingSettingsRead(
        default_provider=configured_default.name if configured_default else None,
        default_model=default_model,
        default_target_interface=(
            configured_default.default_target_interface
            if configured_default
            else settings.default_target_interface
        ),
        environment_default_provider=settings.default_provider,
        environment_default_model=settings.default_model,
        environment_default_target_interface=settings.default_target_interface,
    )


def update_routing_settings(
    session: Session,
    payload: RoutingSettingsUpdate,
) -> RoutingSettingsRead:
    values = payload.model_dump(exclude_unset=True)
    provider: ProviderConfig | None = None
    if "default_provider" in values and values["default_provider"]:
        provider = get_provider_config_by_name(session, str(values["default_provider"]))
        if not provider:
            raise HTTPException(status_code=400, detail="Default provider is not configured")
        if not provider.is_enabled:
            raise HTTPException(status_code=400, detail="Disabled provider cannot be default")
        provider.is_default = True
        _clear_default_provider(session, provider)
    else:
        provider = session.exec(select(ProviderConfig).where(ProviderConfig.is_default)).first()
    if provider and "default_model" in values:
        model_name = values["default_model"]
        provider.default_model_name = (model_name or "").strip() or None
        provider.updated_at = now_utc()
    if provider and values.get("default_target_interface"):
        _validate_target_interface(values["default_target_interface"])
        provider.default_target_interface = values["default_target_interface"].lower()
        provider.updated_at = now_utc()
    if provider:
        session.add(provider)
    session.commit()
    return get_routing_settings(session)


def resolve_routing_rule_config(
    session: Session,
    body: dict[str, Any],
    api_key: BusinessApiKey,
    header_provider: str | None,
) -> tuple[ProviderConfig, ModelConfig] | None:
    gateway = _gateway_options(body)
    if header_provider or gateway.get("provider"):
        return None
    requested = body.get("model") or api_key.default_model or get_settings().default_model
    if not requested:
        return None
    requested = str(requested)
    _check_api_key_policy(api_key, requested)
    rule = session.exec(
        select(RoutingRule).where(
            RoutingRule.public_model_name == requested,
            RoutingRule.is_enabled,
        )
        .order_by(RoutingRule.priority, RoutingRule.id)
    ).first()
    if not rule:
        return None
    provider_model = _select_provider_model_for_rule(session, rule)
    provider_config = get_provider_config(session, provider_model.provider_config_id)
    if not provider_config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider is disabled: {provider_config.name}",
        )
    model_config = ModelConfig(
        provider_config_id=provider_config.id or 0,
        public_model_name=requested,
        upstream_model_name=provider_model.upstream_model_name,
        supported_interfaces=provider_model.supported_interfaces,
        supports_streaming=provider_model.supports_streaming,
        default_target_interface=provider_model.default_target_interface,
        default_parameters=rule.default_parameters,
        is_enabled=True,
        is_default=False,
        notes=f"routing-rule:{rule.name}",
    )
    return provider_config, model_config


def _select_provider_model_for_rule(session: Session, rule: RoutingRule) -> ProviderModel:
    strategy = rule.strategy.lower()
    if strategy == "fixed":
        if rule.provider_model_id is None:
            raise HTTPException(status_code=400, detail="Fixed routing rule has no provider model")
        return _enabled_provider_model(session, rule.provider_model_id)
    if strategy == "fallback":
        candidate_ids = []
        if rule.provider_model_id is not None:
            candidate_ids.append(rule.provider_model_id)
        candidate_ids.extend(_json_loads_int_list(rule.fallback_provider_model_ids))
        return _first_enabled_provider_model(session, candidate_ids)
    if strategy == "weighted":
        weighted_ids = [
            int(item[0])
            for item in sorted(
                _json_loads_float_dict(rule.weight_config).items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]
        if rule.provider_model_id is not None and rule.provider_model_id not in weighted_ids:
            weighted_ids.append(rule.provider_model_id)
        return _first_enabled_provider_model(session, weighted_ids)
    if strategy == "custom" and rule.provider_model_id is not None:
        return _enabled_provider_model(session, rule.provider_model_id)
    raise HTTPException(
        status_code=400,
        detail=f"Routing strategy '{rule.strategy}' cannot select an enabled provider model",
    )


def _enabled_provider_model(session: Session, provider_model_id: int) -> ProviderModel:
    model = get_provider_model(session, provider_model_id)
    if not model.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider model is disabled: {model.upstream_model_name}",
        )
    return model


def _first_enabled_provider_model(session: Session, candidate_ids: list[int]) -> ProviderModel:
    for candidate_id in candidate_ids:
        model = session.get(ProviderModel, candidate_id)
        if model and model.is_enabled:
            return model
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Routing rule has no enabled provider model candidates",
    )


def resolve_provider_name(
    session: Session,
    body: dict[str, Any],
    api_key: BusinessApiKey,
    header_provider: str | None,
) -> str:
    gateway = _gateway_options(body)
    configured_default = session.exec(
        select(ProviderConfig).where(ProviderConfig.is_default, ProviderConfig.is_enabled)
    ).first()
    provider = (
        header_provider
        or gateway.get("provider")
        or api_key.default_provider
        or (configured_default.name if configured_default else None)
        or get_settings().default_provider
    )
    return str(provider).lower()


def resolve_provider_config(
    session: Session,
    body: dict[str, Any],
    api_key: BusinessApiKey,
    header_provider: str | None,
) -> ProviderConfig:
    provider_name = resolve_provider_name(session, body, api_key, header_provider)
    config = get_provider_config_by_name(session, provider_name)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider is not configured: {provider_name}",
        )
    if not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider is disabled: {provider_name}",
        )
    provider_registry.get(config.provider_type)
    return config


def resolve_model_config(
    session: Session,
    body: dict[str, Any],
    api_key: BusinessApiKey,
    provider_config: ProviderConfig,
) -> ModelConfig:
    requested = body.get("model") or api_key.default_model or provider_config.default_model_name
    if not requested:
        default_model = session.exec(
            select(ModelConfig).where(
                ModelConfig.provider_config_id == provider_config.id,
                ModelConfig.is_default,
            )
        ).first()
        requested = (
            default_model.public_model_name if default_model else get_settings().default_model
        )
    requested = str(requested)
    _check_api_key_policy(api_key, requested)
    model = session.exec(
        select(ModelConfig).where(
            ModelConfig.provider_config_id == provider_config.id,
            ModelConfig.public_model_name == requested,
        )
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model is not configured for provider '{provider_config.name}': {requested}",
        )
    if not model.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model is disabled: {requested}",
        )
    return model


def _check_api_key_policy(api_key: BusinessApiKey, requested_model: str) -> None:
    allowed = _json_loads_list(api_key.allowed_models)
    if allowed and requested_model not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key is not allowed to use model: {requested_model}",
        )


def resolve_target_interface(
    body: dict[str, Any],
    source_interface: str,
    header_target_interface: str | None,
    provider_config: ProviderConfig,
    model_config: ModelConfig,
) -> str:
    gateway = _gateway_options(body)
    configured = (
        header_target_interface
        or gateway.get("target_interface")
        or model_config.default_target_interface
        or provider_config.default_target_interface
        or get_settings().default_target_interface
    )
    target = str(configured).lower()
    resolved = source_interface if target == "same" else target
    if resolved not in INTERFACES:
        raise HTTPException(status_code=400, detail=f"Unsupported target interface: {resolved}")
    return resolved


def prepare_upstream_body(body: dict[str, Any], model_config: ModelConfig) -> dict[str, Any]:
    defaults = _json_loads_dict(model_config.default_parameters)
    clean_body = {key: value for key, value in body.items() if key != "gateway"}
    merged = {**defaults, **clean_body}
    merged["model"] = model_config.upstream_model_name
    return merged


def validate_gateway_resolution(
    provider_config: ProviderConfig,
    model_config: ModelConfig,
    source_interface: str,
    target_interface: str,
    stream: bool,
) -> None:
    provider = provider_registry.get(provider_config.provider_type)
    provider.validate_config(provider_config)
    model_interfaces = set(_json_loads_list(model_config.supported_interfaces))
    if source_interface not in model_interfaces:
        detail = (
            f"Model '{model_config.public_model_name}' does not support "
            f"source interface: {source_interface}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    if target_interface not in model_interfaces:
        detail = (
            f"Model '{model_config.public_model_name}' does not support "
            f"target interface: {target_interface}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    if target_interface not in provider.supported_interfaces:
        detail = (
            f"Provider '{provider_config.name}' does not support "
            f"target interface: {target_interface}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    if stream and not provider.supports_streaming:
        raise HTTPException(
            status_code=400,
            detail=f"Provider does not support streaming: {provider_config.name}",
        )
    if stream and not provider_config.supports_streaming:
        raise HTTPException(
            status_code=400,
            detail=f"Streaming is disabled for provider: {provider_config.name}",
        )
    if stream and not model_config.supports_streaming:
        raise HTTPException(
            status_code=400,
            detail=f"Streaming is disabled for model: {model_config.public_model_name}",
        )


def test_provider_config(session: Session, provider_id: int) -> ProviderTestResult:
    config = get_provider_config(session, provider_id)
    try:
        provider = provider_registry.get(config.provider_type)
        provider.validate_config(config)
    except HTTPException as exc:
        return ProviderTestResult(ok=False, message=str(exc.detail))
    return ProviderTestResult(ok=True, message=f"Provider '{config.name}' is ready")
