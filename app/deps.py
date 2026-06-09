from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from jwt import PyJWTError
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import BusinessApiKey, User, now_utc
from app.security import decode_access_token, hash_api_key

SessionDep = Annotated[Session, Depends(get_session)]


def _bearer_value(value: str | None) -> str | None:
    if value and value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return None


def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    token = _bearer_value(authorization) or access_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing JWT bearer token",
        )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token",
        ) from exc
    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_api_key_principal(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[User, BusinessApiKey]:
    token = _bearer_value(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key bearer token",
        )
    api_key = session.exec(
        select(BusinessApiKey).where(BusinessApiKey.key_hash == hash_api_key(token))
    ).first()
    if not api_key or api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    user = session.get(User, api_key.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive API key owner",
        )
    api_key.last_used_at = now_utc()
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return user, api_key


ApiKeyPrincipalDep = Annotated[tuple[User, BusinessApiKey], Depends(get_api_key_principal)]
