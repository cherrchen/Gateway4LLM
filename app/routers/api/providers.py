from fastapi import APIRouter

from app.deps import CurrentUserDep, SessionDep
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
from app.services.provider_configs import (
    create_model_config,
    create_provider_config,
    create_provider_model,
    create_routing_rule,
    get_model_config_read,
    get_provider_config_read,
    get_provider_model_read,
    get_routing_rule_read,
    get_routing_settings,
    list_model_configs,
    list_provider_configs,
    list_provider_models,
    list_provider_types,
    list_routing_rules,
    reject_model_delete,
    reject_provider_delete,
    reject_provider_model_delete,
    reject_routing_rule_delete,
    set_default_model,
    set_default_provider,
    set_default_provider_model,
    set_model_enabled,
    set_provider_enabled,
    set_provider_model_enabled,
    set_routing_rule_enabled,
    sync_provider_models,
    test_provider_config,
    test_provider_model,
    update_model_config,
    update_provider_config,
    update_provider_model,
    update_routing_rule,
    update_routing_settings,
)

router = APIRouter(tags=["providers"])


@router.get("/provider-types", response_model=list[ProviderTypeRead])
def provider_types(user: CurrentUserDep) -> list[ProviderTypeRead]:
    return list_provider_types()


@router.get("/providers", response_model=list[ProviderConfigRead])
def providers(user: CurrentUserDep, session: SessionDep) -> list[ProviderConfigRead]:
    return list_provider_configs(session)


@router.get("/providers/{provider_id}", response_model=ProviderConfigRead)
def provider(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return get_provider_config_read(session, provider_id)


@router.post("/providers", response_model=ProviderConfigRead, status_code=201)
def create_provider(
    payload: ProviderConfigCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return create_provider_config(session, payload)


@router.patch("/providers/{provider_id}", response_model=ProviderConfigRead)
def update_provider(
    provider_id: int,
    payload: ProviderConfigUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return update_provider_config(session, provider_id, payload)


@router.post("/providers/{provider_id}/enable", response_model=ProviderConfigRead)
def enable_provider(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return set_provider_enabled(session, provider_id, True)


@router.post("/providers/{provider_id}/disable", response_model=ProviderConfigRead)
def disable_provider(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return set_provider_enabled(session, provider_id, False)


@router.post("/providers/{provider_id}/set-default", response_model=ProviderConfigRead)
def default_provider(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderConfigRead:
    return set_default_provider(session, provider_id)


@router.delete("/providers/{provider_id}", status_code=405)
def delete_provider(provider_id: int, user: CurrentUserDep) -> None:
    reject_provider_delete(provider_id)


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResult)
def test_provider(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderTestResult:
    return test_provider_config(session, provider_id)


@router.get("/models", response_model=list[ModelConfigRead])
def models(
    user: CurrentUserDep,
    session: SessionDep,
    provider_id: int | None = None,
) -> list[ModelConfigRead]:
    return list_model_configs(session, provider_id)


@router.get("/models/{model_id}", response_model=ModelConfigRead)
def model(
    model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return get_model_config_read(session, model_id)


@router.post("/models", response_model=ModelConfigRead, status_code=201)
def create_model(
    payload: ModelConfigCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return create_model_config(session, payload)


@router.patch("/models/{model_id}", response_model=ModelConfigRead)
def update_model(
    model_id: int,
    payload: ModelConfigUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return update_model_config(session, model_id, payload)


@router.post("/models/{model_id}/enable", response_model=ModelConfigRead)
def enable_model(
    model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return set_model_enabled(session, model_id, True)


@router.post("/models/{model_id}/disable", response_model=ModelConfigRead)
def disable_model(
    model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return set_model_enabled(session, model_id, False)


@router.post("/models/{model_id}/set-default", response_model=ModelConfigRead)
def default_model(
    model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ModelConfigRead:
    return set_default_model(session, model_id)


@router.delete("/models/{model_id}", status_code=405)
def delete_model(model_id: int, user: CurrentUserDep) -> None:
    reject_model_delete(model_id)


@router.get("/provider-models", response_model=list[ProviderModelRead])
def provider_models(
    user: CurrentUserDep,
    session: SessionDep,
    provider_id: int | None = None,
) -> list[ProviderModelRead]:
    return list_provider_models(session, provider_id)


@router.get("/provider-models/{provider_model_id}", response_model=ProviderModelRead)
def provider_model(
    provider_model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return get_provider_model_read(session, provider_model_id)


@router.post("/provider-models", response_model=ProviderModelRead, status_code=201)
def create_provider_model_route(
    payload: ProviderModelCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return create_provider_model(session, payload)


@router.patch("/provider-models/{provider_model_id}", response_model=ProviderModelRead)
def update_provider_model_route(
    provider_model_id: int,
    payload: ProviderModelUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return update_provider_model(session, provider_model_id, payload)


@router.post("/provider-models/{provider_model_id}/enable", response_model=ProviderModelRead)
def enable_provider_model(
    provider_model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return set_provider_model_enabled(session, provider_model_id, True)


@router.post("/provider-models/{provider_model_id}/disable", response_model=ProviderModelRead)
def disable_provider_model(
    provider_model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return set_provider_model_enabled(session, provider_model_id, False)


@router.post("/provider-models/{provider_model_id}/set-default", response_model=ProviderModelRead)
def default_provider_model(
    provider_model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderModelRead:
    return set_default_provider_model(session, provider_model_id)


@router.post("/provider-models/{provider_model_id}/test", response_model=ProviderTestResult)
def test_provider_model_route(
    provider_model_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> ProviderTestResult:
    return test_provider_model(session, provider_model_id)


@router.post(
    "/providers/{provider_id}/provider-models/sync",
    response_model=list[ProviderModelRead],
)
def sync_provider_model_route(
    provider_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> list[ProviderModelRead]:
    return sync_provider_models(session, provider_id)


@router.delete("/provider-models/{provider_model_id}", status_code=405)
def delete_provider_model(provider_model_id: int, user: CurrentUserDep) -> None:
    reject_provider_model_delete(provider_model_id)


@router.get("/routing-rules", response_model=list[RoutingRuleRead])
def routing_rules(
    user: CurrentUserDep,
    session: SessionDep,
    public_model_name: str | None = None,
) -> list[RoutingRuleRead]:
    return list_routing_rules(session, public_model_name)


@router.get("/routing-rules/{rule_id}", response_model=RoutingRuleRead)
def routing_rule(
    rule_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingRuleRead:
    return get_routing_rule_read(session, rule_id)


@router.post("/routing-rules", response_model=RoutingRuleRead, status_code=201)
def create_routing_rule_route(
    payload: RoutingRuleCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingRuleRead:
    return create_routing_rule(session, payload)


@router.patch("/routing-rules/{rule_id}", response_model=RoutingRuleRead)
def update_routing_rule_route(
    rule_id: int,
    payload: RoutingRuleUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingRuleRead:
    return update_routing_rule(session, rule_id, payload)


@router.post("/routing-rules/{rule_id}/enable", response_model=RoutingRuleRead)
def enable_routing_rule(
    rule_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingRuleRead:
    return set_routing_rule_enabled(session, rule_id, True)


@router.post("/routing-rules/{rule_id}/disable", response_model=RoutingRuleRead)
def disable_routing_rule(
    rule_id: int,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingRuleRead:
    return set_routing_rule_enabled(session, rule_id, False)


@router.delete("/routing-rules/{rule_id}", status_code=405)
def delete_routing_rule(rule_id: int, user: CurrentUserDep) -> None:
    reject_routing_rule_delete(rule_id)


@router.get("/settings/routing", response_model=RoutingSettingsRead, tags=["settings"])
def routing_settings(
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingSettingsRead:
    return get_routing_settings(session)


@router.patch("/settings/routing", response_model=RoutingSettingsRead, tags=["settings"])
def update_routing(
    payload: RoutingSettingsUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> RoutingSettingsRead:
    return update_routing_settings(session, payload)
