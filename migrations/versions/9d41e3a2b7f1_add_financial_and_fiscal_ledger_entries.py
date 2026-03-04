"""add financial and fiscal ledger entries

Revision ID: 9d41e3a2b7f1
Revises: 705e33447302
Create Date: 2026-03-04 13:40:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d41e3a2b7f1"
down_revision = "705e33447302"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "financial_ledger_entry" not in existing_tables:
        op.create_table(
            "financial_ledger_entry",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("income_event_id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("recognition_date", sa.Date(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("regime", sa.String(length=20), nullable=False),
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
            sa.ForeignKeyConstraint(
                ["income_event_id"], ["income_event.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["business_id"], ["business.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "income_event_id", name="uq_financial_ledger_income_event"
            ),
            sa.CheckConstraint(
                "amount >= 0",
                name="financial_ledger_entry_amount_non_negative",
            ),
            sa.CheckConstraint(
                "regime IN ('fiscal', 'financiera')",
                name="financial_ledger_entry_regime_allowed_values",
            ),
        )
        op.create_index(
            "ix_financial_ledger_entry_income_event_id",
            "financial_ledger_entry",
            ["income_event_id"],
            unique=True,
        )
        op.create_index(
            "ix_financial_ledger_entry_business_id",
            "financial_ledger_entry",
            ["business_id"],
            unique=False,
        )
        op.create_index(
            "ix_financial_ledger_entry_recognition_date",
            "financial_ledger_entry",
            ["recognition_date"],
            unique=False,
        )
        op.create_index(
            "ix_financial_ledger_entry_regime",
            "financial_ledger_entry",
            ["regime"],
            unique=False,
        )
        op.create_index(
            "ix_financial_ledger_entry_source_ref",
            "financial_ledger_entry",
            ["source_ref"],
            unique=False,
        )

    if "fiscal_income_entry" not in existing_tables:
        op.create_table(
            "fiscal_income_entry",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("income_event_id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("recognition_date", sa.Date(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("regime", sa.String(length=20), nullable=False),
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
            sa.ForeignKeyConstraint(
                ["income_event_id"], ["income_event.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["business_id"], ["business.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "income_event_id", name="uq_fiscal_income_income_event"
            ),
            sa.CheckConstraint(
                "amount >= 0",
                name="fiscal_income_entry_amount_non_negative",
            ),
            sa.CheckConstraint(
                "regime IN ('fiscal', 'financiera')",
                name="fiscal_income_entry_regime_allowed_values",
            ),
        )
        op.create_index(
            "ix_fiscal_income_entry_income_event_id",
            "fiscal_income_entry",
            ["income_event_id"],
            unique=True,
        )
        op.create_index(
            "ix_fiscal_income_entry_business_id",
            "fiscal_income_entry",
            ["business_id"],
            unique=False,
        )
        op.create_index(
            "ix_fiscal_income_entry_recognition_date",
            "fiscal_income_entry",
            ["recognition_date"],
            unique=False,
        )
        op.create_index(
            "ix_fiscal_income_entry_regime",
            "fiscal_income_entry",
            ["regime"],
            unique=False,
        )
        op.create_index(
            "ix_fiscal_income_entry_source_ref",
            "fiscal_income_entry",
            ["source_ref"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "fiscal_income_entry" in existing_tables:
        for index_name in (
            "ix_fiscal_income_entry_source_ref",
            "ix_fiscal_income_entry_regime",
            "ix_fiscal_income_entry_recognition_date",
            "ix_fiscal_income_entry_business_id",
            "ix_fiscal_income_entry_income_event_id",
        ):
            try:
                op.drop_index(index_name, table_name="fiscal_income_entry")
            except Exception:
                pass
        op.drop_table("fiscal_income_entry")

    if "financial_ledger_entry" in existing_tables:
        for index_name in (
            "ix_financial_ledger_entry_source_ref",
            "ix_financial_ledger_entry_regime",
            "ix_financial_ledger_entry_recognition_date",
            "ix_financial_ledger_entry_business_id",
            "ix_financial_ledger_entry_income_event_id",
        ):
            try:
                op.drop_index(index_name, table_name="financial_ledger_entry")
            except Exception:
                pass
        op.drop_table("financial_ledger_entry")
