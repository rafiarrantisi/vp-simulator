"""billing entitlements, usage events, session costs (pivot-v4 §7)

Revision ID: f1a2b3c4d5e6
Revises: d3f9a07b1c22
Create Date: 2026-06-20

Additive only (CREATE TABLE) — does not touch existing tables, so the live
product is unaffected until billing is enforced.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd3f9a07b1c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'entitlements',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('plan', sa.String(), nullable=False, server_default='free'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mor_customer_id', sa.String(), nullable=False, server_default=''),
        sa.Column('mor_subscription_id', sa.String(), nullable=False, server_default=''),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )
    op.create_table(
        'usage_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_usage_events_user_id', 'usage_events', ['user_id'])
    op.create_index('ix_usage_events_kind', 'usage_events', ['kind'])
    op.create_index('ix_usage_events_created_at', 'usage_events', ['created_at'])
    op.create_table(
        'session_costs',
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_out', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('est_cost_usd', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('session_id'),
    )
    op.create_index('ix_session_costs_user_id', 'session_costs', ['user_id'])
    op.create_index('ix_session_costs_created_at', 'session_costs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_session_costs_created_at', table_name='session_costs')
    op.drop_index('ix_session_costs_user_id', table_name='session_costs')
    op.drop_table('session_costs')
    op.drop_index('ix_usage_events_created_at', table_name='usage_events')
    op.drop_index('ix_usage_events_kind', table_name='usage_events')
    op.drop_index('ix_usage_events_user_id', table_name='usage_events')
    op.drop_table('usage_events')
    op.drop_table('entitlements')
