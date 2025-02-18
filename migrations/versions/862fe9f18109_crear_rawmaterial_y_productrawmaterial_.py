"""Crear RawMaterial y ProductRawMaterial y actualizar Product

Revision ID: 862fe9f18109
Revises: 7aa960eec286
Create Date: 2025-02-17 20:34:26.978248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '862fe9f18109'
down_revision = '7aa960eec286'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('raw_material',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=False),
    sa.Column('stock', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('product_raw_material',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('raw_material_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.ForeignKeyConstraint(['raw_material_id'], ['raw_material.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('product_raw_material')
    op.drop_table('raw_material')
    # ### end Alembic commands ###
