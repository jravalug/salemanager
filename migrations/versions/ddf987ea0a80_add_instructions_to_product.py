"""Add instructions to Product

Revision ID: ddf987ea0a80
Revises: 7ad4eb6e5f5f
Create Date: 2025-02-18 02:11:44.960304

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ddf987ea0a80"
down_revision = "7ad4eb6e5f5f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instructions", sa.Text(), nullable=True))

    with op.batch_alter_table("product_inventory_item", schema=None) as batch_op:
        batch_op.drop_column("instructions")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("product_inventory_item", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instructions", sa.TEXT(), nullable=True))

    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.drop_column("instructions")

    # ### end Alembic commands ###
