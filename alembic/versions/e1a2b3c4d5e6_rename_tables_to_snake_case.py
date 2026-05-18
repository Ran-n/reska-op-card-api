"""rename compound table names to snake_case

Revision ID: e1a2b3c4d5e6
Revises: f3a9b2c1d4e5
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "f3a9b2c1d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RENAMES = [
    ("settype", "set_type"),
    ("cardtype", "card_type"),
    ("cardtribe", "card_tribe"),
    ("cardattribute", "card_attribute"),
    ("cardcolor", "card_color"),
    ("cardrarity", "card_rarity"),
    ("cardblock", "card_block"),
    ("cardformat", "card_format"),
    ("cardkeywords", "card_keywords"),
    ("cardreswords", "card_reswords"),
]


def _table_exists(conn: sa.engine.Connection, name: str) -> bool:
    return sa.inspect(conn).has_table(name)


def upgrade() -> None:
    conn = op.get_bind()
    for old, new in _RENAMES:
        if _table_exists(conn, old):
            op.rename_table(old, new)


def downgrade() -> None:
    for old, new in reversed(_RENAMES):
        op.rename_table(new, old)
