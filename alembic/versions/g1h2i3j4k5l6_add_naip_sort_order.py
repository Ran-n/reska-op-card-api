"""add naip.sort_order

Revision ID: g1h2i3j4k5l6
Revises: d5e6f7a8b9c0
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('naip', sa.Column('sort_order', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('naip', 'sort_order')
