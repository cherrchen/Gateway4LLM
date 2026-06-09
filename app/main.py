from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db
from app.routers import router as app_router


def create_app() -> FastAPI:
    app = FastAPI(title="Gateway4LLM")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(app_router)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
