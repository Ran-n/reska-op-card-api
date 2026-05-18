#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/18 00:00:00.000000
Revised: 2026/05/18 14:15:44.734582

add db-side timestamp defaults and update triggers

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "h2i3j4k5l6m7"
down_revision: str | Sequence[str] | None = "g1h2i3j4k5l6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"
_TS_EXPR = "strftime('%Y-%m-%d %H:%M:%f', 'now')"

# Tables that carry AFTER UPDATE triggers
_TRIGGER_TABLES = [
    "set_type", "card_type", "artist", "rarity", "tribe", "attribute",
    "color", "block", "format", "keyword", "resword", "set", "name",
    "image", "effect", "trigger", "card", "naip",
    "card_effect_history", "card_trigger_history",
    "card_tribe", "card_attribute", "card_color", "card_rarity",
    "card_block", "card_format", "card_keyword", "card_resword",
    "naip_color", "naip_tribe", "naip_attribute", "naip_keyword",
    "naip_resword", "naip_block", "naip_format",
]

# (old_name, new_ddl, columns_to_copy, post_indexes)
# Rebuilds are ordered leaf-first so FKs stay valid during the rebuild.
# All tables that previously had stale FK references (_old suffixes) are
# also corrected here.
_REBUILDS = [
    # ── Lookup tables (no outbound FKs) ──────────────────────────────────────
    (
        "set_type",
        f"""CREATE TABLE set_type (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "card_type",
        f"""CREATE TABLE card_type (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     VARCHAR NOT NULL,
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, symbol, name, \"desc\"",
        [],
    ),
    (
        "artist",
        f"""CREATE TABLE artist (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "rarity",
        f"""CREATE TABLE rarity (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     VARCHAR NOT NULL,
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, symbol, name, \"desc\"",
        [],
    ),
    (
        "tribe",
        f"""CREATE TABLE tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "attribute",
        f"""CREATE TABLE attribute (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "color",
        f"""CREATE TABLE color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "block",
        f"""CREATE TABLE block (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "format",
        f"""CREATE TABLE format (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "keyword",
        f"""CREATE TABLE keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    (
        "resword",
        f"""CREATE TABLE resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       VARCHAR NOT NULL,
            "desc"     VARCHAR
        )""",
        "id, created_ts, updated_ts, name, \"desc\"",
        [],
    ),
    # ── Text-dedup lookup tables ──────────────────────────────────────────────
    (
        "name",
        f"""CREATE TABLE "name" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL UNIQUE
        )""",
        "id, created_ts, updated_ts, name",
        [],
    ),
    (
        "image",
        f"""CREATE TABLE "image" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            path       TEXT NOT NULL UNIQUE
        )""",
        "id, created_ts, updated_ts, path",
        [],
    ),
    (
        "effect",
        f"""CREATE TABLE "effect" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            effect     TEXT NOT NULL UNIQUE
        )""",
        "id, created_ts, updated_ts, effect",
        [],
    ),
    (
        "trigger",
        f"""CREATE TABLE "trigger" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            trigger    TEXT NOT NULL UNIQUE
        )""",
        "id, created_ts, updated_ts, trigger",
        [],
    ),
    # ── set (depends on set_type) ─────────────────────────────────────────────
    (
        "set",
        f"""CREATE TABLE "set" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            type_fk    INTEGER REFERENCES set_type(id),
            code       TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            series     TEXT,
            ord        INTEGER,
            "desc"     TEXT,
            release_ts TEXT
        )""",
        "id, created_ts, updated_ts, type_fk, code, name, series, ord, \"desc\", release_ts",
        [],
    ),
    # ── card (depends on set, card_type, name, effect, trigger) ──────────────
    (
        "card",
        f"""CREATE TABLE card (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk INTEGER NOT NULL REFERENCES card_type(id),
            name_fk     INTEGER NOT NULL REFERENCES "name"(id),
            effect_fk   INTEGER REFERENCES "effect"(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            number      INTEGER NOT NULL,
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER,
            UNIQUE (set_fk, number)
        )""",
        "id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, effect_fk, trigger_fk, number, power, life, counter, cost",
        [
            "CREATE INDEX ix_card_set_fk ON card (set_fk)",
            "CREATE INDEX ix_card_cardtype_fk ON card (cardtype_fk)",
            "CREATE INDEX ix_card_name_fk ON card (name_fk)",
        ],
    ),
    # ── naip (depends on card, set, artist, rarity, name, image, effect,
    #          trigger, card_type) ────────────────────────────────────────────
    (
        "naip",
        f"""CREATE TABLE naip (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
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
            cardtype_fk INTEGER REFERENCES card_type(id),
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER
        )""",
        "id, created_ts, updated_ts, card_fk, set_fk, artist_fk, rarity_fk, "
        "effect_fk, trigger_fk, name_fk, image_fk, is_default, is_errata, "
        "sort_order, cardtype_fk, power, life, counter, cost",
        [
            "CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1",
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip (card_fk, set_fk, artist_fk, rarity_fk) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL",
        ],
    ),
    # ── history tables ────────────────────────────────────────────────────────
    (
        "card_effect_history",
        f"""CREATE TABLE card_effect_history (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            effect_fk  INTEGER NOT NULL REFERENCES "effect"(id),
            valid_from DATE NOT NULL,
            valid_to   DATE
        )""",
        "id, created_ts, updated_ts, card_fk, effect_fk, valid_from, valid_to",
        [],
    ),
    (
        "card_trigger_history",
        f"""CREATE TABLE card_trigger_history (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            trigger_fk INTEGER NOT NULL REFERENCES "trigger"(id),
            valid_from DATE NOT NULL,
            valid_to   DATE
        )""",
        "id, created_ts, updated_ts, card_fk, trigger_fk, valid_from, valid_to",
        [],
    ),
    # ── card junction tables ──────────────────────────────────────────────────
    (
        "card_tribe",
        f"""CREATE TABLE card_tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            tribe_fk   INTEGER NOT NULL REFERENCES tribe(id),
            UNIQUE (card_fk, tribe_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, tribe_fk",
        [
            "CREATE INDEX ix_card_tribe_card_fk ON card_tribe (card_fk)",
            "CREATE INDEX ix_card_tribe_tribe_fk ON card_tribe (tribe_fk)",
        ],
    ),
    (
        "card_attribute",
        f"""CREATE TABLE card_attribute (
            id           INTEGER PRIMARY KEY,
            created_ts   {_TS},
            updated_ts   {_TS},
            card_fk      INTEGER NOT NULL REFERENCES card(id),
            attribute_fk INTEGER NOT NULL REFERENCES attribute(id),
            UNIQUE (card_fk, attribute_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, attribute_fk",
        [
            "CREATE INDEX ix_card_attribute_card_fk ON card_attribute (card_fk)",
            "CREATE INDEX ix_card_attribute_attribute_fk ON card_attribute (attribute_fk)",
        ],
    ),
    (
        "card_color",
        f"""CREATE TABLE card_color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            color_fk   INTEGER NOT NULL REFERENCES color(id),
            UNIQUE (card_fk, color_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, color_fk",
        [
            "CREATE INDEX ix_card_color_card_fk ON card_color (card_fk)",
            "CREATE INDEX ix_card_color_color_fk ON card_color (color_fk)",
        ],
    ),
    (
        "card_rarity",
        f"""CREATE TABLE card_rarity (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            rarity_fk  INTEGER NOT NULL REFERENCES rarity(id),
            UNIQUE (card_fk, rarity_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, rarity_fk",
        [
            "CREATE INDEX ix_card_rarity_card_fk ON card_rarity (card_fk)",
            "CREATE INDEX ix_card_rarity_rarity_fk ON card_rarity (rarity_fk)",
        ],
    ),
    (
        "card_block",
        f"""CREATE TABLE card_block (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            block_fk   INTEGER NOT NULL REFERENCES block(id),
            UNIQUE (card_fk, block_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, block_fk",
        [
            "CREATE INDEX ix_card_block_card_fk ON card_block (card_fk)",
            "CREATE INDEX ix_card_block_block_fk ON card_block (block_fk)",
        ],
    ),
    (
        "card_format",
        f"""CREATE TABLE card_format (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            format_fk  INTEGER NOT NULL REFERENCES format(id),
            UNIQUE (card_fk, format_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, format_fk",
        [
            "CREATE INDEX ix_card_format_card_fk ON card_format (card_fk)",
            "CREATE INDEX ix_card_format_format_fk ON card_format (format_fk)",
        ],
    ),
    (
        "card_keyword",
        f"""CREATE TABLE card_keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            keyword_fk INTEGER NOT NULL REFERENCES keyword(id),
            UNIQUE (card_fk, keyword_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, keyword_fk",
        [
            "CREATE INDEX ix_card_keyword_card_fk ON card_keyword (card_fk)",
            "CREATE INDEX ix_card_keyword_keyword_fk ON card_keyword (keyword_fk)",
        ],
    ),
    (
        "card_resword",
        f"""CREATE TABLE card_resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            resword_fk INTEGER NOT NULL REFERENCES resword(id),
            UNIQUE (card_fk, resword_fk)
        )""",
        "id, created_ts, updated_ts, card_fk, resword_fk",
        [
            "CREATE INDEX ix_card_resword_card_fk ON card_resword (card_fk)",
            "CREATE INDEX ix_card_resword_resword_fk ON card_resword (resword_fk)",
        ],
    ),
    # ── naip junction tables ──────────────────────────────────────────────────
    (
        "naip_color",
        f"""CREATE TABLE naip_color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            color_fk   INTEGER NOT NULL REFERENCES color(id),
            UNIQUE (naip_fk, color_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, color_fk",
        [
            "CREATE INDEX ix_naip_color_naip_fk ON naip_color (naip_fk)",
            "CREATE INDEX ix_naip_color_color_fk ON naip_color (color_fk)",
        ],
    ),
    (
        "naip_tribe",
        f"""CREATE TABLE naip_tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            tribe_fk   INTEGER NOT NULL REFERENCES tribe(id),
            UNIQUE (naip_fk, tribe_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, tribe_fk",
        [
            "CREATE INDEX ix_naip_tribe_naip_fk ON naip_tribe (naip_fk)",
            "CREATE INDEX ix_naip_tribe_tribe_fk ON naip_tribe (tribe_fk)",
        ],
    ),
    (
        "naip_attribute",
        f"""CREATE TABLE naip_attribute (
            id           INTEGER PRIMARY KEY,
            created_ts   {_TS},
            updated_ts   {_TS},
            naip_fk      INTEGER NOT NULL REFERENCES naip(id),
            attribute_fk INTEGER NOT NULL REFERENCES attribute(id),
            UNIQUE (naip_fk, attribute_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, attribute_fk",
        [
            "CREATE INDEX ix_naip_attribute_naip_fk ON naip_attribute (naip_fk)",
            "CREATE INDEX ix_naip_attribute_attribute_fk ON naip_attribute (attribute_fk)",
        ],
    ),
    (
        "naip_keyword",
        f"""CREATE TABLE naip_keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            keyword_fk INTEGER NOT NULL REFERENCES keyword(id),
            UNIQUE (naip_fk, keyword_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, keyword_fk",
        [
            "CREATE INDEX ix_naip_keyword_naip_fk ON naip_keyword (naip_fk)",
            "CREATE INDEX ix_naip_keyword_keyword_fk ON naip_keyword (keyword_fk)",
        ],
    ),
    (
        "naip_resword",
        f"""CREATE TABLE naip_resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            resword_fk INTEGER NOT NULL REFERENCES resword(id),
            UNIQUE (naip_fk, resword_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, resword_fk",
        [
            "CREATE INDEX ix_naip_resword_naip_fk ON naip_resword (naip_fk)",
            "CREATE INDEX ix_naip_resword_resword_fk ON naip_resword (resword_fk)",
        ],
    ),
    (
        "naip_block",
        f"""CREATE TABLE naip_block (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            block_fk   INTEGER NOT NULL REFERENCES block(id),
            UNIQUE (naip_fk, block_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, block_fk",
        [
            "CREATE INDEX ix_naip_block_naip_fk ON naip_block (naip_fk)",
            "CREATE INDEX ix_naip_block_block_fk ON naip_block (block_fk)",
        ],
    ),
    (
        "naip_format",
        f"""CREATE TABLE naip_format (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            format_fk  INTEGER NOT NULL REFERENCES format(id),
            UNIQUE (naip_fk, format_fk)
        )""",
        "id, created_ts, updated_ts, naip_fk, format_fk",
        [
            "CREATE INDEX ix_naip_format_naip_fk ON naip_format (naip_fk)",
            "CREATE INDEX ix_naip_format_format_fk ON naip_format (format_fk)",
        ],
    ),
]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    for tbl, ddl, cols, indexes in _REBUILDS:
        # Drop all indexes on this table before renaming
        idx_rows = conn.execute(
            sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{tbl}'")
        ).fetchall()
        for (idx_name,) in idx_rows:
            if not idx_name.startswith("sqlite_autoindex_"):
                conn.execute(sa.text(f'DROP INDEX IF EXISTS "{idx_name}"'))

        conn.execute(sa.text(f'ALTER TABLE "{tbl}" RENAME TO "{tbl}_old"'))
        conn.execute(sa.text(ddl))
        conn.execute(sa.text(f'INSERT INTO "{tbl}" ({cols}) SELECT {cols} FROM "{tbl}_old"'))
        conn.execute(sa.text(f'DROP TABLE "{tbl}_old"'))

        for idx_sql in indexes:
            conn.execute(sa.text(idx_sql))

    # AFTER UPDATE triggers — fire when updated_ts is not explicitly changed
    for tbl in _TRIGGER_TABLES:
        conn.execute(sa.text(f"""
            CREATE TRIGGER IF NOT EXISTS trg_{tbl}_update
            AFTER UPDATE ON "{tbl}"
            FOR EACH ROW
            WHEN NEW.updated_ts IS OLD.updated_ts
            BEGIN
                UPDATE "{tbl}"
                SET updated_ts = {_TS_EXPR}
                WHERE id = NEW.id;
            END
        """))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    for tbl in _TRIGGER_TABLES:
        conn.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{tbl}_update"))
