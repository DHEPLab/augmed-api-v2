"""add experiment and rl_run tables

Revision ID: a1b2c3d4e5f6
Revises: 5ec038ebcfe5
Create Date: 2026-02-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '5ec038ebcfe5'
branch_labels = None
depends_on = None


def upgrade():
    # Create experiment table
    op.create_table(
        'experiment',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('experiment_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('arms', postgresql.JSONB, nullable=False),
        sa.Column('case_pool', postgresql.JSONB, nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )

    # Create rl_run table
    op.create_table(
        'rl_run',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'experiment_id',
            sa.String(100),
            sa.ForeignKey('experiment.experiment_id'),
            nullable=False,
        ),
        sa.Column('model_version', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('triggered_by', sa.String(50), nullable=True),
        sa.Column('configs_generated', sa.Integer, nullable=True),
        sa.Column('answers_consumed', sa.Integer, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_params', postgresql.JSONB, nullable=True),
    )

    # Add experiment tracking columns to display_config
    op.add_column('display_config', sa.Column('experiment_id', sa.String(100), nullable=True))
    op.add_column('display_config', sa.Column('rl_run_id', sa.Integer, nullable=True))
    op.add_column('display_config', sa.Column('arm', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('display_config', 'arm')
    op.drop_column('display_config', 'rl_run_id')
    op.drop_column('display_config', 'experiment_id')
    op.drop_table('rl_run')
    op.drop_table('experiment')
