"""rename naip.desc to effect and add naip.trigger

Revision ID: c3f8a1d92e74
Revises: 681d524342bf
Create Date: 2026-05-14 18:43:58.256165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f8a1d92e74'
down_revision: Union[str, Sequence[str], None] = '681d524342bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('naip') as batch_op:
        batch_op.alter_column('desc', new_column_name='effect')
        batch_op.add_column(sa.Column('trigger', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('naip') as batch_op:
        batch_op.drop_column('trigger')
        batch_op.alter_column('effect', new_column_name='desc')
