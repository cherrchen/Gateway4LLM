import uuid
import secrets

from fastapi import APIRouter, Depends, status

from app.schemas.auth.users import UserResponse, UserCreate, UserToken
from app.core.database import get_session, AsyncSession

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(session: AsyncSession = Depends(get_session)):
    """
    Register a new user, is going to be added.
    """
    return UserResponse(
        id=uuid.uuid4(),
    )

@router.post("/login", response_model=UserToken, status_code=status.HTTP_200_OK)
async def login_user(session: AsyncSession = Depends(get_session)):
    """
    User login is going to be added.
    """
    return UserToken(
        token_type="JWT",
        access_token=secrets.token_hex(20),
    )
