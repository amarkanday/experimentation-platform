"""Add metrics tables

Revision ID: e45a2f9c8d21
Revises: ba93ceb4d658
Create Date: 2023-11-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e45a2f9c8d21'
down_revision = 'ba93ceb4d658'
branch_labels = None
depends_on = None

schema_name = 'app'

def upgrade():
    # Create MetricType enum
    op.create_table(
        'raw_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('targeting_rule_id', sa.String(255), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema_name}.feature_flags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], [f'{schema_name}.segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema_name
    )

    # Create indexes for raw_metrics
    op.create_index(op.f(f'{schema_name}_raw_metric_metric_type'), 'raw_metrics', ['metric_type'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_timestamp'), 'raw_metrics', ['timestamp'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_feature_flag_id'), 'raw_metrics', ['feature_flag_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_targeting_rule_id'), 'raw_metrics', ['targeting_rule_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_user_id'), 'raw_metrics', ['user_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_segment_id'), 'raw_metrics', ['segment_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_flag_time'), 'raw_metrics', ['feature_flag_id', 'timestamp'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_raw_metric_user_flag'), 'raw_metrics', ['user_id', 'feature_flag_id'], schema=schema_name)

    # Create aggregated_metrics table
    op.create_table(
        'aggregated_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('period', sa.String(10), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('targeting_rule_id', sa.String(255), nullable=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sum_value', sa.Float(), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('distinct_users', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema_name}.feature_flags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], [f'{schema_name}.segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema_name
    )

    # Create indexes for aggregated_metrics
    op.create_index(op.f(f'{schema_name}_agg_metric_metric_type'), 'aggregated_metrics', ['metric_type'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_agg_metric_period'), 'aggregated_metrics', ['period'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_agg_metric_period_start'), 'aggregated_metrics', ['period_start'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_agg_metric_feature_flag_id'), 'aggregated_metrics', ['feature_flag_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_agg_metric_targeting_rule_id'), 'aggregated_metrics', ['targeting_rule_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_agg_metric_segment_id'), 'aggregated_metrics', ['segment_id'], schema=schema_name)
    op.create_index(
        op.f(f'{schema_name}_agg_metric_unique'),
        'aggregated_metrics',
        ['metric_type', 'period', 'period_start', 'feature_flag_id', 'targeting_rule_id', 'segment_id'],
        unique=True,
        schema=schema_name
    )
    op.create_index(
        op.f(f'{schema_name}_agg_metric_period_time'),
        'aggregated_metrics',
        ['period', 'period_start'],
        schema=schema_name
    )
    op.create_index(
        op.f(f'{schema_name}_agg_metric_flag_period'),
        'aggregated_metrics',
        ['feature_flag_id', 'period', 'period_start'],
        schema=schema_name
    )

    # Create error_logs table
    op.create_table(
        'error_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('message', sa.String(1000), nullable=False),
        sa.Column('stack_trace', sa.String(), nullable=True),
        sa.Column('request_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['feature_flag_id'], [f'{schema_name}.feature_flags.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema_name
    )

    # Create indexes for error_logs
    op.create_index(op.f(f'{schema_name}_error_type'), 'error_logs', ['error_type'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_error_timestamp'), 'error_logs', ['timestamp'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_error_feature_flag_id'), 'error_logs', ['feature_flag_id'], schema=schema_name)
    op.create_index(op.f(f'{schema_name}_error_user_id'), 'error_logs', ['user_id'], schema=schema_name)
    op.create_index(
        op.f(f'{schema_name}_error_flag_time'),
        'error_logs',
        ['feature_flag_id', 'timestamp'],
        schema=schema_name
    )


def downgrade():
    # Drop all tables and indexes
    op.drop_table('error_logs', schema=schema_name)
    op.drop_table('aggregated_metrics', schema=schema_name)
    op.drop_table('raw_metrics', schema=schema_name)
