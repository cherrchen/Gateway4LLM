from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.v1.endpoints import router as v1_router
from app.api.auth import router as auth_router
from app.core.database import db_init, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("FastAPI Backend Started!")
    try:
        await db_init()
        logger.debug("FastAPI Database Inited!")
        yield
    finally:
        await engine.dispose()
        logger.debug("FastAPI Database Disconnected!")


app = FastAPI(
    title="LLM API Gateway",
    description="An API gateway for managing LLM requests.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api")

@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {"status": "ok"}
