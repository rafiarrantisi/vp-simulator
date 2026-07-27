"""add preferred_language to user_profiles

Revision ID: 3f9b07c1a2d5
Revises: 2e8a91d3c704
Create Date: 2026-07-27

Additive only — does not touch existing columns or tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '3f9b07c1a2d5'
down_revision: Union[str, Sequence[str], None] = '2e8a91d3c704'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('preferred_language', sa.String(), nullable=False, server_default='en'),
    )


def downgrade() -> None:
    op.drop_column('user_profiles', 'preferred_language')
