"""Initial roles and permissions

Revision ID: 001_initial_roles
Create Date: 2024-04-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.app.core.permissions import UserRole, ResourceType, Action, DEFAULT_ROLE_PERMISSIONS
from backend.app.core.database_config import get_schema_name

# revision identifiers, used by Alembic
revision = '001_initial_roles'
down_revision = None
branch_labels = None
depends_on = None

schema_name = get_schema_name()

def upgrade() -> None:
    # Create roles
    roles = []
    for role in UserRole:
        roles.append({
            'id': uuid.uuid4(),
            'name': role.value,
            'description': f"Default {role.value} role",
            'created_at': sa.func.now(),
            'updated_at': sa.func.now()
        })

    op.bulk_insert(
        sa.Table(
            'roles',
            sa.MetaData(),
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(50)),
            sa.Column('description', sa.String(255)),
            sa.Column('created_at', sa.DateTime),
            sa.Column('updated_at', sa.DateTime),
            schema=schema_name
        ),
        roles
    )

    # Create permissions
    permissions = []
    for resource in ResourceType:
        for action in Action:
            permissions.append({
                'id': uuid.uuid4(),
                'name': f"{resource.value}:{action.value}",
                'description': f"Permission to {action.value} {resource.value}",
                'resource': resource.value,
                'action': action.value,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now()
            })

    op.bulk_insert(
        sa.Table(
            'permissions',
            sa.MetaData(),
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(50)),
            sa.Column('description', sa.String(255)),
            sa.Column('resource', sa.String(50)),
            sa.Column('action', sa.String(50)),
            sa.Column('created_at', sa.DateTime),
            sa.Column('updated_at', sa.DateTime),
            schema=schema_name
        ),
        permissions
    )

def downgrade() -> None:
    # Remove all permissions and roles
    op.execute(f'DELETE FROM {schema_name}.permissions')
    op.execute(f'DELETE FROM {schema_name}.roles')
