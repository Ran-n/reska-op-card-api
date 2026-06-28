#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Add deleted_ts to api_key for soft-delete support.

Revision ID: 0012_api_key_soft_delete
Revises: 0011_api_key_log
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_api_key_soft_delete"
down_revision: str | Sequence[str] | None = "0011_api_key_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE api_key ADD COLUMN deleted_ts TEXT"))


def downgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_new (
            id             INTEGER PRIMARY KEY,
            created_ts     TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            key            TEXT NOT NULL,
            can_edit       INTEGER NOT NULL DEFAULT 0,
            label          TEXT NOT NULL,
            request_count  INTEGER NOT NULL DEFAULT 0,
            last_used_ts   TEXT,
            CONSTRAINT uq_api_key_key   UNIQUE (key),
            CONSTRAINT uq_api_key_label UNIQUE (label)
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_new SELECT id, created_ts, key, can_edit, label, request_count, last_used_ts FROM api_key"))
    op.execute(sa.text("DROP TABLE api_key"))
    op.execute(sa.text("ALTER TABLE api_key_new RENAME TO api_key"))
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_key ON api_key (key)"))
