"""Add reports table for analytics

Revision ID: add_reports_table
Revises: add_role_field_to_user
Create Date: 2023-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_reports_table'
down_revision = 'add_role_field_to_user'  # Make sure this matches the previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create ReportType enum
    report_type = sa.Enum(
        'experiment_result',
        'feature_flag_usage',
        'user_activity',
        'custom',
        name='reporttype',
        schema='app'
    )
    report_type.create(op.get_bind())

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('report_type', sa.Enum('experiment_result', 'feature_flag_usage', 'user_activity', 'custom',
                                       name='reporttype', schema='app'), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=True),
        sa.Column('query_definition', postgresql.JSONB(), nullable=True),
        sa.Column('visualization_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        # Add foreign key constraints
        sa.ForeignKeyConstraint(['owner_id'], ['app.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['experiment_id'], ['app.experiments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['feature_flag_id'], ['app.feature_flags.id'], ondelete='SET NULL'),

        # Set the schema
        schema='app'
    )

    # Add indexes
    op.create_index('ix_app_reports_owner_id', 'reports', ['owner_id'], schema='app')
    op.create_index('ix_app_reports_experiment_id', 'reports', ['experiment_id'], schema='app')
    op.create_index('ix_app_reports_feature_flag_id', 'reports', ['feature_flag_id'], schema='app')
    op.create_index('ix_app_reports_report_type', 'reports', ['report_type'], schema='app')


def downgrade():
    # Drop indexes
    op.drop_index('ix_app_reports_owner_id', table_name='reports', schema='app')
    op.drop_index('ix_app_reports_experiment_id', table_name='reports', schema='app')
    op.drop_index('ix_app_reports_feature_flag_id', table_name='reports', schema='app')
    op.drop_index('ix_app_reports_report_type', table_name='reports', schema='app')

    # Drop table
    op.drop_table('reports', schema='app')

    # Drop enum
    op.execute('DROP TYPE app.reporttype')
