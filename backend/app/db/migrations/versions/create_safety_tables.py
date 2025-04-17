"""Create safety monitoring tables

Revision ID: 9734af8b92e1
Revises: e45a2f9c8d21
Create Date: 2023-11-25 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '9734af8b92e1'
down_revision = 'e45a2f9c8d21'  # Reference to the previous migration
branch_labels = None
depends_on = None

# Schema name
schema = "experimentation"


def upgrade() -> None:
    # Create enum type for rollback trigger types
    op.execute(
        f"CREATE TYPE {schema}.rollbacktriggertype AS ENUM "
        "('error_rate', 'latency', 'manual', 'automatic', 'scheduled', 'custom_metric')"
    )

    # Create safety settings table
    op.create_table(
        'safety_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('enable_automatic_rollbacks', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('default_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema=schema
    )

    # Create feature flag safety config table
    op.create_table(
        'feature_flag_safety_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('rollback_percentage', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema}.feature_flags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema
    )
    op.create_index(
        f'{schema}_safety_config_feature_flag_id_idx',
        'feature_flag_safety_configs',
        ['feature_flag_id'],
        unique=True,
        schema=schema
    )

    # Create safety rollback records table
    op.create_table(
        'safety_rollback_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('safety_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('trigger_reason', sa.Text(), nullable=False),
        sa.Column('previous_percentage', sa.Integer(), nullable=False),
        sa.Column('target_percentage', sa.Integer(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('executed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema}.feature_flags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['safety_config_id'], [f'{schema}.feature_flag_safety_configs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['executed_by_user_id'], [f'{schema}.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema
    )
    op.create_index(
        f'{schema}_rollback_feature_flag_id_idx',
        'safety_rollback_records',
        ['feature_flag_id'],
        schema=schema
    )
    op.create_index(
        f'{schema}_rollback_created_at_idx',
        'safety_rollback_records',
        ['created_at'],
        schema=schema
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('safety_rollback_records', schema=schema)
    op.drop_table('feature_flag_safety_configs', schema=schema)
    op.drop_table('safety_settings', schema=schema)

    # Drop enum type
    op.execute(f"DROP TYPE IF EXISTS {schema}.rollbacktriggertype")
