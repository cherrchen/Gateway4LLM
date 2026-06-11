"""add provider model catalog and routing rules

Revision ID: 20260611_0002
Revises: 20260610_0001
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "20260611_0002"
down_revision: str | None = "20260610_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "providermodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_config_id", sa.Integer(), nullable=False),
        sa.Column("upstream_model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("supported_interfaces", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("default_target_interface", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("input_price_per_million_tokens", sa.Float(), nullable=True),
        sa.Column("output_price_per_million_tokens", sa.Float(), nullable=True),
        sa.Column("capabilities", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("health_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["provider_config_id"], ["providerconfig.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_providermodel_provider_config_id"),
        "providermodel",
        ["provider_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_providermodel_upstream_model_name"),
        "providermodel",
        ["upstream_model_name"],
        unique=False,
    )

    op.create_table(
        "routingrule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("public_model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("strategy", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provider_model_id", sa.Integer(), nullable=True),
        sa.Column(
            "fallback_provider_model_ids",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
        ),
        sa.Column("weight_config", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("custom_config", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("default_parameters", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["provider_model_id"], ["providermodel.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_routingrule_public_model_name"),
        "routingrule",
        ["public_model_name"],
        unique=False,
    )
    op.create_index(op.f("ix_routingrule_strategy"), "routingrule", ["strategy"], unique=False)
    op.create_index(op.f("ix_routingrule_priority"), "routingrule", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_routingrule_priority"), table_name="routingrule")
    op.drop_index(op.f("ix_routingrule_strategy"), table_name="routingrule")
    op.drop_index(op.f("ix_routingrule_public_model_name"), table_name="routingrule")
    op.drop_table("routingrule")
    op.drop_index(op.f("ix_providermodel_upstream_model_name"), table_name="providermodel")
    op.drop_index(op.f("ix_providermodel_provider_config_id"), table_name="providermodel")
    op.drop_table("providermodel")
