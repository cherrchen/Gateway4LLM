from fastapi import APIRouter

from app.routers.api.auth import router as auth_router
from app.routers.api.keys import router as keys_router
from app.routers.api.logs import router as logs_router
from app.routers.api.providers import router as providers_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(keys_router)
router.include_router(logs_router)
router.include_router(providers_router)
