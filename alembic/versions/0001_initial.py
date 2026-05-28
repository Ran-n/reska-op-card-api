#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/28 13:10:27.857387
Revised: 2026/05/28 13:10:27.857387

squashed initial schema with seed data

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"
_TS_EXPR = "strftime('%Y-%m-%d %H:%M:%f', 'now')"

# All tables that carry an AFTER UPDATE trigger (every table with updated_ts)
_TRIGGER_TABLES = [
    "set_type",
    "card_type",
    "artist",
    "rarity",
    "tribe",
    "attribute",
    "color",
    "block",
    "format",
    "keyword",
    "resword",
    "name",
    "image",
    "effect",
    "trigger",
    "language",
    "region",
    "region_language",
    "set",
    "card",
    "naip",
    "naip_serial",
    "card_effect_history",
    "card_trigger_history",
    "card_tribe",
    "card_attribute",
    "card_color",
    "card_rarity",
    "card_format",
    "card_keyword",
    "card_resword",
    "naip_color",
    "naip_tribe",
    "naip_attribute",
    "naip_keyword",
    "naip_resword",
    "card_ban",
    "banned_pair",
]

# ── Seed data ─────────────────────────────────────────────────────────────────

_CARD_TYPES = [
    ("LEADER", "Leader"),
    ("CHARACTER", "Character"),
    ("EVENT", "Event"),
    ("STAGE", "Stage"),
    ("DON", "DON!!"),
]

# (symbol, name, is_type, is_base)
_RARITIES = [
    ("C", "Common", False, True),
    ("UC", "Uncommon", False, True),
    ("R", "Rare", False, True),
    ("SR", "Super Rare", False, True),
    ("SEC", "Secret Rare", False, True),
    ("L", "Leader", True, True),
    ("P", "Promo", False, True),
    ("TR", "Treasure Rare", False, False),
    ("AA", "Alternate Art", False, False),
    ("SP", "Special Rare", False, False),
    ("MR", "Manga Rare", False, False),
    ("FA", "Full Art", False, False),
    ("D", "DON!!", True, True),
    ("AU", "Gold Rare", False, False),
    ("AG", "Silver Rare", False, False),
    ("AUD", "Gold DON!! Rare", False, False),
    ("EMR", "Event Manga Rare", False, False),
    ("PTR", "Pattern Rare", False, False),
    ("FD", "Foil DON!! Rare", False, False),
    ("NFD", "Non-Foil DON!!", False, True),
]

# (code, name)
_LANGUAGES = [
    ("ja", "Japanese"),
    ("en", "English"),
    ("fr", "French"),
    ("zh-Hans", "Simplified Chinese"),
    ("ko", "Korean"),
]

# (code, name)
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

# (region_code, language_code)
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

    # ── Leaf lookup tables (no outbound FKs) ─────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE set_type (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_type (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     TEXT NOT NULL,
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE artist (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE rarity (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     TEXT NOT NULL,
            name       TEXT NOT NULL,
            "desc"     TEXT,
            is_type    INTEGER NOT NULL DEFAULT 0,
            is_base    INTEGER NOT NULL DEFAULT 0
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE attribute (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE block (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT,
            image_fk   INTEGER REFERENCES image(id)
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE format (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )

    # ── Text-dedup lookup tables ──────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE "name" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            name       TEXT NOT NULL UNIQUE
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE image (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            path       TEXT NOT NULL UNIQUE
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE effect (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            effect     TEXT NOT NULL UNIQUE
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE "trigger" (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            trigger    TEXT NOT NULL UNIQUE
        )
    """)
    )

    # ── Language / region ─────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE language (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            code       TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            "desc"     TEXT,
            image_fk   INTEGER REFERENCES image(id)
        )
    """)
    )

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

    # ── Set ───────────────────────────────────────────────────────────────────

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

    # ── Card ──────────────────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE card (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk INTEGER NOT NULL REFERENCES card_type(id),
            name_fk     INTEGER NOT NULL REFERENCES "name"(id),
            effect_fk   INTEGER REFERENCES effect(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            block_fk    INTEGER REFERENCES block(id),
            number      INTEGER NOT NULL,
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER,
            UNIQUE (set_fk, number)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_set_fk ON card (set_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_cardtype_fk ON card (cardtype_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_name_fk ON card (name_fk)"))

    # ── Naip ──────────────────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            card_fk     INTEGER NOT NULL REFERENCES card(id),
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            artist_fk   INTEGER REFERENCES artist(id),
            rarity_fk   INTEGER REFERENCES rarity(id),
            name_fk     INTEGER REFERENCES "name"(id),
            image_fk    INTEGER REFERENCES image(id),
            effect_fk   INTEGER REFERENCES effect(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            is_default  INTEGER NOT NULL DEFAULT 0,
            is_errata   INTEGER NOT NULL DEFAULT 0,
            sort_order  INTEGER,
            serial_max  INTEGER,
            cardtype_fk INTEGER REFERENCES card_type(id),
            block_fk    INTEGER REFERENCES block(id),
            language_fk INTEGER REFERENCES language(id),
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER
        )
    """)
    )
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1"))
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip (card_fk, set_fk, artist_fk, rarity_fk) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
        )
    )

    # ── Naip serial ───────────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_serial (
            id            INTEGER PRIMARY KEY,
            created_ts    {_TS},
            updated_ts    {_TS},
            naip_fk       INTEGER NOT NULL REFERENCES naip(id),
            serial_number INTEGER NOT NULL,
            image_fk      INTEGER REFERENCES image(id),
            UNIQUE (naip_fk, serial_number),
            CONSTRAINT ck_naip_serial_number_positive CHECK (serial_number >= 1)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_serial_naip_fk ON naip_serial (naip_fk)"))

    # ── History tables ────────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_effect_history (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            effect_fk  INTEGER NOT NULL REFERENCES effect(id),
            valid_from DATE NOT NULL,
            valid_to   DATE
        )
    """)
    )

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_trigger_history (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            trigger_fk INTEGER NOT NULL REFERENCES "trigger"(id),
            valid_from DATE NOT NULL,
            valid_to   DATE
        )
    """)
    )

    # ── Card junction tables ──────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            tribe_fk   INTEGER NOT NULL REFERENCES tribe(id),
            UNIQUE (card_fk, tribe_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_tribe_card_fk ON card_tribe (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_tribe_tribe_fk ON card_tribe (tribe_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_attribute (
            id           INTEGER PRIMARY KEY,
            created_ts   {_TS},
            updated_ts   {_TS},
            card_fk      INTEGER NOT NULL REFERENCES card(id),
            attribute_fk INTEGER NOT NULL REFERENCES attribute(id),
            UNIQUE (card_fk, attribute_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_attribute_card_fk ON card_attribute (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_attribute_attribute_fk ON card_attribute (attribute_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            color_fk   INTEGER NOT NULL REFERENCES color(id),
            UNIQUE (card_fk, color_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_color_card_fk ON card_color (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_color_color_fk ON card_color (color_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_rarity (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            rarity_fk  INTEGER NOT NULL REFERENCES rarity(id),
            UNIQUE (card_fk, rarity_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_rarity_card_fk ON card_rarity (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_rarity_rarity_fk ON card_rarity (rarity_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_format (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            format_fk  INTEGER NOT NULL REFERENCES format(id),
            UNIQUE (card_fk, format_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_format_card_fk ON card_format (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_format_format_fk ON card_format (format_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            keyword_fk INTEGER NOT NULL REFERENCES keyword(id),
            UNIQUE (card_fk, keyword_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_keyword_card_fk ON card_keyword (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_keyword_keyword_fk ON card_keyword (keyword_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            resword_fk INTEGER NOT NULL REFERENCES resword(id),
            UNIQUE (card_fk, resword_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_card_resword_card_fk ON card_resword (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_resword_resword_fk ON card_resword (resword_fk)"))

    # ── Naip junction tables ──────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_color (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            color_fk   INTEGER NOT NULL REFERENCES color(id),
            UNIQUE (naip_fk, color_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_color_naip_fk ON naip_color (naip_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_naip_color_color_fk ON naip_color (color_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_tribe (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            tribe_fk   INTEGER NOT NULL REFERENCES tribe(id),
            UNIQUE (naip_fk, tribe_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_tribe_naip_fk ON naip_tribe (naip_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_naip_tribe_tribe_fk ON naip_tribe (tribe_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_attribute (
            id           INTEGER PRIMARY KEY,
            created_ts   {_TS},
            updated_ts   {_TS},
            naip_fk      INTEGER NOT NULL REFERENCES naip(id),
            attribute_fk INTEGER NOT NULL REFERENCES attribute(id),
            UNIQUE (naip_fk, attribute_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_attribute_naip_fk ON naip_attribute (naip_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_naip_attribute_attribute_fk ON naip_attribute (attribute_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_keyword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            keyword_fk INTEGER NOT NULL REFERENCES keyword(id),
            UNIQUE (naip_fk, keyword_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_keyword_naip_fk ON naip_keyword (naip_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_naip_keyword_keyword_fk ON naip_keyword (keyword_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip_resword (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            naip_fk    INTEGER NOT NULL REFERENCES naip(id),
            resword_fk INTEGER NOT NULL REFERENCES resword(id),
            UNIQUE (naip_fk, resword_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_resword_naip_fk ON naip_resword (naip_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_naip_resword_resword_fk ON naip_resword (resword_fk)"))

    # ── Ban tables ────────────────────────────────────────────────────────────

    conn.execute(
        sa.text(f"""
        CREATE TABLE card_ban (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_fk    INTEGER NOT NULL REFERENCES card(id),
            format_fk  INTEGER REFERENCES format(id),
            UNIQUE (card_fk, format_fk)
        )
    """)
    )
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_card_ban_global_unique ON card_ban (card_fk) WHERE format_fk IS NULL"))
    conn.execute(sa.text("CREATE INDEX ix_card_ban_card_fk ON card_ban (card_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_ban_format_fk ON card_ban (format_fk)"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE banned_pair (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            card_a_fk  INTEGER NOT NULL REFERENCES card(id),
            card_b_fk  INTEGER NOT NULL REFERENCES card(id),
            format_fk  INTEGER REFERENCES format(id),
            UNIQUE (card_a_fk, card_b_fk, format_fk),
            CONSTRAINT ck_banned_pair_ordered CHECK (card_a_fk < card_b_fk)
        )
    """)
    )
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_banned_pair_global_unique ON banned_pair (card_a_fk, card_b_fk) "
            "WHERE format_fk IS NULL"
        )
    )
    conn.execute(sa.text("CREATE INDEX ix_banned_pair_card_a_fk ON banned_pair (card_a_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_banned_pair_card_b_fk ON banned_pair (card_b_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_banned_pair_format_fk ON banned_pair (format_fk)"))

    # ── AFTER UPDATE triggers (updated_ts auto-refresh) ───────────────────────

    for tbl in _TRIGGER_TABLES:
        conn.execute(
            sa.text(f"""
            CREATE TRIGGER trg_{tbl}_update
            AFTER UPDATE ON "{tbl}"
            FOR EACH ROW
            WHEN NEW.updated_ts IS OLD.updated_ts
            BEGIN
                UPDATE "{tbl}" SET updated_ts = {_TS_EXPR} WHERE id = NEW.id;
            END
        """)
        )

    # ── naip_serial enforcement triggers ─────────────────────────────────────

    conn.execute(
        sa.text("""
        CREATE TRIGGER trg_naip_serial_check_max_insert
        BEFORE INSERT ON naip_serial
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'serial_number exceeds serial_max for this naip')
            WHERE (
                SELECT serial_max FROM naip WHERE id = NEW.naip_fk
            ) IS NOT NULL
            AND NEW.serial_number > (
                SELECT serial_max FROM naip WHERE id = NEW.naip_fk
            );
        END
    """)
    )

    conn.execute(
        sa.text("""
        CREATE TRIGGER trg_naip_serial_check_max_update
        BEFORE UPDATE ON naip_serial
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'serial_number exceeds serial_max for this naip')
            WHERE (
                SELECT serial_max FROM naip WHERE id = NEW.naip_fk
            ) IS NOT NULL
            AND NEW.serial_number > (
                SELECT serial_max FROM naip WHERE id = NEW.naip_fk
            );
        END
    """)
    )

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))

    # ── Seed data ─────────────────────────────────────────────────────────────

    for symbol, name in _CARD_TYPES:
        conn.execute(
            sa.text("INSERT INTO card_type (symbol, name) VALUES (:s, :n)"),
            {"s": symbol, "n": name},
        )

    for symbol, name, is_type, is_base in _RARITIES:
        conn.execute(
            sa.text("INSERT INTO rarity (symbol, name, is_type, is_base) VALUES (:s, :n, :it, :ib)"),
            {"s": symbol, "n": name, "it": int(is_type), "ib": int(is_base)},
        )

    for code, name in _LANGUAGES:
        conn.execute(
            sa.text("INSERT INTO language (code, name) VALUES (:c, :n)"),
            {"c": code, "n": name},
        )

    for code, name in _REGIONS:
        conn.execute(
            sa.text("INSERT INTO region (code, name) VALUES (:c, :n)"),
            {"c": code, "n": name},
        )

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

    # Drop serial enforcement triggers
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_update"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_insert"))

    # Drop AFTER UPDATE triggers
    for tbl in reversed(_TRIGGER_TABLES):
        conn.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{tbl}_update"))

    # Drop indexes (partial indexes must be named explicitly)
    for idx in [
        "ix_banned_pair_format_fk",
        "ix_banned_pair_card_b_fk",
        "ix_banned_pair_card_a_fk",
        "ix_banned_pair_global_unique",
        "ix_card_ban_format_fk",
        "ix_card_ban_card_fk",
        "ix_card_ban_global_unique",
        "ix_naip_resword_resword_fk",
        "ix_naip_resword_naip_fk",
        "ix_naip_keyword_keyword_fk",
        "ix_naip_keyword_naip_fk",
        "ix_naip_attribute_attribute_fk",
        "ix_naip_attribute_naip_fk",
        "ix_naip_tribe_tribe_fk",
        "ix_naip_tribe_naip_fk",
        "ix_naip_color_color_fk",
        "ix_naip_color_naip_fk",
        "ix_card_resword_resword_fk",
        "ix_card_resword_card_fk",
        "ix_card_keyword_keyword_fk",
        "ix_card_keyword_card_fk",
        "ix_card_format_format_fk",
        "ix_card_format_card_fk",
        "ix_card_rarity_rarity_fk",
        "ix_card_rarity_card_fk",
        "ix_card_color_color_fk",
        "ix_card_color_card_fk",
        "ix_card_attribute_attribute_fk",
        "ix_card_attribute_card_fk",
        "ix_card_tribe_tribe_fk",
        "ix_card_tribe_card_fk",
        "ix_naip_serial_naip_fk",
        "ix_naip_unique_print",
        "ix_naip_one_default_per_card",
        "ix_card_name_fk",
        "ix_card_cardtype_fk",
        "ix_card_set_fk",
        "ix_region_language_language_fk",
        "ix_region_language_region_fk",
    ]:
        conn.execute(sa.text(f'DROP INDEX IF EXISTS "{idx}"'))

    # Drop tables in reverse dependency order
    for tbl in [
        "banned_pair",
        "card_ban",
        "naip_resword",
        "naip_keyword",
        "naip_attribute",
        "naip_tribe",
        "naip_color",
        "card_resword",
        "card_keyword",
        "card_format",
        "card_rarity",
        "card_color",
        "card_attribute",
        "card_tribe",
        "card_trigger_history",
        "card_effect_history",
        "naip_serial",
        "naip",
        "card",
        '"set"',
        "region_language",
        "region",
        "language",
        '"trigger"',
        "effect",
        "image",
        '"name"',
        "resword",
        "keyword",
        "format",
        "block",
        "color",
        "attribute",
        "tribe",
        "rarity",
        "artist",
        "card_type",
        "set_type",
    ]:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {tbl}"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
