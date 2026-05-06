"""Add is_window column to seats table

Revision ID: 2026_05_01_add_is_window
Revises: 2026_05_01_add_booking_seats
Create Date: 2026-05-01 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2026_05_01_add_is_window'
down_revision: Union[str, None] = '2026_05_01_add_booking_seats'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_window column to seats table."""
    op.add_column(
        'seats',
        sa.Column('is_window', sa.Boolean(), nullable=True, server_default='false')
    )
    print("Added is_window column to seats table")


def downgrade() -> None:
    """Drop is_window column from seats table."""
    op.drop_column('seats', 'is_window')
    print("Dropped is_window column from seats table")
