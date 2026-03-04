"""add reconciliation fields to income_event

Revision ID: c4a7e2d8f9b1
Revises: 9d41e3a2b7f1
Create Date: 2026-03-04 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4a7e2d8f9b1"
down_revision = "9d41e3a2b7f1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("income_event")}

    if "bank_operation_number" not in columns:
        op.add_column(
            "income_event",
            sa.Column("bank_operation_number", sa.String(length=80), nullable=True),
        )
    if "reconciled_by" not in columns:
        op.add_column(
            "income_event",
            sa.Column("reconciled_by", sa.String(length=120), nullable=True),
        )
    if "reconciled_at" not in columns:
        op.add_column(
            "income_event",
            sa.Column("reconciled_at", sa.DateTime(), nullable=True),
        )

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("income_event")
    }
    if "ix_income_event_bank_operation_number" not in existing_indexes:
        op.create_index(
            "ix_income_event_bank_operation_number",
            "income_event",
            ["bank_operation_number"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("income_event")}
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("income_event")
    }

    if "ix_income_event_bank_operation_number" in existing_indexes:
        op.drop_index(
            "ix_income_event_bank_operation_number", table_name="income_event"
        )

    if "reconciled_at" in columns:
        op.drop_column("income_event", "reconciled_at")
    if "reconciled_by" in columns:
        op.drop_column("income_event", "reconciled_by")
    if "bank_operation_number" in columns:
        op.drop_column("income_event", "bank_operation_number")
