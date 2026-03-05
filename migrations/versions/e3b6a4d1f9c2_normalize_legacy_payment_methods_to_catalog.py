"""normalize legacy payment methods to catalog

Revision ID: e3b6a4d1f9c2
Revises: d8a1c5b7e9f0
Create Date: 2026-03-04 22:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "e3b6a4d1f9c2"
down_revision = "d8a1c5b7e9f0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "sale" not in existing_tables:
        return

    op.execute(
        sa.text(
            """
            UPDATE sale
            SET payment_method = CASE
                WHEN lower(trim(coalesce(payment_method, ''))) IN ('cash', 'efectivo') THEN 'cash'
                WHEN lower(trim(coalesce(payment_method, ''))) IN ('transfer', 'transferencia', 'bank', 'bank_transfer', 'wire', 'transferencia_bancaria') THEN 'transfer'
                WHEN lower(trim(coalesce(payment_method, ''))) IN ('check', 'cheque', 'chek') THEN 'check'
                WHEN lower(trim(coalesce(payment_method, ''))) IN ('card', 'tarjeta', 'mix', 'mixto', 'other', 'otro', '') THEN 'cash'
                ELSE 'cash'
            END
            """
        )
    )


def downgrade():
    return
