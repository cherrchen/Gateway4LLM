from fastapi import FastAPI
from app.api.v1.endpoints import v1_router

app = FastAPI(
    title="LLM API Gateway",
    description="An API gateway for managing LLM requests.",
    version="0.1.0",
)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {"status": "ok"}