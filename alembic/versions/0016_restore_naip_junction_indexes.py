#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/30

Restore FK indexes on naip_color/tribe/attribute/keyword/resword/serial that
were silently dropped by 0007_fix_naip_junction_fk's CREATE TABLE rebuild
(the rebuild's raw CREATE TABLE statements never recreated the indexes that
0001_initial had originally created on these tables).

Revision ID: 0016_restore_naip_junction_indexes
Revises: 0015_api_key_rename_deleted_ts
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_restore_naip_junction_indexes"
down_revision: str | Sequence[str] | None = "0015_api_key_rename_deleted_ts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_INDEXES = [
    ("ix_naip_color_naip_fk", "naip_color", "naip_fk"),
    ("ix_naip_color_color_fk", "naip_color", "color_fk"),
    ("ix_naip_tribe_naip_fk", "naip_tribe", "naip_fk"),
    ("ix_naip_tribe_tribe_fk", "naip_tribe", "tribe_fk"),
    ("ix_naip_attribute_naip_fk", "naip_attribute", "naip_fk"),
    ("ix_naip_attribute_attribute_fk", "naip_attribute", "attribute_fk"),
    ("ix_naip_keyword_naip_fk", "naip_keyword", "naip_fk"),
    ("ix_naip_keyword_keyword_fk", "naip_keyword", "keyword_fk"),
    ("ix_naip_resword_naip_fk", "naip_resword", "naip_fk"),
    ("ix_naip_resword_resword_fk", "naip_resword", "resword_fk"),
    ("ix_naip_serial_naip_fk", "naip_serial", "naip_fk"),
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
