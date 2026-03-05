"""add debtor invoice fields to sale

Revision ID: f1c2d3e4b5a6
Revises: e3b6a4d1f9c2
Create Date: 2026-03-04 23:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "f1c2d3e4b5a6"
down_revision = "e3b6a4d1f9c2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "sale" not in existing_tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("sale")}

    columns_to_add = [
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

    with op.batch_alter_table("sale") as batch_op:
        for column in columns_to_add:
            if column.name not in existing_columns:
                batch_op.add_column(column)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "sale" not in existing_tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("sale")}

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
    ]

    with op.batch_alter_table("sale") as batch_op:
        for column_name in columns_to_drop:
            if column_name in existing_columns:
                batch_op.drop_column(column_name)
