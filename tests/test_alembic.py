from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_alembic_upgrade_head_creates_provider_registry_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "migrated.db"
    url = f"sqlite:///{db_path}"
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "head")

    engine = create_engine(url)
    inspector = inspect(engine)
    assert {
        "user",
        "businessapikey",
        "gatewaylog",
        "providerconfig",
        "modelconfig",
        "providermodel",
        "routingrule",
        "alembic_version",
    }.issubset(set(inspector.get_table_names()))
    key_columns = {column["name"] for column in inspector.get_columns("businessapikey")}
    assert {"default_provider", "default_model", "allowed_models"}.issubset(key_columns)
    provider_model_columns = {column["name"] for column in inspector.get_columns("providermodel")}
    assert {"upstream_model_name", "capabilities", "health_status"}.issubset(
        provider_model_columns
    )
    routing_rule_columns = {column["name"] for column in inspector.get_columns("routingrule")}
    assert {"public_model_name", "strategy", "provider_model_id"}.issubset(routing_rule_columns)
