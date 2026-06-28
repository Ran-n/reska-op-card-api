#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Add api_key_log table for per-request access logging.

Revision ID: 0011_api_key_log
Revises: 0010_api_key_label_required_unique
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_api_key_log"
down_revision: str | Sequence[str] | None = "0010_api_key_label_required_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE api_key_log (
            id          INTEGER PRIMARY KEY,
            ts          TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            api_key_fk  INTEGER NOT NULL REFERENCES api_key(id),
            method      TEXT NOT NULL,
            path        TEXT NOT NULL,
            status_code INTEGER NOT NULL
        )
    """))
    op.execute(sa.text("CREATE INDEX ix_api_key_log_key_ts ON api_key_log (api_key_fk, ts)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE api_key_log"))
