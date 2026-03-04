"""add cash subaccount balance and movement

Revision ID: e8f1a2b3c4d5
Revises: f4b8d1c9e2a3
Create Date: 2026-03-04 15:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e8f1a2b3c4d5"
down_revision = "f4b8d1c9e2a3"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()

    if "cash_subaccount_balance" not in existing_tables:
        op.create_table(
            "cash_subaccount_balance",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("regime", sa.String(length=20), nullable=False),
            sa.Column("location", sa.String(length=20), nullable=False),
            sa.Column("subaccount_code", sa.String(length=50), nullable=False),
            sa.Column("subaccount_name", sa.String(length=120), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("current_balance", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["business_id"], ["business.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "business_id",
                "subaccount_code",
                name="uq_cash_subaccount_balance_business_code",
            ),
            sa.CheckConstraint(
                "regime IN ('fiscal', 'financiera')",
                name="cash_subaccount_balance_regime_allowed_values",
            ),
            sa.CheckConstraint(
                "location IN ('cash_box', 'bank_account')",
                name="cash_subaccount_balance_location_allowed_values",
            ),
            sa.CheckConstraint(
                "currency = 'CUP'",
                name="cash_subaccount_balance_currency_cup_only",
            ),
            sa.CheckConstraint(
                "current_balance >= 0",
                name="cash_subaccount_balance_non_negative",
            ),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("cash_subaccount_balance")
    }

    if "ix_cash_subaccount_balance_business_id" not in existing_indexes:
        op.create_index(
            "ix_cash_subaccount_balance_business_id",
            "cash_subaccount_balance",
            ["business_id"],
            unique=False,
        )
    if "ix_cash_subaccount_balance_regime" not in existing_indexes:
        op.create_index(
            "ix_cash_subaccount_balance_regime",
            "cash_subaccount_balance",
            ["regime"],
            unique=False,
        )
    if "ix_cash_subaccount_balance_location" not in existing_indexes:
        op.create_index(
            "ix_cash_subaccount_balance_location",
            "cash_subaccount_balance",
            ["location"],
            unique=False,
        )
    if "ix_cash_subaccount_balance_subaccount_code" not in existing_indexes:
        op.create_index(
            "ix_cash_subaccount_balance_subaccount_code",
            "cash_subaccount_balance",
            ["subaccount_code"],
            unique=False,
        )

    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "cash_subaccount_movement" not in existing_tables:
        op.create_table(
            "cash_subaccount_movement",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("balance_id", sa.Integer(), nullable=False),
            sa.Column("regime", sa.String(length=20), nullable=False),
            sa.Column("location", sa.String(length=20), nullable=False),
            sa.Column("subaccount_code", sa.String(length=50), nullable=False),
            sa.Column("movement_kind", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("source_type", sa.String(length=30), nullable=True),
            sa.Column("source_ref", sa.String(length=120), nullable=True),
            sa.Column(
                "counterparty_subaccount_code", sa.String(length=50), nullable=True
            ),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["balance_id"], ["cash_subaccount_balance.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["business_id"], ["business.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(
                "regime IN ('fiscal', 'financiera')",
                name="cash_subaccount_movement_regime_allowed_values",
            ),
            sa.CheckConstraint(
                "location IN ('cash_box', 'bank_account')",
                name="cash_subaccount_movement_location_allowed_values",
            ),
            sa.CheckConstraint(
                "movement_kind IN ('inflow', 'outflow', 'transfer_in', 'transfer_out')",
                name="cash_subaccount_movement_kind_allowed_values",
            ),
            sa.CheckConstraint(
                "amount > 0",
                name="cash_subaccount_movement_amount_positive",
            ),
            sa.CheckConstraint(
                "currency = 'CUP'",
                name="cash_subaccount_movement_currency_cup_only",
            ),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("cash_subaccount_movement")
    }

    for index_name, columns in [
        ("ix_cash_subaccount_movement_business_id", ["business_id"]),
        ("ix_cash_subaccount_movement_balance_id", ["balance_id"]),
        ("ix_cash_subaccount_movement_regime", ["regime"]),
        ("ix_cash_subaccount_movement_location", ["location"]),
        ("ix_cash_subaccount_movement_subaccount_code", ["subaccount_code"]),
        ("ix_cash_subaccount_movement_movement_kind", ["movement_kind"]),
        ("ix_cash_subaccount_movement_occurred_at", ["occurred_at"]),
        ("ix_cash_subaccount_movement_source_type", ["source_type"]),
        ("ix_cash_subaccount_movement_source_ref", ["source_ref"]),
    ]:
        if index_name not in existing_indexes:
            op.create_index(
                index_name, "cash_subaccount_movement", columns, unique=False
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if "cash_subaccount_movement" in existing_tables:
        existing_indexes = {
            index["name"] for index in inspector.get_indexes("cash_subaccount_movement")
        }
        for index_name in [
            "ix_cash_subaccount_movement_source_ref",
            "ix_cash_subaccount_movement_source_type",
            "ix_cash_subaccount_movement_occurred_at",
            "ix_cash_subaccount_movement_movement_kind",
            "ix_cash_subaccount_movement_subaccount_code",
            "ix_cash_subaccount_movement_location",
            "ix_cash_subaccount_movement_regime",
            "ix_cash_subaccount_movement_balance_id",
            "ix_cash_subaccount_movement_business_id",
        ]:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="cash_subaccount_movement")
        op.drop_table("cash_subaccount_movement")

    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    if "cash_subaccount_balance" in existing_tables:
        existing_indexes = {
            index["name"] for index in inspector.get_indexes("cash_subaccount_balance")
        }
        for index_name in [
            "ix_cash_subaccount_balance_subaccount_code",
            "ix_cash_subaccount_balance_location",
            "ix_cash_subaccount_balance_regime",
            "ix_cash_subaccount_balance_business_id",
        ]:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="cash_subaccount_balance")
        op.drop_table("cash_subaccount_balance")
