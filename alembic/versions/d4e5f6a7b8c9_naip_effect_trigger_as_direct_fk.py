"""naip stores effect_fk and trigger_fk as direct FKs, not junction tables

Drops naip_effect junction.
Adds naip.effect_fk → effect.id
Adds naip.trigger_fk → trigger.id

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # Read naip_effect junction before dropping it
    naip_effect_rows = conn.execute(
        sa.text("SELECT naip_fk, effect_fk FROM naip_effect")
    ).fetchall()

    op.drop_table("naip_effect")

    # Add effect_fk and trigger_fk directly on naip
    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_effect", "effect", ["effect_fk"], ["id"])
        batch_op.create_foreign_key("fk_naip_trigger", "trigger", ["trigger_fk"], ["id"])

    # Restore effect_fk from old junction rows
    for naip_id, effect_fk in naip_effect_rows:
        conn.execute(
            sa.text("UPDATE naip SET effect_fk = :e WHERE id = :n"),
            {"e": effect_fk, "n": naip_id},
        )


def downgrade() -> None:
    conn = op.get_bind()

    naip_rows = conn.execute(
        sa.text("SELECT id, effect_fk FROM naip WHERE effect_fk IS NOT NULL")
    ).fetchall()

    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_effect", type_="foreignkey")
        batch_op.drop_constraint("fk_naip_trigger", type_="foreignkey")
        batch_op.drop_column("effect_fk")
        batch_op.drop_column("trigger_fk")

    op.create_table(
        "naip_effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("naip_fk", sa.Integer(), sa.ForeignKey("naip.id"), nullable=False),
        sa.Column("effect_fk", sa.Integer(), sa.ForeignKey("effect.id"), nullable=False),
    )

    for naip_id, effect_fk in naip_rows:
        conn.execute(
            sa.text("INSERT INTO naip_effect (naip_fk, effect_fk) VALUES (:n, :e)"),
            {"n": naip_id, "e": effect_fk},
        )
