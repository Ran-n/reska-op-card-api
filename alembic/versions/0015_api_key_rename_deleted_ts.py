#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28

Rename api_key.deleted_ts to revoked_ts.

Revision ID: 0015_api_key_rename_deleted_ts
Revises: 0014_api_key_log_cascade
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_api_key_rename_deleted_ts"
down_revision: str | Sequence[str] | None = "0014_api_key_log_cascade"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE api_key RENAME COLUMN deleted_ts TO revoked_ts"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE api_key RENAME COLUMN revoked_ts TO deleted_ts"))
