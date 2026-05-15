"""add created_ts and updated_ts to tables that were missing them

Tables affected:
  card, card_effect_history, card_trigger_history,
  effect, image, name, trigger

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = [
    "card",
    "card_effect_history",
    "card_trigger_history",
    "effect",
    "image",
    "name",
    "trigger",
]


def upgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        op.add_column(table, sa.Column("created_ts", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("updated_ts", sa.DateTime(), nullable=True))
        conn.execute(sa.text(f"UPDATE \"{table}\" SET created_ts = CURRENT_TIMESTAMP, updated_ts = CURRENT_TIMESTAMP"))


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "updated_ts")
        op.drop_column(table, "created_ts")
