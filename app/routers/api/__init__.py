from fastapi import APIRouter

from app.routers.api.auth import router as auth_router
from app.routers.api.keys import router as keys_router
from app.routers.api.logs import router as logs_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(keys_router)
router.include_router(logs_router)
