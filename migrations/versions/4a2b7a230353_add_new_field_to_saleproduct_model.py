"""Add new field to SaleDetail model

Revision ID: 4a2b7a230353
Revises: b14889ea2ef0
Create Date: 2025-02-21 14:47:07.496796

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4a2b7a230353"
down_revision = "b14889ea2ef0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("sale_detail", schema=None) as batch_op:
        batch_op.add_column(sa.Column("unit_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("total_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("discount", sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("sale_detail", schema=None) as batch_op:
        batch_op.drop_column("discount")
        batch_op.drop_column("total_price")
        batch_op.drop_column("unit_price")

    # ### end Alembic commands ###
