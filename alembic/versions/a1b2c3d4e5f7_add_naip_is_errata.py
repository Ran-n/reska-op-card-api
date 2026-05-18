"""add naip.is_errata column

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f7"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = {r[1] for r in conn.execute(sa.text("PRAGMA table_info(naip)"))}
    if "is_default" not in existing:
        conn.execute(sa.text("ALTER TABLE naip ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0"))
    conn.execute(sa.text("ALTER TABLE naip ADD COLUMN is_errata INTEGER NOT NULL DEFAULT 0"))


def downgrade() -> None:
    # SQLite cannot DROP COLUMN before 3.35; rebuild the table without it
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text("ALTER TABLE naip RENAME TO naip_old"))
    conn.execute(
        sa.text(
            """CREATE TABLE naip (
            id          INTEGER PRIMARY KEY,
            created_ts  TEXT,
            updated_ts  TEXT,
            card_fk     INTEGER NOT NULL REFERENCES card(id),
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            artist_fk   INTEGER REFERENCES artist(id),
            rarity_fk   INTEGER REFERENCES rarity(id),
            name_fk     INTEGER REFERENCES name(id),
            image_fk    INTEGER REFERENCES image(id),
            effect_fk   INTEGER REFERENCES effect(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            is_default  INTEGER NOT NULL DEFAULT 0
        )"""
        )
    )
    conn.execute(
        sa.text(
            "INSERT INTO naip (id, created_ts, updated_ts, card_fk, set_fk, artist_fk, "
            "rarity_fk, name_fk, image_fk, effect_fk, trigger_fk, is_default) "
            "SELECT id, created_ts, updated_ts, card_fk, set_fk, artist_fk, "
            "rarity_fk, name_fk, image_fk, effect_fk, trigger_fk, is_default FROM naip_old"
        )
    )
    conn.execute(sa.text("DROP TABLE naip_old"))

    conn.execute(sa.text("CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
