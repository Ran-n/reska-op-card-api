#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/02 00:00:00.000000
Revised: 2026/06/02 00:00:00.000000

replace set.series (str) and set.ord (int) with set.parent_fk (self-referential FK)

Revision ID: 0004_set_parent_fk
Revises: 0003_print_variant
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_set_parent_fk"
down_revision: str | Sequence[str] | None = "0003_print_variant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"
_TS_EXPR = "strftime('%Y-%m-%d %H:%M:%f', 'now')"


def _trigger(table: str) -> str:
    q = f'"{table}"'
    return (
        f"CREATE TRIGGER trg_{table}_update AFTER UPDATE ON {q} "
        f"WHEN NEW.updated_ts IS OLD.updated_ts "
        f"BEGIN UPDATE {q} SET updated_ts = {_TS_EXPR} WHERE id = NEW.id; END"
    )


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_set_update"))
    conn.execute(sa.text('ALTER TABLE "set" RENAME TO set_old'))

    conn.execute(
        sa.text(f"""
        CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            type_fk     INTEGER REFERENCES set_type(id),
            language_fk INTEGER NOT NULL REFERENCES language(id),
            parent_fk   INTEGER REFERENCES "set"(id),
            code        TEXT NOT NULL,
            name        TEXT NOT NULL,
            "desc"      TEXT,
            release_ts  TEXT,
            UNIQUE (code, language_fk)
        )
    """)
    )

    conn.execute(
        sa.text(
            'INSERT INTO "set" '
            '(id, created_ts, updated_ts, type_fk, language_fk, parent_fk, code, name, "desc", release_ts) '
            'SELECT id, created_ts, updated_ts, type_fk, language_fk, NULL, code, name, "desc", release_ts '
            "FROM set_old"
        )
    )

    conn.execute(sa.text(_trigger("set")))
    conn.execute(sa.text('CREATE INDEX ix_set_parent_fk ON "set" (parent_fk)'))
    conn.execute(sa.text("DROP TABLE set_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_set_update"))
    conn.execute(sa.text('ALTER TABLE "set" RENAME TO set_old'))

    conn.execute(
        sa.text(f"""
        CREATE TABLE "set" (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            type_fk     INTEGER REFERENCES set_type(id),
            language_fk INTEGER NOT NULL REFERENCES language(id),
            code        TEXT NOT NULL,
            name        TEXT NOT NULL,
            series      TEXT,
            ord         INTEGER,
            "desc"      TEXT,
            release_ts  TEXT,
            UNIQUE (code, language_fk)
        )
    """)
    )

    conn.execute(
        sa.text(
            'INSERT INTO "set" '
            '(id, created_ts, updated_ts, type_fk, language_fk, code, name, series, ord, "desc", release_ts) '
            'SELECT id, created_ts, updated_ts, type_fk, language_fk, code, name, NULL, NULL, "desc", release_ts '
            "FROM set_old"
        )
    )

    conn.execute(sa.text(_trigger("set")))
    conn.execute(sa.text("DROP TABLE set_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
