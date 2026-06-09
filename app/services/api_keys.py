from sqlmodel import select
from sqlmodel.orm.session import Session

from app.models import BusinessApiKey, User, now_utc
from app.schemas import ApiKeyCreate, ApiKeyCreated
from app.security import generate_api_key, hash_api_key, key_prefix


def list_user_api_keys(session: Session, user: User) -> list[BusinessApiKey]:
    return list(session.exec(select(BusinessApiKey).where(BusinessApiKey.user_id == user.id)).all())


def create_user_api_key(session: Session, user: User, payload: ApiKeyCreate) -> ApiKeyCreated:
    raw_key = generate_api_key()
    api_key = BusinessApiKey(
        user_id=user.id,
        name=payload.name,
        key_hash=hash_api_key(raw_key),
        key_prefix=key_prefix(raw_key),
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return ApiKeyCreated(api_key=raw_key, **api_key.model_dump())


def revoke_user_api_key(session: Session, user: User, key_id: int) -> BusinessApiKey | None:
    api_key = session.get(BusinessApiKey, key_id)
    if not api_key or api_key.user_id != user.id:
        return None
    if not api_key.is_revoked:
        api_key.is_revoked = True
        api_key.revoked_at = now_utc()
        session.add(api_key)
        session.commit()
        session.refresh(api_key)
    return api_key
