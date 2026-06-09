import importlib
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("G4L_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("G4L_JWT_SECRET", "test-secret")
    monkeypatch.setenv("G4L_API_KEY_HASH_SECRET", "test-key-secret")

    import app.core.config as config
    import app.core.database as database

    config.get_settings.cache_clear()
    importlib.reload(database)
    SQLModel.metadata.drop_all(database.engine)

    from app.main import create_app

    test_app = create_app()
    with TestClient(test_app) as test_client:
        yield test_client
