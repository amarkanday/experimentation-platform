"""Add rollout schedules tables.

Revision ID: add_rollout_schedules
Revises: add_reports_table
Create Date: 2023-11-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_rollout_schedules'
down_revision = 'add_reports_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for rollout schedules and rollout stages.

    This creates the tables needed for gradual feature flag rollout schedules:
    - rollout_schedules: Main table for rollout schedules
    - rollout_stages: Table for stages within a rollout schedule
    """
    schema_name = 'experimentation'

    # Create enum types
    trigger_type = sa.Enum('time_based', 'metric_based', 'manual', name='triggertype')
    op.create_type('triggertype', schema='experimentation', create_type=False,
                  values=['time_based', 'metric_based', 'manual'])

    rollout_stage_status = sa.Enum('pending', 'in_progress', 'completed', 'failed',
                                 name='rolloutstagesstatus')
    op.create_type('rolloutstagesstatus', schema='experimentation', create_type=False,
                  values=['pending', 'in_progress', 'completed', 'failed'])

    rollout_schedule_status = sa.Enum('draft', 'active', 'paused', 'completed', 'cancelled',
                                    name='rolloutschedulestatus')
    op.create_type('rolloutschedulestatus', schema='experimentation', create_type=False,
                  values=['draft', 'active', 'paused', 'completed', 'cancelled'])

    # Create rollout_schedules table
    op.create_table(
        'rollout_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'completed', 'cancelled',
                                   name='rolloutschedulestatus', schema=schema_name),
                 nullable=False, default='draft'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('config_data', postgresql.JSONB(), nullable=True),
        sa.Column('max_percentage', sa.Integer(), nullable=True, default=100),
        sa.Column('min_stage_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema_name}.feature_flags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], [f'{schema_name}.users.id'], ondelete='SET NULL'),
        sa.CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date > start_date', name='check_rollout_schedule_dates'),
        sa.CheckConstraint('max_percentage >= 0 AND max_percentage <= 100', name='check_max_percentage'),
        schema=schema_name
    )

    # Create indexes for rollout_schedules
    op.create_index(
        f'{schema_name}_rollout_schedule_flag_status',
        'rollout_schedules',
        ['feature_flag_id', 'status'],
        schema=schema_name
    )
    op.create_index(
        op.f('ix_experimentation_rollout_schedules_status'),
        'rollout_schedules',
        ['status'],
        schema=schema_name
    )

    # Create rollout_stages table
    op.create_table(
        'rollout_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('rollout_schedule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('target_percentage', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed',
                                   name='rolloutstagesstatus', schema=schema_name),
                 nullable=False, default='pending'),
        sa.Column('trigger_type', sa.Enum('time_based', 'metric_based', 'manual',
                                        name='triggertype', schema=schema_name),
                 nullable=False),
        sa.Column('trigger_configuration', postgresql.JSONB(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('completed_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['rollout_schedule_id'], [f'{schema_name}.rollout_schedules.id'], ondelete='CASCADE'),
        sa.CheckConstraint('target_percentage >= 0 AND target_percentage <= 100', name='check_target_percentage'),
        schema=schema_name
    )

    # Create indexes for rollout_stages
    op.create_index(
        f'{schema_name}_rollout_stage_schedule',
        'rollout_stages',
        ['rollout_schedule_id', 'stage_order'],
        schema=schema_name
    )


def downgrade() -> None:
    """
    Remove rollout schedule tables.
    """
    schema_name = 'experimentation'

    # Drop tables
    op.drop_table('rollout_stages', schema=schema_name)
    op.drop_table('rollout_schedules', schema=schema_name)

    # Drop enum types
    op.drop_type('triggertype', schema='experimentation')
    op.drop_type('rolloutstagesstatus', schema='experimentation')
    op.drop_type('rolloutschedulestatus', schema='experimentation')
