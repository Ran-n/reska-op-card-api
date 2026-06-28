#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Add ON DELETE CASCADE to api_key_log.api_key_fk.

Revision ID: 0014_api_key_log_cascade
Revises: 0013_api_key_label_unique_active_only
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_api_key_log_cascade"
down_revision: str | Sequence[str] | None = "0013_api_key_label_unique_active_only"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_log_new (
            id          INTEGER PRIMARY KEY,
            ts          TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            api_key_fk  INTEGER NOT NULL REFERENCES api_key(id) ON DELETE CASCADE,
            method      TEXT NOT NULL,
            path        TEXT NOT NULL,
            status_code INTEGER NOT NULL
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_log_new SELECT id, ts, api_key_fk, method, path, status_code FROM api_key_log"))
    op.execute(sa.text("DROP TABLE api_key_log"))
    op.execute(sa.text("ALTER TABLE api_key_log_new RENAME TO api_key_log"))
    op.execute(sa.text("CREATE INDEX ix_api_key_log_key_ts ON api_key_log (api_key_fk, ts)"))


def downgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_log_new (
            id          INTEGER PRIMARY KEY,
            ts          TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            api_key_fk  INTEGER NOT NULL REFERENCES api_key(id),
            method      TEXT NOT NULL,
            path        TEXT NOT NULL,
            status_code INTEGER NOT NULL
        )
    """))
    op.execute(sa.text("INSERT INTO api_key_log_new SELECT id, ts, api_key_fk, method, path, status_code FROM api_key_log"))
    op.execute(sa.text("DROP TABLE api_key_log"))
    op.execute(sa.text("ALTER TABLE api_key_log_new RENAME TO api_key_log"))
    op.execute(sa.text("CREATE INDEX ix_api_key_log_key_ts ON api_key_log (api_key_fk, ts)"))
