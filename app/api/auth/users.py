from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.users import User
from app.schemas.auth.users import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_user(
        current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    return current_user

