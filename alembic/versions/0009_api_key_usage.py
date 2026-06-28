#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Add request_count and last_used_ts to api_key.

Revision ID: 0009_api_key_usage
Revises: 0008_api_keys
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_api_key_usage"
down_revision: str | Sequence[str] | None = "0008_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE api_key ADD COLUMN request_count INTEGER NOT NULL DEFAULT 0"))
    op.execute(sa.text("ALTER TABLE api_key ADD COLUMN last_used_ts TEXT"))


def downgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_new (
            id         INTEGER PRIMARY KEY,
            created_ts TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            key        TEXT NOT NULL,
            can_edit   INTEGER NOT NULL DEFAULT 0,
            label      TEXT,
            CONSTRAINT uq_api_key_key UNIQUE (key)
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_new SELECT id, created_ts, key, can_edit, label FROM api_key"))
    op.execute(sa.text("DROP TABLE api_key"))
    op.execute(sa.text("ALTER TABLE api_key_new RENAME TO api_key"))
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_key ON api_key (key)"))
