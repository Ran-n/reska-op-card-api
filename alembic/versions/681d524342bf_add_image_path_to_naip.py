"""add image_path to naip

Revision ID: 681d524342bf
Revises: a22f8db88250
Create Date: 2026-05-13 10:24:58.573118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '681d524342bf'
down_revision: Union[str, Sequence[str], None] = 'a22f8db88250'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('naip', sa.Column('image_path', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('naip', 'image_path')
