"""backfill created_ts/updated_ts rows that are date-only (YYYY-MM-DD) to full datetime

Appends ' 00:00:00' to any value that is exactly 10 characters long, preserving the
original date. Applies to every table that has timestamp columns.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = [
    "set_type",
    "card_type",
    "artist",
    "rarity",
    "tribe",
    "attribute",
    "color",
    "block",
    "format",
    "keywords",
    "reswords",
    "set",
    "name",
    "image",
    "effect",
    "trigger",
    "card",
    "naip",
    "card_effect_history",
    "card_trigger_history",
    "card_tribe",
    "card_attribute",
    "card_color",
    "card_rarity",
    "card_block",
    "card_format",
    "card_keywords",
    "card_reswords",
]

_FIX = (
    "UPDATE \"{t}\" SET "
    "created_ts = created_ts || ' 00:00:00' WHERE length(created_ts) = 10, "
    "updated_ts = updated_ts || ' 00:00:00' WHERE length(updated_ts) = 10"
)


def upgrade() -> None:
    conn = op.get_bind()
    for t in _TABLES:
        conn.execute(sa.text(
            f"UPDATE \"{t}\" SET created_ts = created_ts || ' 00:00:00' WHERE length(created_ts) = 10"
        ))
        conn.execute(sa.text(
            f"UPDATE \"{t}\" SET updated_ts = updated_ts || ' 00:00:00' WHERE length(updated_ts) = 10"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    for t in _TABLES:
        conn.execute(sa.text(
            f"UPDATE \"{t}\" SET created_ts = substr(created_ts, 1, 10) WHERE length(created_ts) = 19"
        ))
        conn.execute(sa.text(
            f"UPDATE \"{t}\" SET updated_ts = substr(updated_ts, 1, 10) WHERE length(updated_ts) = 19"
        ))
