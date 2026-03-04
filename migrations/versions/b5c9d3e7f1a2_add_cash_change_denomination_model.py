"""add cash change denomination model

Revision ID: b5c9d3e7f1a2
Revises: e8f1a2b3c4d5
Create Date: 2026-03-04 16:55:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5c9d3e7f1a2"
down_revision = "e8f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "cash_change_denomination" not in existing_tables:
        op.create_table(
            "cash_change_denomination",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("movement_id", sa.Integer(), nullable=False),
            sa.Column("denomination_value", sa.Float(), nullable=False),
            sa.Column("unit_count", sa.Integer(), nullable=False),
            sa.Column("total_amount", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["movement_id"],
                ["cash_subaccount_movement.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(
                "denomination_value > 0",
                name="cash_change_denomination_value_positive",
            ),
            sa.CheckConstraint(
                "unit_count > 0",
                name="cash_change_denomination_unit_count_positive",
            ),
            sa.CheckConstraint(
                "total_amount > 0",
                name="cash_change_denomination_total_positive",
            ),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("cash_change_denomination")
    }
    if "ix_cash_change_denomination_movement_id" not in existing_indexes:
        op.create_index(
            "ix_cash_change_denomination_movement_id",
            "cash_change_denomination",
            ["movement_id"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "cash_change_denomination" in existing_tables:
        existing_indexes = {
            index["name"] for index in inspector.get_indexes("cash_change_denomination")
        }
        if "ix_cash_change_denomination_movement_id" in existing_indexes:
            op.drop_index(
                "ix_cash_change_denomination_movement_id",
                table_name="cash_change_denomination",
            )
        op.drop_table("cash_change_denomination")
