"""add debtor invoice fields to daily income

Revision ID: f9d8c7b6a5e4
Revises: f1c2d3e4b5a6
Create Date: 2026-03-05 09:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "f9d8c7b6a5e4"
down_revision = "f1c2d3e4b5a6"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "daily_income" not in existing_tables:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("daily_income")
    }

    columns_to_add = [
        sa.Column("payment_method", sa.String(length=20), nullable=True),
        sa.Column("debtor_type", sa.String(length=20), nullable=True),
        sa.Column("debtor_natural_full_name", sa.String(length=150), nullable=True),
        sa.Column(
            "debtor_natural_identity_number",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column("debtor_natural_bank_account", sa.String(length=80), nullable=True),
        sa.Column("debtor_legal_entity_name", sa.String(length=200), nullable=True),
        sa.Column("debtor_legal_reeup_code", sa.String(length=50), nullable=True),
        sa.Column("debtor_legal_address", sa.String(length=255), nullable=True),
        sa.Column("debtor_legal_credit_branch", sa.String(length=120), nullable=True),
        sa.Column("debtor_legal_bank_account", sa.String(length=80), nullable=True),
        sa.Column(
            "debtor_legal_contract_number",
            sa.String(length=80),
            nullable=True,
        ),
    ]

    with op.batch_alter_table("daily_income") as batch_op:
        for column in columns_to_add:
            if column.name not in existing_columns:
                batch_op.add_column(column)

    op.execute(
        "UPDATE daily_income SET payment_method = 'cash' WHERE payment_method IS NULL"
    )

    refreshed_columns = {
        column["name"] for column in sa.inspect(bind).get_columns("daily_income")
    }

    with op.batch_alter_table("daily_income") as batch_op:
        if "payment_method" in refreshed_columns:
            batch_op.alter_column(
                "payment_method",
                existing_type=sa.String(length=20),
                nullable=False,
                server_default="cash",
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "daily_income" not in existing_tables:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("daily_income")
    }

    columns_to_drop = [
        "debtor_legal_contract_number",
        "debtor_legal_bank_account",
        "debtor_legal_credit_branch",
        "debtor_legal_address",
        "debtor_legal_reeup_code",
        "debtor_legal_entity_name",
        "debtor_natural_bank_account",
        "debtor_natural_identity_number",
        "debtor_natural_full_name",
        "debtor_type",
        "payment_method",
    ]

    with op.batch_alter_table("daily_income") as batch_op:
        for column_name in columns_to_drop:
            if column_name in existing_columns:
                batch_op.drop_column(column_name)
