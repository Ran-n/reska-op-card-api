#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/01 00:00:00.000000
Revised: 2026/06/01 00:00:00.000000

add print_variant table; card.rarity_fk; naip.print_variant_fk replaces naip.rarity_fk;
strip is_type/is_base from rarity; remove NFD rarity

Revision ID: 0003_print_variant
Revises: 0002_naip_is_foil
Create Date: 2026-06-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_print_variant"
down_revision: str | Sequence[str] | None = "0002_naip_is_foil"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"
_TS_EXPR = "strftime('%Y-%m-%d %H:%M:%f', 'now')"


def _trigger(table: str) -> str:
    return (
        f"CREATE TRIGGER trg_{table}_update AFTER UPDATE ON {table} "
        f"WHEN NEW.updated_ts IS OLD.updated_ts "
        f"BEGIN UPDATE {table} SET updated_ts = {_TS_EXPR} WHERE id = NEW.id; END"
    )


# Ordered parent-first so subquery lookups always resolve
_PRINT_VARIANTS = [
    ("STD", "Standard", None),
    ("AA", "Alternate Art", None),
    ("TR", "Treasure Rare", "AA"),
    ("SP", "Special Rare", "AA"),
    ("MR", "Manga Rare", "AA"),
    ("FA", "Full Art", "AA"),
    ("AUD", "Gold DON!! Rare", "AA"),
    ("PTR", "Pattern Rare", "AA"),
    ("MTR", "Metallic Rare", "AA"),
    ("GR", "Ghost Rare", "SP"),
    ("EMR", "Event Manga Rare", "MR"),
    ("RMR", "Red Manga Rare", "MR"),
    ("AU", "Gold Rare", "MTR"),
    ("AG", "Silver Rare", "MTR"),
]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # ── 1. print_variant table ────────────────────────────────────────────────
    conn.execute(
        sa.text(f"""
        CREATE TABLE print_variant (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     TEXT NOT NULL,
            name       TEXT NOT NULL,
            "desc"     TEXT,
            parent_fk  INTEGER REFERENCES print_variant(id)
        )
    """)
    )
    conn.execute(sa.text(_trigger("print_variant")))

    for symbol, name, parent_sym in _PRINT_VARIANTS:
        if parent_sym is None:
            conn.execute(
                sa.text("INSERT INTO print_variant (symbol, name) VALUES (:s, :n)"),
                {"s": symbol, "n": name},
            )
        else:
            conn.execute(
                sa.text(
                    "INSERT INTO print_variant (symbol, name, parent_fk) "
                    "VALUES (:s, :n, (SELECT id FROM print_variant WHERE symbol = :p))"
                ),
                {"s": symbol, "n": name, "p": parent_sym},
            )

    # ── 2. Rebuild rarity (drop is_type, is_base, remove NFD) ────────────────
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_rarity_update"))
    conn.execute(sa.text("ALTER TABLE rarity RENAME TO rarity_old"))
    conn.execute(
        sa.text(f"""
        CREATE TABLE rarity (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            updated_ts {_TS},
            symbol     TEXT NOT NULL,
            name       TEXT NOT NULL,
            "desc"     TEXT
        )
    """)
    )
    # Keep only base card rarities; move print-level finishes to print_variant
    _BASE_RARITIES = ("'C'", "'UC'", "'R'", "'SR'", "'SEC'", "'L'", "'P'", "'D'")
    conn.execute(
        sa.text(
            'INSERT INTO rarity SELECT id, created_ts, updated_ts, symbol, name, "desc" '
            f"FROM rarity_old WHERE symbol IN ({', '.join(_BASE_RARITIES)})"
        )
    )
    conn.execute(sa.text(_trigger("rarity")))
    conn.execute(sa.text("DROP TABLE rarity_old"))

    # ── 3. card.rarity_fk ────────────────────────────────────────────────────
    conn.execute(sa.text("ALTER TABLE card ADD COLUMN rarity_fk INTEGER REFERENCES rarity(id)"))
    conn.execute(sa.text("CREATE INDEX ix_card_rarity_fk ON card (rarity_fk)"))

    # ── 4. Rebuild naip (rarity_fk → print_variant_fk) ───────────────────────
    # Drop triggers that reference naip before rename — SQLite auto-updates
    # trigger bodies on rename, which would leave them referencing naip_old
    # after the old table is dropped.
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_update"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_insert"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_update"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_unique_print"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_one_default_per_card"))
    conn.execute(sa.text("ALTER TABLE naip RENAME TO naip_old"))

    conn.execute(
        sa.text(f"""
        CREATE TABLE naip (
            id               INTEGER PRIMARY KEY,
            created_ts       {_TS},
            updated_ts       {_TS},
            card_fk          INTEGER NOT NULL REFERENCES card(id),
            set_fk           INTEGER NOT NULL REFERENCES "set"(id),
            artist_fk        INTEGER REFERENCES artist(id),
            print_variant_fk INTEGER NOT NULL REFERENCES print_variant(id),
            name_fk          INTEGER REFERENCES name(id),
            image_fk         INTEGER REFERENCES image(id),
            effect_fk        INTEGER REFERENCES effect(id),
            trigger_fk       INTEGER REFERENCES "trigger"(id),
            is_default       INTEGER NOT NULL DEFAULT 0,
            is_errata        INTEGER NOT NULL DEFAULT 0,
            is_foil          INTEGER NOT NULL DEFAULT 0,
            sort_order       INTEGER,
            serial_max       INTEGER,
            cardtype_fk      INTEGER REFERENCES card_type(id),
            block_fk         INTEGER REFERENCES block(id),
            language_fk      INTEGER REFERENCES language(id),
            power            INTEGER,
            life             INTEGER,
            counter          INTEGER,
            cost             INTEGER
        )
    """)
    )
    conn.execute(
        sa.text(
            "INSERT INTO naip "
            "SELECT id, created_ts, updated_ts, card_fk, set_fk, artist_fk, "
            "(SELECT id FROM print_variant WHERE symbol = 'STD'), "
            "name_fk, image_fk, effect_fk, trigger_fk, is_default, is_errata, is_foil, "
            "sort_order, serial_max, cardtype_fk, block_fk, language_fk, "
            "power, life, counter, cost "
            "FROM naip_old"
        )
    )
    conn.execute(sa.text(_trigger("naip")))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1"))
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip "
            "(card_fk, set_fk, artist_fk, print_variant_fk, is_foil) "
            "WHERE artist_fk IS NOT NULL"
        )
    )
    conn.execute(sa.text("CREATE INDEX ix_naip_print_variant_fk ON naip (print_variant_fk)"))
    conn.execute(sa.text("DROP TABLE naip_old"))

    # Recreate naip_serial enforcement triggers (now referencing the new naip)
    conn.execute(
        sa.text("""
        CREATE TRIGGER trg_naip_serial_check_max_insert
        BEFORE INSERT ON naip_serial
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'serial_number exceeds serial_max for this naip')
            WHERE (SELECT serial_max FROM naip WHERE id = NEW.naip_fk) IS NOT NULL
            AND NEW.serial_number > (SELECT serial_max FROM naip WHERE id = NEW.naip_fk);
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
            WHERE (SELECT serial_max FROM naip WHERE id = NEW.naip_fk) IS NOT NULL
            AND NEW.serial_number > (SELECT serial_max FROM naip WHERE id = NEW.naip_fk);
        END
    """)
    )

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # ── 1. Restore naip (print_variant_fk → rarity_fk NULL) ──────────────────
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_update"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_insert"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_naip_serial_check_max_update"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_unique_print"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_one_default_per_card"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_print_variant_fk"))
    conn.execute(sa.text("ALTER TABLE naip RENAME TO naip_old"))

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
            name_fk     INTEGER REFERENCES name(id),
            image_fk    INTEGER REFERENCES image(id),
            effect_fk   INTEGER REFERENCES effect(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            is_default  INTEGER NOT NULL DEFAULT 0,
            is_errata   INTEGER NOT NULL DEFAULT 0,
            is_foil     INTEGER NOT NULL DEFAULT 0,
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
    conn.execute(
        sa.text(
            "INSERT INTO naip "
            "SELECT id, created_ts, updated_ts, card_fk, set_fk, artist_fk, "
            "NULL, "  # rarity_fk — not recoverable from print_variant_fk
            "name_fk, image_fk, effect_fk, trigger_fk, is_default, is_errata, is_foil, "
            "sort_order, serial_max, cardtype_fk, block_fk, language_fk, "
            "power, life, counter, cost "
            "FROM naip_old"
        )
    )
    conn.execute(sa.text(_trigger("naip")))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_naip_one_default_per_card ON naip (card_fk) WHERE is_default = 1"))
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip "
            "(card_fk, set_fk, artist_fk, rarity_fk, is_foil) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
        )
    )
    conn.execute(sa.text("DROP TABLE naip_old"))

    # Recreate naip_serial enforcement triggers (now referencing the restored naip)
    conn.execute(
        sa.text("""
        CREATE TRIGGER trg_naip_serial_check_max_insert
        BEFORE INSERT ON naip_serial
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'serial_number exceeds serial_max for this naip')
            WHERE (SELECT serial_max FROM naip WHERE id = NEW.naip_fk) IS NOT NULL
            AND NEW.serial_number > (SELECT serial_max FROM naip WHERE id = NEW.naip_fk);
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
            WHERE (SELECT serial_max FROM naip WHERE id = NEW.naip_fk) IS NOT NULL
            AND NEW.serial_number > (SELECT serial_max FROM naip WHERE id = NEW.naip_fk);
        END
    """)
    )

    # ── 2. Remove card.rarity_fk (rebuild card — SQLite can't drop columns) ───
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_card_update"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_rarity_fk"))
    conn.execute(sa.text("ALTER TABLE card RENAME TO card_old"))
    conn.execute(
        sa.text(f"""
        CREATE TABLE card (
            id          INTEGER PRIMARY KEY,
            created_ts  {_TS},
            updated_ts  {_TS},
            set_fk      INTEGER NOT NULL REFERENCES "set"(id),
            cardtype_fk INTEGER NOT NULL REFERENCES card_type(id),
            name_fk     INTEGER NOT NULL REFERENCES name(id),
            effect_fk   INTEGER REFERENCES effect(id),
            trigger_fk  INTEGER REFERENCES "trigger"(id),
            block_fk    INTEGER REFERENCES block(id),
            number      INTEGER NOT NULL,
            power       INTEGER,
            life        INTEGER,
            counter     INTEGER,
            cost        INTEGER
        )
    """)
    )
    conn.execute(
        sa.text(
            "INSERT INTO card "
            "SELECT id, created_ts, updated_ts, set_fk, cardtype_fk, name_fk, "
            "effect_fk, trigger_fk, block_fk, number, power, life, counter, cost "
            "FROM card_old"
        )
    )
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_set_number"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_cardtype_fk"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_name_fk"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_card_set_fk"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_card_set_number ON card (set_fk, number)"))
    conn.execute(sa.text("CREATE INDEX ix_card_cardtype_fk ON card (cardtype_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_name_fk ON card (name_fk)"))
    conn.execute(sa.text("CREATE INDEX ix_card_set_fk ON card (set_fk)"))
    conn.execute(sa.text(_trigger("card")))
    conn.execute(sa.text("DROP TABLE card_old"))

    # ── 3. Restore rarity (add is_type, is_base, restore NFD) ────────────────
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_rarity_update"))
    conn.execute(sa.text("ALTER TABLE rarity RENAME TO rarity_old"))
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
        sa.text('INSERT INTO rarity SELECT id, created_ts, updated_ts, symbol, name, "desc", 0, 0 FROM rarity_old')
    )
    # Restore rows that were moved to print_variant (is_type/is_base cannot be recovered, default 0)
    for sym, name in [
        ("TR", "Treasure Rare"),
        ("AA", "Alternate Art"),
        ("SP", "Special Rare"),
        ("MR", "Manga Rare"),
        ("FA", "Full Art"),
        ("AU", "Gold Rare"),
        ("AG", "Silver Rare"),
        ("AUD", "Gold DON!! Rare"),
        ("EMR", "Event Manga Rare"),
        ("PTR", "Pattern Rare"),
        ("NFD", "Non-Foil DON!!"),
    ]:
        conn.execute(
            sa.text("INSERT INTO rarity (symbol, name, is_type, is_base) VALUES (:s, :n, 0, 0)"),
            {"s": sym, "n": name},
        )
    conn.execute(sa.text(_trigger("rarity")))
    conn.execute(sa.text("DROP TABLE rarity_old"))

    # ── 4. Drop print_variant ─────────────────────────────────────────────────
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_print_variant_update"))
    conn.execute(sa.text("DROP TABLE IF EXISTS print_variant"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
