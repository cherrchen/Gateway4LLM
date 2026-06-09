from fastapi import APIRouter

from app.routers.gateway.anthropic import router as anthropic_router
from app.routers.gateway.chat import router as chat_router
from app.routers.gateway.responses import router as responses_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(responses_router)
router.include_router(anthropic_router)
