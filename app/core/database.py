from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=True if settings.app_mode == "dev" else False,  # keep True in Develop Mode
    future=True,
)

async def db_init():
    async with engine.begin() as conn: # type: ignore
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
