"""add language column to sessions (multilingual patient responses)

Revision ID: 2e8a91d3c704
Revises: 7b3c8e1d2f60
Create Date: 2026-07-27

Additive only — does not touch existing columns or tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '2e8a91d3c704'
down_revision: Union[str, Sequence[str], None] = '7b3c8e1d2f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('language', sa.String(), nullable=False, server_default='en'),
    )


def downgrade() -> None:
    op.drop_column('sessions', 'language')
