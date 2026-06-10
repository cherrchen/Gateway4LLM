import json

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.orm.session import Session

from app.models import BusinessApiKey, User, now_utc
from app.schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyRead, ApiKeyUpdate
from app.security import generate_api_key, hash_api_key, key_prefix


def _parse_allowed_models(value: str | None) -> list[str] | None:
    if not value:
        return None
    parsed = json.loads(value)
    return [str(item) for item in parsed] if isinstance(parsed, list) else None


def _dump_allowed_models(value: list[str] | None) -> str | None:
    if not value:
        return None
    return json.dumps([str(item) for item in value], ensure_ascii=False, separators=(",", ":"))


def api_key_to_read(api_key: BusinessApiKey) -> ApiKeyRead:
    return ApiKeyRead(
        **api_key.model_dump(exclude={"allowed_models"}),
        allowed_models=_parse_allowed_models(api_key.allowed_models),
    )


def list_user_api_keys(session: Session, user: User) -> list[ApiKeyRead]:
    rows = session.exec(select(BusinessApiKey).where(BusinessApiKey.user_id == user.id)).all()
    return [api_key_to_read(row) for row in rows]


def create_user_api_key(session: Session, user: User, payload: ApiKeyCreate) -> ApiKeyCreated:
    raw_key = generate_api_key()
    api_key = BusinessApiKey(
        user_id=user.id,
        name=payload.name.strip(),
        key_hash=hash_api_key(raw_key),
        key_prefix=key_prefix(raw_key),
        default_provider=(payload.default_provider or "").strip().lower() or None,
        default_model=(payload.default_model or "").strip() or None,
        allowed_models=_dump_allowed_models(payload.allowed_models),
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return ApiKeyCreated(api_key=raw_key, **api_key_to_read(api_key).model_dump())


def update_user_api_key(
    session: Session,
    user: User,
    key_id: int,
    payload: ApiKeyUpdate,
) -> ApiKeyRead:
    api_key = session.get(BusinessApiKey, key_id)
    if not api_key or api_key.user_id != user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revoked API key policy cannot be updated",
        )
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and values["name"] is not None:
        api_key.name = values["name"].strip()
    if "default_provider" in values:
        api_key.default_provider = (values["default_provider"] or "").strip().lower() or None
    if "default_model" in values:
        api_key.default_model = (values["default_model"] or "").strip() or None
    if "allowed_models" in values:
        api_key.allowed_models = _dump_allowed_models(values["allowed_models"])
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key_to_read(api_key)


def revoke_user_api_key(session: Session, user: User, key_id: int) -> ApiKeyRead | None:
    api_key = session.get(BusinessApiKey, key_id)
    if not api_key or api_key.user_id != user.id:
        return None
    if not api_key.is_revoked:
        api_key.is_revoked = True
        api_key.revoked_at = now_utc()
        session.add(api_key)
        session.commit()
        session.refresh(api_key)
    return api_key_to_read(api_key)
