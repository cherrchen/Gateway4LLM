from fastapi import APIRouter

from app.routers.api import router as api_router
from app.routers.gateway import router as gateway_router
from app.routers.ui import router as ui_router

router = APIRouter()
router.include_router(ui_router)
router.include_router(api_router)
router.include_router(gateway_router)
