"""add collection receipt model

Revision ID: f4b8d1c9e2a3
Revises: c4a7e2d8f9b1
Create Date: 2026-03-04 14:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4b8d1c9e2a3"
down_revision = "c4a7e2d8f9b1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if "collection_receipt" not in existing_tables:
        op.create_table(
            "collection_receipt",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("income_event_id", sa.Integer(), nullable=False),
            sa.Column("bank_operation_number", sa.String(length=80), nullable=False),
            sa.Column("collected_date", sa.Date(), nullable=False),
            sa.Column("bank_name", sa.String(length=120), nullable=True),
            sa.Column("reconciled_by", sa.String(length=120), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["income_event_id"],
                ["income_event.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("income_event_id"),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("collection_receipt")
    }

    if "ix_collection_receipt_income_event_id" not in existing_indexes:
        op.create_index(
            "ix_collection_receipt_income_event_id",
            "collection_receipt",
            ["income_event_id"],
            unique=False,
        )
    if "ix_collection_receipt_bank_operation_number" not in existing_indexes:
        op.create_index(
            "ix_collection_receipt_bank_operation_number",
            "collection_receipt",
            ["bank_operation_number"],
            unique=False,
        )
    if "ix_collection_receipt_collected_date" not in existing_indexes:
        op.create_index(
            "ix_collection_receipt_collected_date",
            "collection_receipt",
            ["collected_date"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if "collection_receipt" not in existing_tables:
        return

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("collection_receipt")
    }

    if "ix_collection_receipt_collected_date" in existing_indexes:
        op.drop_index(
            "ix_collection_receipt_collected_date", table_name="collection_receipt"
        )
    if "ix_collection_receipt_bank_operation_number" in existing_indexes:
        op.drop_index(
            "ix_collection_receipt_bank_operation_number",
            table_name="collection_receipt",
        )
    if "ix_collection_receipt_income_event_id" in existing_indexes:
        op.drop_index(
            "ix_collection_receipt_income_event_id", table_name="collection_receipt"
        )

    op.drop_table("collection_receipt")
