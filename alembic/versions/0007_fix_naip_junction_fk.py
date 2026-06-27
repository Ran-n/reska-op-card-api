#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/26
Revised: 2026/06/26

Fix naip junction table FK references broken by migration 0003.

ALTER TABLE naip RENAME TO naip_old in 0003_print_variant caused SQLite
to rewrite all FK references in child tables from naip → naip_old, even
though PRAGMA foreign_keys = OFF was set. After naip_old was dropped, the
FK definitions in naip_color/tribe/attribute/keyword/resword/serial became
dangling, causing OperationalError on any DML with foreign_keys = ON.

Revision ID: 0007_fix_naip_junction_fk
Revises: 0006_add_missing_indexes
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_fix_naip_junction_fk"
down_revision: str | Sequence[str] | None = "0006_add_missing_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"

_JUNCTION_TABLES = [
    (
        "naip_color",
        "naip_color_old",
        f"""CREATE TABLE naip_color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            color_fk   INTEGER NOT NULL REFERENCES color(id),
            UNIQUE (naip_fk, color_fk)
        )""",
        "INSERT INTO naip_color SELECT id, created_ts, updated_ts, naip_fk, color_fk FROM naip_color_old",
    ),
    (
        "naip_tribe",
        "naip_tribe_old",
        f"""CREATE TABLE naip_tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            tribe_fk   INTEGER NOT NULL REFERENCES tribe(id),
            UNIQUE (naip_fk, tribe_fk)
        )""",
        "INSERT INTO naip_tribe SELECT id, created_ts, updated_ts, naip_fk, tribe_fk FROM naip_tribe_old",
    ),
    (
        "naip_attribute",
        "naip_attribute_old",
        f"""CREATE TABLE naip_attribute (
            id           INTEGER PRIMARY KEY,
            created_ts   {_TS},
            updated_ts   {_TS},
            naip_fk      INTEGER NOT NULL REFERENCES naip(id),
            attribute_fk INTEGER NOT NULL REFERENCES attribute(id),
            UNIQUE (naip_fk, attribute_fk)
        )""",
        "INSERT INTO naip_attribute SELECT id, created_ts, updated_ts, naip_fk, attribute_fk FROM naip_attribute_old",
    ),
    (
        "naip_keyword",
        "naip_keyword_old",
        f"""CREATE TABLE naip_keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            keyword_fk INTEGER NOT NULL REFERENCES keyword(id),
            UNIQUE (naip_fk, keyword_fk)
        )""",
        "INSERT INTO naip_keyword SELECT id, created_ts, updated_ts, naip_fk, keyword_fk FROM naip_keyword_old",
    ),
    (
        "naip_resword",
        "naip_resword_old",
        f"""CREATE TABLE naip_resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            resword_fk INTEGER NOT NULL REFERENCES resword(id),
            UNIQUE (naip_fk, resword_fk)
        )""",
        "INSERT INTO naip_resword SELECT id, created_ts, updated_ts, naip_fk, resword_fk FROM naip_resword_old",
    ),
    (
        "naip_serial",
        "naip_serial_old",
        f"""CREATE TABLE naip_serial (
            id            INTEGER PRIMARY KEY,
            created_ts    {_TS},
            updated_ts    {_TS},
            naip_fk       INTEGER NOT NULL REFERENCES naip(id),
            serial_number INTEGER NOT NULL,
            image_fk      INTEGER REFERENCES image(id),
            UNIQUE (naip_fk, serial_number),
            CONSTRAINT ck_naip_serial_number_positive CHECK (serial_number >= 1)
        )""",
        "INSERT INTO naip_serial SELECT id, created_ts, updated_ts, naip_fk, serial_number, image_fk FROM naip_serial_old",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))
    conn.execute(sa.text("PRAGMA legacy_alter_table = ON"))

    for table, tmp, create_sql, copy_sql in _JUNCTION_TABLES:
        conn.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_update"))
        conn.execute(sa.text(f"ALTER TABLE {table} RENAME TO {tmp}"))
        conn.execute(sa.text(create_sql))
        conn.execute(sa.text(copy_sql))
        conn.execute(sa.text(f"DROP TABLE {tmp}"))

    conn.execute(sa.text("PRAGMA legacy_alter_table = OFF"))
    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    # Data is preserved; downgrade is a no-op since naip_old no longer exists
    # and the broken state cannot be safely restored.
    pass
