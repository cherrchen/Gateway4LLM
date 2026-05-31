from fastapi import APIRouter

from app.api.auth.auth import router as auth_router
from app.api.auth.users import router as user_router
from app.api.auth.api_keys import router as api_keys_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(user_router, prefix="/users", tags=["User"])
router.include_router(api_keys_router, prefix="/keys", tags=["Keys"])