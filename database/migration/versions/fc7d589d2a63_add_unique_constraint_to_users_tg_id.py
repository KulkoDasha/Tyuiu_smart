"""add unique constraint to users.tg_id

Revision ID: fc7d589d2a63
Revises: bd138fad1463
Create Date: 2026-01-12 13:30:18.812982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc7d589d2a63'
down_revision: Union[str, None] = 'bd138fad1463'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_users_tg_id', 'users', ['tg_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_tg_id', 'users', type_='unique')
