from fastapi import APIRouter

from app.routers.ui.auth import router as auth_router
from app.routers.ui.dashboard import router as dashboard_router
from app.routers.ui.gateway_test import router as gateway_test_router
from app.routers.ui.keys import router as keys_router
from app.routers.ui.logs import router as logs_router
from app.routers.ui.pages import router as pages_router
from app.routers.ui.providers import router as providers_router

router = APIRouter(tags=["demo-ui"])
router.include_router(pages_router)
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(keys_router)
router.include_router(logs_router)
router.include_router(gateway_test_router)
router.include_router(providers_router)
