"""merge heads

Revision ID: 64e15548d39c
Revises: 1fd7a3fc10a0, 9734af8b92e1
Create Date: 2025-04-17 13:01:23.114817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64e15548d39c'
down_revision: Union[str, None] = ('1fd7a3fc10a0', '9734af8b92e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
