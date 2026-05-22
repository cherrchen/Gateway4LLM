from fastapi import APIRouter

from app.api.v1.endpoints.chat import router as chat_router

v1_router = APIRouter()
v1_router.include_router(chat_router, prefix="/chat", tags=["Chat"])