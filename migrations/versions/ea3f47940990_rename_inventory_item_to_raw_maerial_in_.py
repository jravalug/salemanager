"""Rename inventory_item to raw_maerial in ProductDetail model

Revision ID: ea3f47940990
Revises: 6eaf5b68ac66
Create Date: 2025-03-03 21:35:12.189556

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "ea3f47940990"
down_revision = "6eaf5b68ac66"
branch_labels = None
depends_on = None


def upgrade():
    # Agregar el nuevo campo `raw_material_id`
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.add_column(sa.Column("raw_material_id", sa.Integer(), nullable=True))

    # Copiar los datos del campo antiguo (`inventory_item_id`) al nuevo (`raw_material_id`)
    connection = op.get_bind()
    connection.execute(
        text("UPDATE product_detail SET raw_material_id = inventory_item_id")
    )

    # # Eliminar la restricción de clave foránea existente
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.drop_constraint("fk_product_detail_inventory_item", type_="foreignkey")

    # # Crear una nueva restricción de clave foránea para `raw_material_id`
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_product_detail_raw_material_id",
            "inventory_item",
            ["raw_material_id"],
            ["id"],
        )

    # # Eliminar el campo antiguo (`inventory_item_id`)
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.drop_column("inventory_item_id")


def downgrade():
    # Agregar el campo antiguo (`inventory_item_id`)
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.add_column(sa.Column("inventory_item_id", sa.Integer(), nullable=True))

    # Copiar los datos del campo nuevo (`raw_material_id`) al antiguo (`inventory_item_id`)
    connection = op.get_bind()
    connection.execute(
        text("UPDATE product_detail SET inventory_item_id = raw_material_id")
    )

    # Eliminar la restricción de clave foránea existente
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_product_detail_raw_material_id", type_="foreignkey"
        )

    # Crear una nueva restricción de clave foránea para `inventory_item_id`
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_product_detail_inventory_item",
            "inventory_item",
            ["inventory_item_id"],
            ["id"],
        )

    # Eliminar el campo nuevo (`raw_material_id`)
    with op.batch_alter_table("product_detail", schema=None) as batch_op:
        batch_op.drop_column("raw_material_id")
