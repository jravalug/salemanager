"""add business cash fund config

Revision ID: c7d9e2f4a1b3
Revises: b5c9d3e7f1a2
Create Date: 2026-03-04 17:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7d9e2f4a1b3"
down_revision = "b5c9d3e7f1a2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "business_cash_fund_config" not in existing_tables:
        op.create_table(
            "business_cash_fund_config",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("regime", sa.String(length=20), nullable=False),
            sa.Column("location", sa.String(length=20), nullable=False),
            sa.Column("subaccount_code", sa.String(length=50), nullable=False),
            sa.Column("display_name", sa.String(length=120), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_custom", sa.Boolean(), nullable=False),
            sa.Column("threshold_max_per_operation", sa.Float(), nullable=True),
            sa.Column("requires_documentation", sa.Boolean(), nullable=False),
            sa.Column("target_balance", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["business_id"],
                ["business.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "business_id",
                "subaccount_code",
                name="uq_business_cash_fund_config_business_subaccount",
            ),
            sa.CheckConstraint(
                "regime IN ('fiscal', 'financiera')",
                name="business_cash_fund_config_regime_allowed_values",
            ),
            sa.CheckConstraint(
                "location IN ('cash_box', 'bank_account')",
                name="business_cash_fund_config_location_allowed_values",
            ),
            sa.CheckConstraint(
                "threshold_max_per_operation IS NULL OR threshold_max_per_operation > 0",
                name="business_cash_fund_config_threshold_positive_or_null",
            ),
            sa.CheckConstraint(
                "target_balance IS NULL OR target_balance >= 0",
                name="business_cash_fund_config_target_non_negative_or_null",
            ),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("business_cash_fund_config")
    }
    for index_name, columns in [
        ("ix_business_cash_fund_config_business_id", ["business_id"]),
        ("ix_business_cash_fund_config_regime", ["regime"]),
        ("ix_business_cash_fund_config_location", ["location"]),
        ("ix_business_cash_fund_config_subaccount_code", ["subaccount_code"]),
    ]:
        if index_name not in existing_indexes:
            op.create_index(
                index_name,
                "business_cash_fund_config",
                columns,
                unique=False,
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "business_cash_fund_config" in existing_tables:
        existing_indexes = {
            index["name"]
            for index in inspector.get_indexes("business_cash_fund_config")
        }
        for index_name in [
            "ix_business_cash_fund_config_subaccount_code",
            "ix_business_cash_fund_config_location",
            "ix_business_cash_fund_config_regime",
            "ix_business_cash_fund_config_business_id",
        ]:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="business_cash_fund_config")
        op.drop_table("business_cash_fund_config")
