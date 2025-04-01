"""Fix enum values mismatch

Revision ID: fce74a1b62d3
Revises: ba93ceb4d658
Create Date: 2025-03-29 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fce74a1b62d3"
down_revision: Union[str, None] = "ba93ceb4d658"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add lowercase values to existing PostgreSQL enums."""
    # First check if the enum values already exist
    conn = op.get_bind()

    # 1. Update experimentstatus enum to include lowercase values
    # In PostgreSQL, adding values to an enum is safe and doesn't require data migration
    op.execute("ALTER TYPE experimentstatus ADD VALUE IF NOT EXISTS 'draft'")
    op.execute("ALTER TYPE experimentstatus ADD VALUE IF NOT EXISTS 'active'")
    op.execute("ALTER TYPE experimentstatus ADD VALUE IF NOT EXISTS 'paused'")
    op.execute("ALTER TYPE experimentstatus ADD VALUE IF NOT EXISTS 'completed'")
    op.execute("ALTER TYPE experimentstatus ADD VALUE IF NOT EXISTS 'archived'")

    # Fix experimenttype enum by adding lowercase values
    op.execute("ALTER TYPE experimenttype ADD VALUE IF NOT EXISTS 'a_b'")
    op.execute("ALTER TYPE experimenttype ADD VALUE IF NOT EXISTS 'mv'")
    op.execute("ALTER TYPE experimenttype ADD VALUE IF NOT EXISTS 'split_url'")
    op.execute("ALTER TYPE experimenttype ADD VALUE IF NOT EXISTS 'bandit'")

    # Fix metrictype enum by adding lowercase values
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'conversion'")
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'revenue'")
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'count'")
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'duration'")
    op.execute("ALTER TYPE metrictype ADD VALUE IF NOT EXISTS 'custom'")


def downgrade() -> None:
    """
    Unfortunately, PostgreSQL doesn't allow removing enum values.
    If a downgrade is needed, you'd need to create new enum types
    without the added values and migrate the data.
    """
    # Cannot remove values from an existing enum in PostgreSQL
    # This would require creating new types and migrating data
    pass
