"""create clientes and link business

Revision ID: a3c1f4d9b2e7
Revises: ea3f47940990
Create Date: 2026-03-03 11:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3c1f4d9b2e7"
down_revision = "ea3f47940990"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "clientes" not in inspector.get_table_names():
        op.create_table(
            "clientes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("tax_id", sa.String(length=30), nullable=True),
            sa.Column("client_type", sa.String(length=20), nullable=False),
            sa.Column("accounting_regime", sa.String(length=20), nullable=False),
            sa.Column("regime_changed_at", sa.DateTime(), nullable=True),
            sa.Column("regime_change_reason", sa.String(length=255), nullable=True),
            sa.Column("last_regime_evaluation_year", sa.Integer(), nullable=True),
            sa.Column("last_regime_evaluated_at", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "client_type IN ('tcp', 'mipyme')", name="client_type_allowed_values"
            ),
            sa.CheckConstraint(
                "accounting_regime IN ('fiscal', 'financiera')",
                name="client_accounting_regime_allowed_values",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("tax_id"),
        )

    op.execute("PRAGMA foreign_keys=OFF")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_business")
    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.add_column(sa.Column("client_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_business_client_id", ["client_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_business_client_id", "clientes", ["client_id"], ["id"]
        )
    op.execute("PRAGMA foreign_keys=ON")


def downgrade():
    op.execute("PRAGMA foreign_keys=OFF")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_business")
    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.drop_constraint("fk_business_client_id", type_="foreignkey")
        batch_op.drop_index("ix_business_client_id")
        batch_op.drop_column("client_id")
    op.execute("PRAGMA foreign_keys=ON")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "clientes" in inspector.get_table_names():
        op.drop_table("clientes")
