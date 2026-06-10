from fastapi import APIRouter, HTTPException

from app.deps import CurrentUserDep, SessionDep
from app.schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyRead, ApiKeyUpdate
from app.services.api_keys import (
    create_user_api_key,
    list_user_api_keys,
    revoke_user_api_key,
    update_user_api_key,
)

router = APIRouter(prefix="/keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyRead])
def list_keys(user: CurrentUserDep, session: SessionDep) -> list[ApiKeyRead]:
    return list_user_api_keys(session, user)


@router.post("", response_model=ApiKeyCreated, status_code=201)
def create_key(payload: ApiKeyCreate, user: CurrentUserDep, session: SessionDep) -> ApiKeyCreated:
    return create_user_api_key(session, user, payload)


@router.patch("/{key_id}", response_model=ApiKeyRead)
def update_key(
    key_id: int,
    payload: ApiKeyUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> ApiKeyRead:
    return update_user_api_key(session, user, key_id, payload)


@router.post("/{key_id}/revoke", response_model=ApiKeyRead)
def revoke_key(key_id: int, user: CurrentUserDep, session: SessionDep) -> ApiKeyRead:
    api_key = revoke_user_api_key(session, user, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return api_key
