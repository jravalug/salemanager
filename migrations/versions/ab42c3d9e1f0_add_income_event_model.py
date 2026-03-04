"""add income_event model

Revision ID: ab42c3d9e1f0
Revises: f2a1b7c8d9e0
Create Date: 2026-03-04 03:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ab42c3d9e1f0"
down_revision = "f2a1b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "income_event" in existing_tables:
        return

    op.create_table(
        "income_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("origin_type", sa.String(length=20), nullable=False),
        sa.Column("payment_channel", sa.String(length=20), nullable=False),
        sa.Column("collection_status", sa.String(length=20), nullable=False),
        sa.Column("collected_date", sa.Date(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("source_ref", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount >= 0", name="income_event_amount_non_negative"),
        sa.CheckConstraint(
            "origin_type IN ('sale', 'service', 'manual')",
            name="income_event_origin_type_allowed_values",
        ),
        sa.CheckConstraint(
            "payment_channel IN ('cash', 'bank_transfer', 'card')",
            name="income_event_payment_channel_allowed_values",
        ),
        sa.CheckConstraint(
            "collection_status IN ('immediate', 'pending', 'collected')",
            name="income_event_collection_status_allowed_values",
        ),
    )

    op.create_index(
        "ix_income_event_business_id",
        "income_event",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_event_date",
        "income_event",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_origin_type",
        "income_event",
        ["origin_type"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_payment_channel",
        "income_event",
        ["payment_channel"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_collection_status",
        "income_event",
        ["collection_status"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_collected_date",
        "income_event",
        ["collected_date"],
        unique=False,
    )
    op.create_index(
        "ix_income_event_source_ref",
        "income_event",
        ["source_ref"],
        unique=False,
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "income_event" not in existing_tables:
        return

    for index_name in (
        "ix_income_event_source_ref",
        "ix_income_event_collected_date",
        "ix_income_event_collection_status",
        "ix_income_event_payment_channel",
        "ix_income_event_origin_type",
        "ix_income_event_event_date",
        "ix_income_event_business_id",
    ):
        try:
            op.drop_index(index_name, table_name="income_event")
        except Exception:
            pass

    op.drop_table("income_event")
