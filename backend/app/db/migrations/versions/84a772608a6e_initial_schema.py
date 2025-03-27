"""Initial schema

Revision ID: 84a772608a6e
Revises:
Create Date: 2025-03-25 11:04:28.232177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '84a772608a6e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Create schema first
    op.execute('CREATE SCHEMA IF NOT EXISTS experimentation')
    op.create_table('permissions',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('resource', sa.String(length=50), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index(op.f('ix_experimentation_permissions_created_at'), 'permissions', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_permissions_name'), 'permissions', ['name'], unique=True, schema='experimentation')
    op.create_index(op.f('ix_experimentation_permissions_resource'), 'permissions', ['resource'], unique=False, schema='experimentation')
    op.create_table('roles',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index(op.f('ix_experimentation_roles_created_at'), 'roles', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_roles_name'), 'roles', ['name'], unique=True, schema='experimentation')
    op.create_table('users',
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index(op.f('ix_experimentation_users_created_at'), 'users', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_users_email'), 'users', ['email'], unique=True, schema='experimentation')
    op.create_index(op.f('ix_experimentation_users_username'), 'users', ['username'], unique=True, schema='experimentation')
    op.create_table('experiments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('hypothesis', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED', name='experimentstatus'), nullable=False),
    sa.Column('experiment_type', sa.Enum('A_B', 'MULTIVARIATE', 'SPLIT_URL', 'BANDIT', name='experimenttype'), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('targeting_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date > start_date', name='check_experiment_dates'),
    sa.ForeignKeyConstraint(['owner_id'], ['experimentation.users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_experiment_owner_status', 'experiments', ['owner_id', 'status'], unique=False, schema='experimentation')
    op.create_index('idx_experiment_status_dates', 'experiments', ['status', 'start_date', 'end_date'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_experiments_created_at'), 'experiments', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_experiments_id'), 'experiments', ['id'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_experiments_status'), 'experiments', ['status'], unique=False, schema='experimentation')
    op.create_table('feature_flags',
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('INACTIVE', 'ACTIVE', name='featureflagstatus'), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=True),
    sa.Column('targeting_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rollout_percentage', sa.Integer(), nullable=False),
    sa.Column('variants', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('rollout_percentage >= 0 AND rollout_percentage <= 100', name='check_rollout_percentage'),
    sa.ForeignKeyConstraint(['owner_id'], ['experimentation.users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_feature_flag_owner_status', 'feature_flags', ['owner_id', 'status'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_feature_flags_created_at'), 'feature_flags', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_feature_flags_key'), 'feature_flags', ['key'], unique=True, schema='experimentation')
    op.create_index(op.f('ix_experimentation_feature_flags_status'), 'feature_flags', ['status'], unique=False, schema='experimentation')
    op.create_table('role_permission_association',
    sa.Column('role_id', sa.UUID(), nullable=False),
    sa.Column('permission_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['experimentation.permissions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['experimentation.roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_table('user_role_association',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('role_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['experimentation.roles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['experimentation.users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_table('feature_flag_overrides',
    sa.Column('feature_flag_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['feature_flag_id'], ['experimentation.feature_flags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_override_feature_user', 'feature_flag_overrides', ['feature_flag_id', 'user_id'], unique=True, schema='experimentation')
    op.create_index(op.f('ix_experimentation_feature_flag_overrides_created_at'), 'feature_flag_overrides', ['created_at'], unique=False, schema='experimentation')
    op.create_table('metrics',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('event_name', sa.String(length=100), nullable=False),
    sa.Column('metric_type', sa.Enum('CONVERSION', 'REVENUE', 'COUNT', 'DURATION', 'CUSTOM', name='metrictype'), nullable=False),
    sa.Column('is_primary', sa.Boolean(), nullable=True),
    sa.Column('aggregation_method', sa.String(length=50), nullable=True),
    sa.Column('minimum_sample_size', sa.Integer(), nullable=True),
    sa.Column('expected_effect', sa.Float(), nullable=True),
    sa.Column('event_value_path', sa.String(length=100), nullable=True),
    sa.Column('lower_is_better', sa.Boolean(), nullable=True),
    sa.Column('experiment_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experimentation.experiments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_metric_experiment_event', 'metrics', ['experiment_id', 'event_name'], unique=False, schema='experimentation')
    op.create_index('idx_metric_experiment_name', 'metrics', ['experiment_id', 'name'], unique=True, schema='experimentation')
    op.create_index(op.f('ix_experimentation_metrics_created_at'), 'metrics', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_metrics_event_name'), 'metrics', ['event_name'], unique=False, schema='experimentation')
    op.create_table('variants',
    sa.Column('experiment_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_control', sa.Boolean(), nullable=True),
    sa.Column('traffic_allocation', sa.Integer(), nullable=True),
    sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('traffic_allocation >= 0 AND traffic_allocation <= 100', name='check_traffic_allocation'),
    sa.ForeignKeyConstraint(['experiment_id'], ['experimentation.experiments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_variant_experiment', 'variants', ['experiment_id'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_variants_created_at'), 'variants', ['created_at'], unique=False, schema='experimentation')
    op.create_table('assignments',
    sa.Column('experiment_id', sa.UUID(), nullable=False),
    sa.Column('variant_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experimentation.experiments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['variant_id'], ['experimentation.variants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_assignment_experiment_user', 'assignments', ['experiment_id', 'user_id'], unique=True, schema='experimentation')
    op.create_index('idx_assignment_user', 'assignments', ['user_id'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_assignments_created_at'), 'assignments', ['created_at'], unique=False, schema='experimentation')
    op.create_table('events',
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('experiment_id', sa.UUID(), nullable=True),
    sa.Column('feature_flag_id', sa.UUID(), nullable=True),
    sa.Column('variant_id', sa.UUID(), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experimentation.experiments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['feature_flag_id'], ['experimentation.feature_flags.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['variant_id'], ['experimentation.variants.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    schema='experimentation'
    )
    op.create_index('idx_event_experiment_timestamp', 'events', ['experiment_id', 'created_at'], unique=False, schema='experimentation')
    op.create_index('idx_event_experiment_type', 'events', ['experiment_id', 'event_type'], unique=False, schema='experimentation')
    op.create_index('idx_event_feature_flag_type', 'events', ['feature_flag_id', 'event_type'], unique=False, schema='experimentation')
    op.create_index('idx_event_user_type', 'events', ['user_id', 'event_type'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_events_created_at'), 'events', ['created_at'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_events_event_type'), 'events', ['event_type'], unique=False, schema='experimentation')
    op.create_index(op.f('ix_experimentation_events_user_id'), 'events', ['user_id'], unique=False, schema='experimentation')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_experimentation_events_user_id'), table_name='events', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_events_event_type'), table_name='events', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_events_created_at'), table_name='events', schema='experimentation')
    op.drop_index('idx_event_user_type', table_name='events', schema='experimentation')
    op.drop_index('idx_event_feature_flag_type', table_name='events', schema='experimentation')
    op.drop_index('idx_event_experiment_type', table_name='events', schema='experimentation')
    op.drop_index('idx_event_experiment_timestamp', table_name='events', schema='experimentation')
    op.drop_table('events', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_assignments_created_at'), table_name='assignments', schema='experimentation')
    op.drop_index('idx_assignment_user', table_name='assignments', schema='experimentation')
    op.drop_index('idx_assignment_experiment_user', table_name='assignments', schema='experimentation')
    op.drop_table('assignments', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_variants_created_at'), table_name='variants', schema='experimentation')
    op.drop_index('idx_variant_experiment', table_name='variants', schema='experimentation')
    op.drop_table('variants', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_metrics_event_name'), table_name='metrics', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_metrics_created_at'), table_name='metrics', schema='experimentation')
    op.drop_index('idx_metric_experiment_name', table_name='metrics', schema='experimentation')
    op.drop_index('idx_metric_experiment_event', table_name='metrics', schema='experimentation')
    op.drop_table('metrics', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_feature_flag_overrides_created_at'), table_name='feature_flag_overrides', schema='experimentation')
    op.drop_index('idx_override_feature_user', table_name='feature_flag_overrides', schema='experimentation')
    op.drop_table('feature_flag_overrides', schema='experimentation')
    op.drop_table('user_role_association')
    op.drop_table('role_permission_association')
    op.drop_index(op.f('ix_experimentation_feature_flags_status'), table_name='feature_flags', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_feature_flags_key'), table_name='feature_flags', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_feature_flags_created_at'), table_name='feature_flags', schema='experimentation')
    op.drop_index('idx_feature_flag_owner_status', table_name='feature_flags', schema='experimentation')
    op.drop_table('feature_flags', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_experiments_status'), table_name='experiments', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_experiments_id'), table_name='experiments', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_experiments_created_at'), table_name='experiments', schema='experimentation')
    op.drop_index('idx_experiment_status_dates', table_name='experiments', schema='experimentation')
    op.drop_index('idx_experiment_owner_status', table_name='experiments', schema='experimentation')
    op.drop_table('experiments', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_users_username'), table_name='users', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_users_email'), table_name='users', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_users_created_at'), table_name='users', schema='experimentation')
    op.drop_table('users', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_roles_name'), table_name='roles', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_roles_created_at'), table_name='roles', schema='experimentation')
    op.drop_table('roles', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_permissions_resource'), table_name='permissions', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_permissions_name'), table_name='permissions', schema='experimentation')
    op.drop_index(op.f('ix_experimentation_permissions_created_at'), table_name='permissions', schema='experimentation')
    op.drop_table('permissions', schema='experimentation')
    # ### end Alembic commands ###
