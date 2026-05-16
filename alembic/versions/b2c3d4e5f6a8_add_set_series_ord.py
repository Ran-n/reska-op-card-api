"""add set.series and set.ord columns

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text('ALTER TABLE "set" RENAME TO set_old'))
    conn.execute(
        sa.text(
            """CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  TEXT,
            updated_ts  TEXT,
            type_fk     INTEGER REFERENCES set_type(id),
            code        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            series      TEXT,
            ord         INTEGER,
            desc        TEXT,
            release_ts  TEXT
        )"""
        )
    )
    conn.execute(
        sa.text(
            'INSERT INTO "set" (id, created_ts, updated_ts, type_fk, code, name, desc, release_ts) '
            "SELECT id, created_ts, updated_ts, type_fk, code, name, desc, release_ts FROM set_old"
        )
    )
    conn.execute(sa.text("DROP TABLE set_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text('ALTER TABLE "set" RENAME TO set_old'))
    conn.execute(
        sa.text(
            """CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  TEXT,
            updated_ts  TEXT,
            type_fk     INTEGER REFERENCES set_type(id),
            code        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            desc        TEXT,
            release_ts  TEXT
        )"""
        )
    )
    conn.execute(
        sa.text(
            'INSERT INTO "set" (id, created_ts, updated_ts, type_fk, code, name, desc, release_ts) '
            "SELECT id, created_ts, updated_ts, type_fk, code, name, desc, release_ts FROM set_old"
        )
    )
    conn.execute(sa.text("DROP TABLE set_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
