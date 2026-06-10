from fastapi import APIRouter

from app.deps import CurrentUserDep, SessionDep
from app.schemas import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigUpdate,
    ProviderConfigCreate,
    ProviderConfigRead,
    ProviderConfigUpdate,
    ProviderTestResult,
    ProviderTypeRead,
    RoutingSettingsRead,
    RoutingSettingsUpdate,
)
from app.services.provider_configs import (
    create_model_config,
    create_provider_config,
    get_model_config_read,
    get_provider_config_read,
    get_routing_settings,
    list_model_configs,
    list_provider_configs,
    list_provider_types,
    reject_model_delete,
    reject_provider_delete,
    set_default_model,
    set_default_provider,
    set_model_enabled,
    set_provider_enabled,
    test_provider_config,
    update_model_config,
    update_provider_config,
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
