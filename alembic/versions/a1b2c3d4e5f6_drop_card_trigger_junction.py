"""drop card_trigger junction table; redundant with card.trigger_fk

Revision ID: a1b2c3d4e5f6
Revises: b1c2d3e4f5a6
Create Date: 2026-05-15
"""

from collections.abc import Sequence  # noqa: I001

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("card_trigger")


def downgrade() -> None:
    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_ts", sa.DateTime(), nullable=True),
        sa.Column("updated_ts", sa.DateTime(), nullable=True),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger_fk", sa.Integer(), sa.ForeignKey("trigger.id"), nullable=False),
    )
