"""rename clientes table to clients

Revision ID: d1f7c4a8b9e2
Revises: c9b2d5e4a1f0
Create Date: 2026-03-03 02:18:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1f7c4a8b9e2"
down_revision = "c9b2d5e4a1f0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "clientes" in table_names and "clients" not in table_names:
        op.rename_table("clientes", "clients")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "clients" in table_names and "clientes" not in table_names:
        op.rename_table("clients", "clientes")
