from operator import or_
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.core.database import get_session
from app.services.auth.security import verify_password, hash_password, create_access_token
from app.schemas.auth.users import UserResponse, UserCreate, UserToken
from app.models import User

router = APIRouter()

async def authenticate_user(
        session: AsyncSession,
        username: str,
        password: str,
) -> User | None:
    statement = select(User).where(
        or_(
            User.username == username,
            User.email == username,
        )
    )
    result = await session.exec(statement)
    user = result.first()

    if user is None:
        return None

    if not verify_password(password, user.password):
        return None

    logger.debug(user.__dict__)

    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_create: UserCreate,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """
    Register a new user, is going to be added.
    """
    statement = select(User).where(User.username == user_create.username)
    result = await session.exec(statement)
    existing_user = result.first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    user = User(
        username=user_create.username,
        email=user_create.email,
        password=hash_password(user_create.password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user

@router.post("/login", response_model=UserToken, status_code=status.HTTP_200_OK)
async def login_user(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> UserToken:
    """
    User login is going to be added.
    """
    user = await authenticate_user(
        session=session,
        username=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))

    return UserToken(
        access_token=access_token,
        token_type="JWT",
    )
