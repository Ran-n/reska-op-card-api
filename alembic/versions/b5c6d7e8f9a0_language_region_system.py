#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/21 00:00:00.000000
Revised: 2026/05/21 13:54:54.408955

add language/region/region_language tables, naip.language_fk, and seed data

Revision ID: b5c6d7e8f9a0
Revises: b4c5d6e7f8a9
Create Date: 2026-05-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: str | Sequence[str] | None = "b4c5d6e7f8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"
_TS_EXPR = "strftime('%Y-%m-%d %H:%M:%f', 'now')"

# BCP-47 language seed rows: (code, name)
_LANGUAGES = [
    ("ja", "Japanese"),
    ("en", "English"),
    ("fr", "French"),
    ("zh-Hans", "Simplified Chinese"),
    ("ko", "Korean"),
]

# UN M.49 region seed rows: (code, name)
_REGIONS = [
    ("392", "Japan"),
    ("003", "North America"),
    ("150", "Europe"),
    ("419", "Latin America and the Caribbean"),
    ("009", "Oceania"),
    ("145", "Western Asia"),
    ("156", "China (Mainland)"),
    ("410", "Korea (Republic of)"),
    ("702", "Singapore"),
    ("458", "Malaysia"),
    ("360", "Indonesia"),
    ("608", "Philippines"),
    ("158", "Taiwan"),
    ("764", "Thailand"),
    ("344", "Hong Kong S.A.R."),
]

# region_language join seed: (region_code, language_code)
_REGION_LANGUAGES = [
    ("392", "ja"),
    ("003", "en"),
    ("150", "en"),
    ("150", "fr"),
    ("419", "en"),
    ("009", "en"),
    ("145", "en"),
    ("156", "zh-Hans"),
    ("410", "ko"),
    ("702", "en"),
    ("702", "ja"),
    ("458", "en"),
    ("458", "ja"),
    ("360", "en"),
    ("360", "ja"),
    ("608", "en"),
    ("608", "ja"),
    ("158", "ja"),
    ("158", "en"),
    ("764", "ja"),
    ("764", "en"),
    ("344", "ja"),
    ("344", "en"),
]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # ── 1. language table ─────────────────────────────────────────────────────
    conn.execute(
        sa.text(f"""
        CREATE TABLE language (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            code       TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            "desc"     TEXT,
            image_fk   INTEGER REFERENCES "image"(id)
        )
    """)
    )
    conn.execute(
        sa.text(f"""
        CREATE TRIGGER trg_language_update
        AFTER UPDATE ON language
        FOR EACH ROW
        WHEN NEW.updated_ts IS OLD.updated_ts
        BEGIN
            UPDATE language SET updated_ts = {_TS_EXPR} WHERE id = NEW.id;
        END
    """)
    )

    # ── 2. region table ───────────────────────────────────────────────────────
    conn.execute(
        sa.text(f"""
        CREATE TABLE region (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            code       TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )
    conn.execute(
        sa.text(f"""
        CREATE TRIGGER trg_region_update
        AFTER UPDATE ON region
        FOR EACH ROW
        WHEN NEW.updated_ts IS OLD.updated_ts
        BEGIN
            UPDATE region SET updated_ts = {_TS_EXPR} WHERE id = NEW.id;
        END
    """)
    )

    # ── 3. region_language junction table ─────────────────────────────────────
    conn.execute(
        sa.text(f"""
        CREATE TABLE region_language (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            region_fk   INTEGER NOT NULL REFERENCES region(id),
            language_fk INTEGER NOT NULL REFERENCES language(id),
            UNIQUE (region_fk, language_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_region_language_region_fk ON region_language (region_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_region_language_language_fk ON region_language (language_fk)"))
    conn.execute(
        sa.text(f"""
        CREATE TRIGGER trg_region_language_update
        AFTER UPDATE ON region_language
        FOR EACH ROW
        WHEN NEW.updated_ts IS OLD.updated_ts
        BEGIN
            UPDATE region_language SET updated_ts = {_TS_EXPR} WHERE id = NEW.id;
        END
    """)
    )

    # ── 4. naip.language_fk column ───────────────────────────────────────────
    conn.execute(sa.text("ALTER TABLE naip ADD COLUMN language_fk INTEGER REFERENCES language(id)"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))

    # ── 5. seed data ──────────────────────────────────────────────────────────
    for code, name in _LANGUAGES:
        conn.execute(sa.text("INSERT INTO language (code, name) VALUES (:code, :name)"), {"code": code, "name": name})

    for code, name in _REGIONS:
        conn.execute(sa.text("INSERT INTO region (code, name) VALUES (:code, :name)"), {"code": code, "name": name})

    for region_code, lang_code in _REGION_LANGUAGES:
        conn.execute(
            sa.text("""
            INSERT INTO region_language (region_fk, language_fk)
            SELECT r.id, l.id
            FROM region r, language l
            WHERE r.code = :rc AND l.code = :lc
        """),
            {"rc": region_code, "lc": lang_code},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # Remove language_fk from naip via table rebuild
    conn.execute(
        sa.text("""
        CREATE TABLE naip_new AS
        SELECT id, created_ts, updated_ts, card_fk, set_fk, artist_fk, rarity_fk,
               effect_fk, trigger_fk, name_fk, image_fk, is_default, is_errata,
               sort_order, serial_max, cardtype_fk, block_fk, power, life, counter, cost
        FROM naip
    """)
    )

    idx_rows = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='naip'")).fetchall()
    for (idx_name,) in idx_rows:
        if not idx_name.startswith("sqlite_autoindex_"):
            conn.execute(sa.text(f'DROP INDEX IF EXISTS "{idx_name}"'))

    conn.execute(sa.text("DROP TABLE naip"))
    conn.execute(
        sa.text("""
        CREATE TABLE naip (
            id          INTEGER PRIMARY KEY,
            created_ts  TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            updated_ts  TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            card_fk     INTEGER NOT NULL REFERENCES card(id),
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            artist_fk   INTEGER REFERENCES artist(id),
            rarity_fk   INTEGER REFERENCES rarity(id),
            effect_fk   INTEGER REFERENCES "effect"(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            name_fk     INTEGER REFERENCES "name"(id),
            image_fk    INTEGER REFERENCES "image"(id),
            is_default  INTEGER NOT NULL DEFAULT 0,
            is_errata   INTEGER NOT NULL DEFAULT 0,
            sort_order  INTEGER,
            serial_max  INTEGER,
            cardtype_fk INTEGER REFERENCES card_type(id),
            block_fk    INTEGER REFERENCES block(id),
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER
        )
    """)
    )
    conn.execute(
        sa.text("""
        INSERT INTO naip SELECT * FROM naip_new
    """)
    )
    conn.execute(sa.text("DROP TABLE naip_new"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1"))
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip (card_fk, set_fk, artist_fk, rarity_fk) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
        )
    )

    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_region_language_update"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_region_language_region_fk"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_region_language_language_fk"))
    conn.execute(sa.text("DROP TABLE IF EXISTS region_language"))

    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_region_update"))
    conn.execute(sa.text("DROP TABLE IF EXISTS region"))

    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_language_update"))
    conn.execute(sa.text("DROP TABLE IF EXISTS language"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
