#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Add api_key table for endpoint authentication.

Revision ID: 0008_api_keys
Revises: 0007_fix_naip_junction_fk
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_api_keys"
down_revision: str | Sequence[str] | None = "0007_fix_naip_junction_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = "TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))"


def upgrade() -> None:
    op.execute(
        sa.text(f"""
        CREATE TABLE api_key (
            id         INTEGER PRIMARY KEY,
            created_ts {_TS},
            key        TEXT NOT NULL,
            can_edit   INTEGER NOT NULL DEFAULT 0,
            label      TEXT,
            CONSTRAINT uq_api_key_key UNIQUE (key)
        )
        """)
    )
    op.execute(sa.text("CREATE UNIQUE INDEX ix_api_key_key ON api_key (key)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS api_key"))
