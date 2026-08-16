"""Qora Mentor system — learning journeys, reasoning autopsies, patient series (PRD_QORA_MENTOR §5.1)

Revision ID: c4d5e6f7a8b9
Revises: 3f9b07c1a2d5
Create Date: 2026-08-16

Additive only (CREATE TABLE) — does not touch existing tables, so the live
product is unaffected until the mentor feature ships.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = '3f9b07c1a2d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB on Postgres (Supabase prod), JSON on anything else (sqlite dev).
JSONB = sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')


def upgrade() -> None:
    # -- Learning journeys (conversational package) ---------------------------
    op.create_table(
        'learning_journeys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('institution_id', sa.String(), nullable=False, server_default='default'),
        sa.Column('user_story', sa.Text(), nullable=False),
        sa.Column('extracted_context', JSONB, nullable=False),
        sa.Column('proposed_plan', JSONB, nullable=False),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('final_plan', JSONB, nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='proposed'),
        # proposed | active | completed | abandoned
        sa.Column('current_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('readiness_start', sa.Integer(), nullable=True),
        sa.Column('readiness_current', sa.Integer(), nullable=True),
        sa.Column('readiness_target', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_learning_journeys_user', 'learning_journeys', ['user_id', 'status'])
    op.create_index('ix_learning_journeys_institution', 'learning_journeys', ['institution_id'])

    # -- Journey cases (ordered) ----------------------------------------------
    op.create_table(
        'journey_cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('journey_id', sa.String(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('focus_area', sa.String(), nullable=True),
        sa.Column('learning_objective', sa.String(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='45'),
        # locked | available | in_progress | completed
        sa.Column('status', sa.String(), nullable=False, server_default='locked'),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['journey_id'], ['learning_journeys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('journey_id', 'day_number', name='uq_journey_cases_day'),
    )
    op.create_index('ix_journey_cases_journey', 'journey_cases', ['journey_id', 'day_number'])

    # -- Reasoning autopsy (post-session analysis) -----------------------------
    op.create_table(
        'reasoning_autopsies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('journey_id', sa.String(), nullable=True),
        sa.Column('user_pathway', JSONB, nullable=True),
        sa.Column('expert_pathway', JSONB, nullable=True),
        sa.Column('divergence_points', JSONB, nullable=True),
        sa.Column('errors_detected', JSONB, nullable=True),
        sa.Column('pearl', sa.Text(), nullable=True),
        sa.Column('readiness_impact', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['journey_id'], ['learning_journeys.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_autopsies_session', 'reasoning_autopsies', ['session_id'])
    op.create_index('ix_autopsies_journey', 'reasoning_autopsies', ['journey_id'])

    # -- Patient series (linked continuity cases) ------------------------------
    op.create_table(
        'patient_series',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('base_condition', sa.String(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('occupation', sa.String(), nullable=True),
        sa.Column('case_sequence', JSONB, nullable=False),
        sa.Column('triggers', JSONB, nullable=False),
        sa.Column('next_visit_context', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # -- User patient history (continuity tracking) ----------------------------
    op.create_table(
        'user_patient_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('series_id', sa.String(), nullable=False),
        sa.Column('current_visit', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_session_id', sa.String(), nullable=True),
        sa.Column('errors_detected', JSONB, nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        # active | completed | abandoned
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['series_id'], ['patient_series.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_session_id'], ['sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'series_id', name='uq_user_patient_history'),
    )
    op.create_index('ix_user_patient_history', 'user_patient_history', ['user_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_user_patient_history', table_name='user_patient_history')
    op.drop_table('user_patient_history')
    op.drop_table('patient_series')
    op.drop_index('ix_autopsies_journey', table_name='reasoning_autopsies')
    op.drop_index('ix_autopsies_session', table_name='reasoning_autopsies')
    op.drop_table('reasoning_autopsies')
    op.drop_index('ix_journey_cases_journey', table_name='journey_cases')
    op.drop_table('journey_cases')
    op.drop_index('ix_learning_journeys_institution', table_name='learning_journeys')
    op.drop_index('ix_learning_journeys_user', table_name='learning_journeys')
    op.drop_table('learning_journeys')
