"""normalize cheque to check payment method

Revision ID: d8a1c5b7e9f0
Revises: c7d9e2f4a1b3
Create Date: 2026-03-04 20:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8a1c5b7e9f0"
down_revision = "c7d9e2f4a1b3"
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
            SET payment_method = 'check'
            WHERE lower(payment_method) = 'cheque'
            """
        )
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "sale" not in existing_tables:
        return

    op.execute(
        sa.text(
            """
            UPDATE sale
            SET payment_method = 'cheque'
            WHERE lower(payment_method) = 'check'
            """
        )
    )
