"""reorder created_ts/updated_ts to immediately follow id on all affected tables

Tables where timestamps were appended at the end instead of after id:
  card, card_effect_history, card_trigger_history, effect, image, name, trigger

Also re-adds card_trigger (was dropped in e5f6a7b8c9d0) with correct column order.

SQLite cannot reorder columns in-place; each table is rebuilt via rename/create/copy/drop.

Revision ID: b1c2d3e4f5a6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rebuild(conn, table: str, create_sql: str, insert_sql: str) -> None:
    conn.execute(sa.text(f'ALTER TABLE "{table}" RENAME TO "{table}_old"'))
    conn.execute(sa.text(create_sql))
    conn.execute(sa.text(insert_sql))
    conn.execute(sa.text(f'DROP TABLE "{table}_old"'))


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    _rebuild(
        conn, "name",
        """CREATE TABLE "name" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            name        TEXT NOT NULL UNIQUE
        )""",
        'INSERT INTO "name" (id, created_ts, updated_ts, name) '
        'SELECT id, created_ts, updated_ts, name FROM "name_old"',
    )

    _rebuild(
        conn, "image",
        """CREATE TABLE "image" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            path        TEXT NOT NULL UNIQUE
        )""",
        'INSERT INTO "image" (id, created_ts, updated_ts, path) '
        'SELECT id, created_ts, updated_ts, path FROM "image_old"',
    )

    _rebuild(
        conn, "effect",
        """CREATE TABLE "effect" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            effect      TEXT NOT NULL UNIQUE
        )""",
        'INSERT INTO "effect" (id, created_ts, updated_ts, effect) '
        'SELECT id, created_ts, updated_ts, effect FROM "effect_old"',
    )

    _rebuild(
        conn, "trigger",
        """CREATE TABLE "trigger" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            trigger     TEXT NOT NULL UNIQUE
        )""",
        'INSERT INTO "trigger" (id, created_ts, updated_ts, trigger) '
        'SELECT id, created_ts, updated_ts, trigger FROM "trigger_old"',
    )

    _rebuild(
        conn, "card",
        """CREATE TABLE "card" (
            id           INTEGER PRIMARY KEY,
            created_ts   DATE,
            updated_ts   DATE,
            set_fk       INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk  INTEGER NOT NULL REFERENCES "card_type"(id),
            name_fk      INTEGER NOT NULL REFERENCES "name"(id),
            effect_fk    INTEGER REFERENCES "effect"(id),
            trigger_fk   INTEGER REFERENCES "trigger"(id),
            number       INTEGER NOT NULL,
            power        INTEGER,
            life         INTEGER,
            counter      INTEGER,
            cost         INTEGER
        )""",
        'INSERT INTO "card" (id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, '
        '                    effect_fk, trigger_fk, number, power, life, counter, cost) '
        'SELECT id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, '
        '       effect_fk, trigger_fk, number, power, life, counter, cost FROM "card_old"',
    )

    _rebuild(
        conn, "card_effect_history",
        """CREATE TABLE "card_effect_history" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            card_fk     INTEGER NOT NULL REFERENCES "card"(id),
            effect_fk   INTEGER NOT NULL REFERENCES "effect"(id),
            valid_from  DATE NOT NULL,
            valid_to    DATE
        )""",
        'INSERT INTO "card_effect_history" '
        '(id, created_ts, updated_ts, card_fk, effect_fk, valid_from, valid_to) '
        'SELECT id, created_ts, updated_ts, card_fk, effect_fk, valid_from, valid_to '
        'FROM "card_effect_history_old"',
    )

    _rebuild(
        conn, "card_trigger_history",
        """CREATE TABLE "card_trigger_history" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            card_fk     INTEGER NOT NULL REFERENCES "card"(id),
            trigger_fk  INTEGER NOT NULL REFERENCES "trigger"(id),
            valid_from  DATE NOT NULL,
            valid_to    DATE
        )""",
        'INSERT INTO "card_trigger_history" '
        '(id, created_ts, updated_ts, card_fk, trigger_fk, valid_from, valid_to) '
        'SELECT id, created_ts, updated_ts, card_fk, trigger_fk, valid_from, valid_to '
        'FROM "card_trigger_history_old"',
    )

    # card_trigger was dropped in e5f6a7b8c9d0; re-add with correct column order
    conn.execute(sa.text(
        """CREATE TABLE "card_trigger" (
            id          INTEGER PRIMARY KEY,
            created_ts  DATE,
            updated_ts  DATE,
            card_fk     INTEGER NOT NULL REFERENCES "card"(id),
            trigger_fk  INTEGER NOT NULL REFERENCES "trigger"(id)
        )"""
    ))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    conn.execute(sa.text('DROP TABLE "card_trigger"'))

    _rebuild(
        conn, "card_trigger_history",
        """CREATE TABLE "card_trigger_history" (
            id          INTEGER PRIMARY KEY,
            card_fk     INTEGER NOT NULL REFERENCES "card"(id),
            trigger_fk  INTEGER NOT NULL REFERENCES "trigger"(id),
            valid_from  DATE NOT NULL,
            valid_to    DATE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "card_trigger_history" '
        '(id, card_fk, trigger_fk, valid_from, valid_to, created_ts, updated_ts) '
        'SELECT id, card_fk, trigger_fk, valid_from, valid_to, created_ts, updated_ts '
        'FROM "card_trigger_history_old"',
    )

    _rebuild(
        conn, "card_effect_history",
        """CREATE TABLE "card_effect_history" (
            id          INTEGER PRIMARY KEY,
            card_fk     INTEGER NOT NULL REFERENCES "card"(id),
            effect_fk   INTEGER NOT NULL REFERENCES "effect"(id),
            valid_from  DATE NOT NULL,
            valid_to    DATE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "card_effect_history" '
        '(id, card_fk, effect_fk, valid_from, valid_to, created_ts, updated_ts) '
        'SELECT id, card_fk, effect_fk, valid_from, valid_to, created_ts, updated_ts '
        'FROM "card_effect_history_old"',
    )

    _rebuild(
        conn, "card",
        """CREATE TABLE "card" (
            id           INTEGER PRIMARY KEY,
            set_fk       INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk  INTEGER NOT NULL REFERENCES "card_type"(id),
            number       INTEGER NOT NULL,
            power        INTEGER,
            life         INTEGER,
            counter      INTEGER,
            cost         INTEGER,
            name_fk      INTEGER NOT NULL REFERENCES "name"(id),
            effect_fk    INTEGER REFERENCES "effect"(id),
            trigger_fk   INTEGER REFERENCES "trigger"(id),
            created_ts   DATE,
            updated_ts   DATE
        )""",
        'INSERT INTO "card" (id, set_fk, cardtype_fk, number, power, life, counter, cost, '
        '                    name_fk, effect_fk, trigger_fk, created_ts, updated_ts) '
        'SELECT id, set_fk, cardtype_fk, number, power, life, counter, cost, '
        '       name_fk, effect_fk, trigger_fk, created_ts, updated_ts FROM "card_old"',
    )

    _rebuild(
        conn, "trigger",
        """CREATE TABLE "trigger" (
            id      INTEGER PRIMARY KEY,
            trigger TEXT NOT NULL UNIQUE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "trigger" (id, trigger, created_ts, updated_ts) '
        'SELECT id, trigger, created_ts, updated_ts FROM "trigger_old"',
    )

    _rebuild(
        conn, "effect",
        """CREATE TABLE "effect" (
            id      INTEGER PRIMARY KEY,
            effect  TEXT NOT NULL UNIQUE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "effect" (id, effect, created_ts, updated_ts) '
        'SELECT id, effect, created_ts, updated_ts FROM "effect_old"',
    )

    _rebuild(
        conn, "image",
        """CREATE TABLE "image" (
            id      INTEGER PRIMARY KEY,
            path    TEXT NOT NULL UNIQUE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "image" (id, path, created_ts, updated_ts) '
        'SELECT id, path, created_ts, updated_ts FROM "image_old"',
    )

    _rebuild(
        conn, "name",
        """CREATE TABLE "name" (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL UNIQUE,
            created_ts  DATE,
            updated_ts  DATE
        )""",
        'INSERT INTO "name" (id, name, created_ts, updated_ts) '
        'SELECT id, name, created_ts, updated_ts FROM "name_old"',
    )

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
