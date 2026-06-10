from collections.abc import Generator
from pathlib import Path

from alembic.config import Config
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from alembic import command
from app.core.config import get_settings


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine()


def init_db() -> None:
    _run_migrations()
    _seed_defaults()


def _run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    config.set_main_option("sqlalchemy.url", str(engine.url))
    command.upgrade(config, "head")


def _seed_defaults() -> None:
    from app.services.provider_configs import ensure_default_configs

    with Session(engine) as session:
        ensure_default_configs(session)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
