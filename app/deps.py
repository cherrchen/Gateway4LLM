from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from loguru import logger
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.models.users import User
from app.models.api_keys import APIKey
from app.services.auth.security import decode_access_token, hash_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# api_key_header = APIKeyHeader(name="x-api-key")

async def get_current_user(
        session: Annotated[AsyncSession, Depends(get_session)],
        token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception
        logger.debug(f"{user_id} user_id is None")
    except ValueError:
        logger.debug(f"user_id is None")
        raise credentials_exception

    try:
        user_id_uuid = UUID(user_id)
        logger.debug(f"{user_id} user_id is inted")
    except ValueError:
        logger.debug(f"{user_id} user_id is invalid")
        raise credentials_exception

    user = await session.get(User, user_id_uuid)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

async def get_current_api_key(
        session: Annotated[AsyncSession, Depends(get_session)],
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> APIKey:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key Header",
        )

    key_hash = hash_api_key(x_api_key)

    statement = select(APIKey).where(APIKey.key_hash == key_hash)

    result = await session.exec(statement)
    api_key = result.first()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive API Key",
        )

    api_key.last_used_at = datetime.now(timezone.utc)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key