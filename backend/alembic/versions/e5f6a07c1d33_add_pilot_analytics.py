"""pilot_events + session_turns.input_type (Fase 5 §35)

Pilot behavioural analytics infrastructure:
- new table `pilot_events` (append-only event log for pilot funnel)
- `session_turns.input_type` column (text|voice) for §35.7 voice-vs-text.

Live sqlite (create_all path) handled by _ensure_runtime_columns() in
app/database.py; Alembic = source of truth for Postgres/prod.

Revision ID: e5f6a07c1d33
Revises: d3f9a07b1c22
Create Date: 2026-08-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a07c1d33'
down_revision: Union[str, Sequence[str], None] = 'd3f9a07b1c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # session_turns.input_type (voice vs text)
    with op.batch_alter_table('session_turns', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('input_type', sa.String(), nullable=False, server_default='text')
        )

    # pilot_events
    op.create_table(
        'pilot_events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('case_id', sa.String(), nullable=True),
    )
    op.create_index('ix_pilot_events_user_id', 'pilot_events', ['user_id'])
    op.create_index('ix_pilot_events_event', 'pilot_events', ['event'])
    op.create_index('ix_pilot_events_session_id', 'pilot_events', ['session_id'])
    op.create_index('ix_pilot_events_case_id', 'pilot_events', ['case_id'])


def downgrade() -> None:
    op.drop_index('ix_pilot_events_case_id', table_name='pilot_events')
    op.drop_index('ix_pilot_events_session_id', table_name='pilot_events')
    op.drop_index('ix_pilot_events_event', table_name='pilot_events')
    op.drop_index('ix_pilot_events_user_id', table_name='pilot_events')
    op.drop_table('pilot_events')
    with op.batch_alter_table('session_turns', schema=None) as batch_op:
        batch_op.drop_column('input_type')