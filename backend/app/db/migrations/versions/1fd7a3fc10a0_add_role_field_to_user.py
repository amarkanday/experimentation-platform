"""add_role_field_to_user

Revision ID: 1fd7a3fc10a0
Revises: fce74a1b62d3
Create Date: 2025-04-12 14:35:47.047829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fd7a3fc10a0'
down_revision: Union[str, None] = 'fce74a1b62d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the UserRole enum type
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'analyst', 'developer', 'viewer')")

    # Add role column to users table with default value 'viewer'
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum('admin', 'analyst', 'developer', 'viewer', name='userrole'),
            nullable=False,
            server_default='viewer'
        ),
        schema='experimentation'
    )


def downgrade() -> None:
    # Drop the role column
    op.drop_column('users', 'role', schema='experimentation')

    # Drop the UserRole enum type
    op.execute("DROP TYPE userrole")
