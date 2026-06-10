"""initial provider registry schema

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "20260610_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "providerconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provider_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("base_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("api_key_env_var", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("api_key_secret_ref", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("default_target_interface", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("default_model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("timeout_seconds", sa.Float(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_providerconfig_name"), "providerconfig", ["name"], unique=True)
    op.create_index(
        op.f("ix_providerconfig_provider_type"),
        "providerconfig",
        ["provider_type"],
        unique=False,
    )

    op.create_table(
        "businessapikey",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("key_prefix", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("default_provider", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("default_model", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("allowed_models", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_businessapikey_key_hash"), "businessapikey", ["key_hash"], unique=True)
    op.create_index(
        op.f("ix_businessapikey_key_prefix"),
        "businessapikey",
        ["key_prefix"],
        unique=False,
    )
    op.create_index(
        op.f("ix_businessapikey_user_id"),
        "businessapikey",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "modelconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_config_id", sa.Integer(), nullable=False),
        sa.Column("public_model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("upstream_model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("supported_interfaces", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("default_target_interface", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("default_parameters", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["provider_config_id"], ["providerconfig.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_modelconfig_provider_config_id"),
        "modelconfig",
        ["provider_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_modelconfig_public_model_name"),
        "modelconfig",
        ["public_model_name"],
        unique=False,
    )

    op.create_table(
        "gatewaylog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("api_key_id", sa.Integer(), nullable=True),
        sa.Column("api_key_prefix", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("route", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source_interface", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("target_interface", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("request_meta", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("response_meta", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gatewaylog_api_key_id"), "gatewaylog", ["api_key_id"], unique=False)
    op.create_index(op.f("ix_gatewaylog_created_at"), "gatewaylog", ["created_at"], unique=False)
    op.create_index(op.f("ix_gatewaylog_user_id"), "gatewaylog", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gatewaylog_user_id"), table_name="gatewaylog")
    op.drop_index(op.f("ix_gatewaylog_created_at"), table_name="gatewaylog")
    op.drop_index(op.f("ix_gatewaylog_api_key_id"), table_name="gatewaylog")
    op.drop_table("gatewaylog")
    op.drop_index(op.f("ix_modelconfig_public_model_name"), table_name="modelconfig")
    op.drop_index(op.f("ix_modelconfig_provider_config_id"), table_name="modelconfig")
    op.drop_table("modelconfig")
    op.drop_index(op.f("ix_businessapikey_user_id"), table_name="businessapikey")
    op.drop_index(op.f("ix_businessapikey_key_prefix"), table_name="businessapikey")
    op.drop_index(op.f("ix_businessapikey_key_hash"), table_name="businessapikey")
    op.drop_table("businessapikey")
    op.drop_index(op.f("ix_providerconfig_provider_type"), table_name="providerconfig")
    op.drop_index(op.f("ix_providerconfig_name"), table_name="providerconfig")
    op.drop_table("providerconfig")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
