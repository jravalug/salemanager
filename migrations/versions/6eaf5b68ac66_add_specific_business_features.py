"""Add specific business features

Revision ID: 6eaf5b68ac66
Revises: 8c0d4d5c7f12
Create Date: 2025-03-02 17:43:42.360855

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6eaf5b68ac66"
down_revision = "8c0d4d5c7f12"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_general", sa.Boolean(), nullable=True))
        batch_op.add_column(
            sa.Column("parent_business_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_business_parent_business_id", "business", ["parent_business_id"], ["id"]
        )

    with op.batch_alter_table("inventory", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("specific_business_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_inventory_specific_business_id",
            "business",
            ["specific_business_id"],
            ["id"],
        )

    with op.batch_alter_table("invoice", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("specific_business_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_invoice_specific_business_id",
            "business",
            ["specific_business_id"],
            ["id"],
        )

    with op.batch_alter_table("sale", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("specific_business_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_sale_specific_business_id",
            "business",
            ["specific_business_id"],
            ["id"],
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("sale", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("specific_business_id")

    with op.batch_alter_table("invoice", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("specific_business_id")

    with op.batch_alter_table("inventory", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("specific_business_id")

    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("parent_business_id")
        batch_op.drop_column("is_general")

    # ### end Alembic commands ###
