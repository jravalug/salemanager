"""Add instructions to ProductDetail

Revision ID: 7ad4eb6e5f5f
Revises: 862fe9f18109
Create Date: 2025-02-18 02:00:54.704734

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7ad4eb6e5f5f"
down_revision = "862fe9f18109"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("product_inventory_item", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instructions", sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("product_inventory_item", schema=None) as batch_op:
        batch_op.drop_column("instructions")

    # ### end Alembic commands ###
