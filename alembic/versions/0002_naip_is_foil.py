#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/29 00:00:00.000000
Revised: 2026/05/29 00:00:00.000000

add naip.is_foil; remove FD (Foil DON!! Rare) rarity

Revision ID: 0002_naip_is_foil
Revises: 0001_initial
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_naip_is_foil"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # 0001_initial was squashed to already include is_foil — skip if present
    existing_cols = [row[1] for row in conn.execute(sa.text("PRAGMA table_info(naip)")).fetchall()]
    if "is_foil" not in existing_cols:
        conn.execute(sa.text("ALTER TABLE naip ADD COLUMN is_foil INTEGER NOT NULL DEFAULT 0"))

        conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_unique_print"))
        conn.execute(
            sa.text(
                "CREATE UNIQUE INDEX ix_naip_unique_print ON naip (card_fk, set_fk, artist_fk, rarity_fk, is_foil) "
                "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
            )
        )

    conn.execute(sa.text("DELETE FROM rarity WHERE symbol = 'FD'"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # Restore FD rarity
    conn.execute(sa.text("INSERT INTO rarity (symbol, name, is_type, is_base) VALUES ('FD', 'Foil DON!! Rare', 0, 0)"))

    # Restore old index (without is_foil)
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_naip_unique_print"))
    conn.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_naip_unique_print ON naip (card_fk, set_fk, artist_fk, rarity_fk) "
            "WHERE artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"
        )
    )

    # SQLite can't drop columns — rebuild naip without is_foil
    conn.execute(sa.text("ALTER TABLE naip RENAME TO naip_old"))
    conn.execute(
        sa.text("""
        CREATE TABLE naip AS SELECT
            id, created_ts, updated_ts, card_fk, set_fk, artist_fk, rarity_fk,
            name_fk, image_fk, effect_fk, trigger_fk, is_default, is_errata,
            sort_order, serial_max, cardtype_fk, block_fk, language_fk,
            power, life, counter, cost
        FROM naip_old
    """)
    )
    conn.execute(sa.text("DROP TABLE naip_old"))

    conn.execute(sa.text("PRAGMA foreign_keys = ON"))
