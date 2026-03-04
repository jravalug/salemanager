"""add app_setting for global threshold

Revision ID: e1f3a7b9c2d4
Revises: c9b2d5e4a1f0
Create Date: 2026-03-04 12:30:00.000000

"""

import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1f3a7b9c2d4"
down_revision = "c9b2d5e4a1f0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())

    if "app_setting" not in existing_tables:
        op.create_table(
            "app_setting",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("key", sa.String(length=100), nullable=False),
            sa.Column("value", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key", name="uq_app_setting_key"),
        )
        op.create_index("ix_app_setting_key", "app_setting", ["key"], unique=True)

    threshold = os.environ.get("ACCOUNTING_FISCAL_THRESHOLD", "500000")
    conn = op.get_bind()
    row = conn.execute(
        sa.text("SELECT id FROM app_setting WHERE key = :key LIMIT 1"),
        {"key": "accounting_fiscal_threshold"},
    ).fetchone()

    if row is None:
        conn.execute(
            sa.text(
                """
                INSERT INTO app_setting (key, value, description)
                VALUES (:key, :value, :description)
                """
            ),
            {
                "key": "accounting_fiscal_threshold",
                "value": str(threshold),
                "description": "Umbral anual para transición de régimen fiscal a financiera",
            },
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "app_setting" not in existing_tables:
        return

    try:
        op.drop_index("ix_app_setting_key", table_name="app_setting")
    except Exception:
        pass

    op.drop_table("app_setting")
