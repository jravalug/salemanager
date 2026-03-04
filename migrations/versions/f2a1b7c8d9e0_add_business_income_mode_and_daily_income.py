"""add business income mode/activity and daily income table

Revision ID: f2a1b7c8d9e0
Revises: d1f7c4a8b9e2
Create Date: 2026-03-03 16:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2a1b7c8d9e0"
down_revision = "d1f7c4a8b9e2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect_name = bind.dialect.name

    existing_business_columns = {
        column["name"] for column in inspector.get_columns("business")
    }

    business_columns_to_add = [
        ("business_activity", sa.String(length=120), True),
        ("income_entry_mode", sa.String(length=30), False),
        ("default_income_activity", sa.String(length=20), False),
    ]

    for column_name, column_type, nullable in business_columns_to_add:
        if column_name not in existing_business_columns:
            server_default = None
            if column_name == "income_entry_mode":
                server_default = "daily_income"
            if column_name == "default_income_activity":
                server_default = "sale"

            op.add_column(
                "business",
                sa.Column(
                    column_name,
                    column_type,
                    nullable=nullable,
                    server_default=server_default,
                ),
            )

    op.execute(
        "UPDATE business SET income_entry_mode = 'daily_income' "
        "WHERE income_entry_mode IS NULL OR TRIM(income_entry_mode) = ''"
    )
    op.execute(
        "UPDATE business SET default_income_activity = 'sale' "
        "WHERE default_income_activity IS NULL OR TRIM(default_income_activity) = ''"
    )

    constraint_names = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("business")
        if constraint.get("name")
    }

    if dialect_name != "sqlite":
        if "business_income_entry_mode_allowed_values" not in constraint_names:
            op.create_check_constraint(
                "business_income_entry_mode_allowed_values",
                "business",
                "income_entry_mode IN ('daily_income', 'detailed_sales')",
            )

        if "business_default_income_activity_allowed_values" not in constraint_names:
            op.create_check_constraint(
                "business_default_income_activity_allowed_values",
                "business",
                "default_income_activity IN ('sale', 'service')",
            )

    existing_tables = set(inspector.get_table_names())
    if "daily_income" not in existing_tables:
        op.create_table(
            "daily_income",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("business_id", sa.Integer(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column(
                "income_type",
                sa.String(length=20),
                nullable=False,
                server_default="income_obtained",
            ),
            sa.Column(
                "activity", sa.String(length=20), nullable=False, server_default="sale"
            ),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column(
                "cash_location",
                sa.String(length=20),
                nullable=False,
                server_default="cash_register",
            ),
            sa.Column(
                "source", sa.String(length=20), nullable=False, server_default="manual"
            ),
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
                ["business_id"], ["business.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("amount >= 0", name="daily_income_amount_non_negative"),
            sa.CheckConstraint(
                "income_type IN ('income_obtained', 'non_taxable')",
                name="daily_income_type_allowed_values",
            ),
            sa.CheckConstraint(
                "activity IN ('sale', 'service')",
                name="daily_income_activity_allowed_values",
            ),
            sa.CheckConstraint(
                "cash_location IN ('cash_register', 'bank_cash')",
                name="daily_income_cash_location_allowed_values",
            ),
            sa.CheckConstraint(
                "source IN ('manual', 'sales_summary')",
                name="daily_income_source_allowed_values",
            ),
            sa.UniqueConstraint(
                "business_id",
                "date",
                "income_type",
                "activity",
                "cash_location",
                "source",
                name="uq_daily_income_summary_bucket",
            ),
        )
        op.create_index(
            "ix_daily_income_business_id", "daily_income", ["business_id"], unique=False
        )
        op.create_index("ix_daily_income_date", "daily_income", ["date"], unique=False)
        op.create_index(
            "ix_daily_income_income_type", "daily_income", ["income_type"], unique=False
        )
        op.create_index(
            "ix_daily_income_cash_location",
            "daily_income",
            ["cash_location"],
            unique=False,
        )
        op.create_index(
            "ix_daily_income_source", "daily_income", ["source"], unique=False
        )


def downgrade():
    pass
