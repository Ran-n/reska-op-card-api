"""add UNIQUE constraint on set.code; add partial unique index on naip(card_fk) where is_default

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # Add UNIQUE on set.code via table rebuild (SQLite cannot ADD CONSTRAINT)
    conn.execute(sa.text('ALTER TABLE "set" RENAME TO "set_old"'))
    conn.execute(sa.text(
        """CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_ts  DATETIME DEFAULT CURRENT_TIMESTAMP,
            type_fk     INTEGER REFERENCES "set_type"(id),
            code        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            desc        TEXT,
            release_ts  DATE
        )"""
    ))
    conn.execute(sa.text(
        'INSERT INTO "set" (id, created_ts, updated_ts, type_fk, code, name, desc, release_ts) '
        'SELECT id, created_ts, updated_ts, type_fk, code, name, desc, release_ts FROM "set_old"'
    ))
    conn.execute(sa.text('DROP TABLE "set_old"'))

    # Deduplicate: keep only the lowest-id naip with is_default=1 per card_fk
    conn.execute(sa.text(
        "UPDATE naip SET is_default = 0 "
        "WHERE is_default = 1 AND id NOT IN ("
        "  SELECT MIN(id) FROM naip WHERE is_default = 1 GROUP BY card_fk"
        ")"
    ))

    # Partial unique index: at most one is_default=1 naip per card_fk
    conn.execute(sa.text(
        "CREATE UNIQUE INDEX ix_naip_one_default_per_card "
        "ON naip (card_fk) WHERE is_default = 1"
    ))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_one_default_per_card"))

    # Rebuild set without UNIQUE on code
    conn.execute(sa.text('ALTER TABLE "set" RENAME TO "set_old"'))
    conn.execute(sa.text(
        """CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_ts  DATETIME DEFAULT CURRENT_TIMESTAMP,
            type_fk     INTEGER REFERENCES "set_type"(id),
            code        TEXT NOT NULL,
            name        TEXT NOT NULL,
            desc        TEXT,
            release_ts  DATE
        )"""
    ))
    conn.execute(sa.text(
        'INSERT INTO "set" (id, created_ts, updated_ts, type_fk, code, name, desc, release_ts) '
        'SELECT id, created_ts, updated_ts, type_fk, code, name, desc, release_ts FROM "set_old"'
    ))
    conn.execute(sa.text('DROP TABLE "set_old"'))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
