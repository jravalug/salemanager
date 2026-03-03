"""extend client and business contact/address fields

Revision ID: c9b2d5e4a1f0
Revises: a3c1f4d9b2e7
Create Date: 2026-03-03 02:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9b2d5e4a1f0"
down_revision = "a3c1f4d9b2e7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_client_columns = {
        column["name"] for column in inspector.get_columns("clientes")
    }

    client_columns_to_add = [
        ("identity_number", sa.String(length=30)),
        ("nit", sa.String(length=30)),
        ("legal_street", sa.String(length=120)),
        ("legal_number", sa.String(length=30)),
        ("legal_between_streets", sa.String(length=120)),
        ("legal_apartment", sa.String(length=50)),
        ("legal_district", sa.String(length=100)),
        ("legal_municipality", sa.String(length=100)),
        ("legal_province", sa.String(length=100)),
        ("legal_postal_code", sa.String(length=20)),
        ("phone_numbers", sa.JSON()),
        ("primary_phone_number", sa.String(length=30)),
        ("email_addresses", sa.JSON()),
        ("primary_email_address", sa.String(length=120)),
        ("fiscal_account_number", sa.String(length=50)),
        ("fiscal_account_card_number", sa.String(length=30)),
    ]

    for column_name, column_type in client_columns_to_add:
        if column_name not in existing_client_columns:
            op.add_column(
                "clientes", sa.Column(column_name, column_type, nullable=True)
            )

    if "tax_id" in existing_client_columns:
        op.execute(
            "UPDATE clientes SET nit = tax_id WHERE nit IS NULL AND tax_id IS NOT NULL"
        )

    existing_business_columns = {
        column["name"] for column in inspector.get_columns("business")
    }

    business_columns_to_add = [
        ("fiscal_street", sa.String(length=120)),
        ("fiscal_number", sa.String(length=30)),
        ("fiscal_between_streets", sa.String(length=120)),
        ("fiscal_apartment", sa.String(length=50)),
        ("fiscal_district", sa.String(length=100)),
        ("fiscal_municipality", sa.String(length=100)),
        ("fiscal_province", sa.String(length=100)),
        ("fiscal_postal_code", sa.String(length=20)),
    ]

    for column_name, column_type in business_columns_to_add:
        if column_name not in existing_business_columns:
            op.add_column(
                "business", sa.Column(column_name, column_type, nullable=True)
            )


def downgrade():
    pass
