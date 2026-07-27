"""add region column to user_profiles (Phase 1 — international pricing)

Revision ID: 7b3c8e1d2f60
Revises: f1a2b3c4d5e6
Create Date: 2026-07-27

Additive only — does not touch existing columns or tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '7b3c8e1d2f60'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('region', sa.String(), nullable=False, server_default='row'),
    )


def downgrade() -> None:
    op.drop_column('user_profiles', 'region')
