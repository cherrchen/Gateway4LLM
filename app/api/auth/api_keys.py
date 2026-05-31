from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.models.users import User
from app.models.api_keys import APIKey
from app.schemas.auth.api_keys import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse
from app.services.auth.security import create_api_key as to_create_api_key
from app.deps import get_current_active_user, get_current_api_key

router = APIRouter()

@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
        api_key_create: APIKeyCreate,
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> APIKeyCreatedResponse:
    raw_api_key, prefix, key_hash = to_create_api_key()
    expire_time = timedelta(days=api_key_create.expire_time) if api_key_create.expire_time is not None else None
    expire_at = datetime.now(timezone.utc) + expire_time if api_key_create.expire_time is not None else None
    api_key = APIKey(
        name=api_key_create.name,
        key_hash=key_hash,
        prefix=prefix,
        expire_time=expire_time,
        expires_at=expire_at,
        user_id=current_user.id,
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        api_key=raw_api_key,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        user_id=api_key.user_id,
    )

@router.get("", response_model=list[APIKeyResponse], status_code=status.HTTP_200_OK)
async def get_api_key_list(
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> Sequence[APIKey]:
    statement = select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at)

    result = await session.exec(statement)
    api_keys = result.all()
    return api_keys

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
        api_key_id: int,
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    api_key = await session.get(APIKey, api_key_id)

    if api_key is None or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id {api_key_id} was not found.",
        )

    api_key.is_active = False
    api_key.deleted_at = datetime.now(timezone.utc)

    session.add(api_key)
    await session.commit()

    return None