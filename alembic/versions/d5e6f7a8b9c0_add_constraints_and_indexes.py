"""add constraints and indexes

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b9
Create Date: 2026-05-17
"""

from collections.abc import Sequence  # noqa: I001

import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # ── Card: unique (set_fk, number) ─────────────────────────────────────────
    # SQLite cannot add a unique constraint to an existing table directly;
    # rebuild the table with the constraint baked in.
    conn.execute(sa.text("ALTER TABLE card RENAME TO card_old"))
    conn.execute(
        sa.text(
            """CREATE TABLE card (
            id           INTEGER PRIMARY KEY,
            created_ts   TEXT,
            updated_ts   TEXT,
            set_fk       INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk  INTEGER NOT NULL REFERENCES card_type(id),
            name_fk      INTEGER NOT NULL REFERENCES name(id),
            effect_fk    INTEGER REFERENCES effect(id),
            trigger_fk   INTEGER REFERENCES trigger(id),
            number       INTEGER NOT NULL,
            power        INTEGER,
            life         INTEGER,
            counter      INTEGER,
            cost         INTEGER,
            UNIQUE (set_fk, number)
        )"""
        )
    )
    conn.execute(
        sa.text(
            "INSERT INTO card (id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, "
            "effect_fk, trigger_fk, number, power, life, counter, cost) "
            "SELECT id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, "
            "effect_fk, trigger_fk, number, power, life, counter, cost FROM card_old"
        )
    )
    conn.execute(sa.text("DROP TABLE card_old"))

    # ── Card: indexes on high-frequency FK columns ────────────────────────────
    conn.execute(sa.text("CREATE INDEX ix_card_set_fk ON card (set_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_cardtype_fk ON card (cardtype_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_name_fk ON card (name_fk)"))

    # ── Naip: unique (card_fk, set_fk, artist_fk, rarity_fk) ─────────────────
    # NULL values in SQLite are not considered equal in UNIQUE constraints, so
    # two rows with the same card_fk/set_fk and NULL artist_fk/rarity_fk would
    # not violate a simple UNIQUE. A partial index (WHERE artist_fk IS NOT NULL
    # AND rarity_fk IS NOT NULL) covers the common case; the is_default partial
    # index already handles the default-print constraint.
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print "
            "ON naip (card_fk, set_fk, artist_fk, rarity_fk) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
        )
    )

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_unique_print"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_name_fk"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_cardtype_fk"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_set_fk"))

    # Rebuild card without the UNIQUE(set_fk, number) constraint
    conn.execute(sa.text("ALTER TABLE card RENAME TO card_old"))
    conn.execute(
        sa.text(
            """CREATE TABLE card (
            id           INTEGER PRIMARY KEY,
            created_ts   TEXT,
            updated_ts   TEXT,
            set_fk       INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk  INTEGER NOT NULL REFERENCES card_type(id),
            name_fk      INTEGER NOT NULL REFERENCES name(id),
            effect_fk    INTEGER REFERENCES effect(id),
            trigger_fk   INTEGER REFERENCES trigger(id),
            number       INTEGER NOT NULL,
            power        INTEGER,
            life         INTEGER,
            counter      INTEGER,
            cost         INTEGER
        )"""
        )
    )
    conn.execute(
        sa.text(
            "INSERT INTO card (id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, "
            "effect_fk, trigger_fk, number, power, life, counter, cost) "
            "SELECT id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, "
            "effect_fk, trigger_fk, number, power, life, counter, cost FROM card_old"
        )
    )
    conn.execute(sa.text("DROP TABLE card_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
