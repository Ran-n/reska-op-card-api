#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Scope the label uniqueness constraint to active (non-deleted) keys only.

Replaces the table-level UNIQUE(label) with a partial unique index
WHERE deleted_ts IS NULL, so a revoked label can be reused.

Revision ID: 0013_api_key_label_unique_active_only
Revises: 0012_api_key_soft_delete
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_api_key_label_unique_active_only"
down_revision: str | Sequence[str] | None = "0012_api_key_soft_delete"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_new (
            id             INTEGER PRIMARY KEY,
            created_ts     TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            key            TEXT NOT NULL,
            can_edit       INTEGER NOT NULL DEFAULT 0,
            label          TEXT NOT NULL,
            request_count  INTEGER NOT NULL DEFAULT 0,
            last_used_ts   TEXT,
            deleted_ts     TEXT,
            CONSTRAINT uq_api_key_key UNIQUE (key)
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_new SELECT id, created_ts, key, can_edit, label, request_count, last_used_ts, deleted_ts FROM api_key"))
    op.execute(sa.text("DROP TABLE api_key"))
    op.execute(sa.text("ALTER TABLE api_key_new RENAME TO api_key"))
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_key ON api_key (key)"))
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_label_active ON api_key (label) WHERE deleted_ts IS NULL"))


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
            deleted_ts     TEXT,
            CONSTRAINT uq_api_key_key   UNIQUE (key),
            CONSTRAINT uq_api_key_label UNIQUE (label)
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_new SELECT id, created_ts, key, can_edit, label, request_count, last_used_ts, deleted_ts FROM api_key"))
    op.execute(sa.text("DROP TABLE api_key"))
    op.execute(sa.text("ALTER TABLE api_key_new RENAME TO api_key"))
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_key ON api_key (key)"))
