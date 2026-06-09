#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/08 12:44:38.470939
Revised: 2026/06/08 12:44:38.470939

add missing FK indexes for set, card, naip, print_variant, and history tables

Revision ID: 0006_add_missing_indexes
Revises: 0005_language_images
Create Date: 2026-06-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_add_missing_indexes"
down_revision: str | Sequence[str] | None = "0005_language_images"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_INDEXES = [
    # set
    ("ix_set_type_fk", '"set"', "type_fk"),
    ("ix_set_language_fk", '"set"', "language_fk"),
    # card
    ("ix_card_effect_fk", "card", "effect_fk"),
    ("ix_card_trigger_fk", "card", "trigger_fk"),
    ("ix_card_block_fk", "card", "block_fk"),
    # naip
    ("ix_naip_card_fk", "naip", "card_fk"),
    ("ix_naip_set_fk", "naip", "set_fk"),
    ("ix_naip_artist_fk", "naip", "artist_fk"),
    ("ix_naip_language_fk", "naip", "language_fk"),
    ("ix_naip_cardtype_fk", "naip", "cardtype_fk"),
    ("ix_naip_block_fk", "naip", "block_fk"),
    # print_variant
    ("ix_print_variant_parent_fk", "print_variant", "parent_fk"),
    # card_effect_history
    ("ix_card_effect_history_card_fk", "card_effect_history", "card_fk"),
    ("ix_card_effect_history_effect_fk", "card_effect_history", "effect_fk"),
    # card_trigger_history
    ("ix_card_trigger_history_card_fk", "card_trigger_history", "card_fk"),
    ("ix_card_trigger_history_trigger_fk", "card_trigger_history", "trigger_fk"),
]


def upgrade() -> None:
    conn = op.get_bind()
    existing = {row[0] for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index'"))}
    for name, table, col in _NEW_INDEXES:
        if name not in existing:
            conn.execute(sa.text(f"CREATE INDEX {name} ON {table} ({col})"))


def downgrade() -> None:
    conn = op.get_bind()
    existing = {row[0] for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index'"))}
    for name, _table, _col in _NEW_INDEXES:
        if name in existing:
            conn.execute(sa.text(f"DROP INDEX {name}"))
