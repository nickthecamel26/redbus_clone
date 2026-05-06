"""Add booking_seats table for many-to-many relationship

Revision ID: 2026_05_01_add_booking_seats
Revises: 737258ce25cb
Create Date: 2026-05-01 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2026_05_01_add_booking_seats'
down_revision: Union[str, None] = '737258ce25cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create booking_seats junction table."""
    # Create the booking_seats table
    op.create_table(
        'booking_seats',
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('seat_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seat_id'], ['seats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('booking_id', 'seat_id')
    )
    
    # Create indexes for faster lookups
    op.create_index('ix_booking_seats_booking_id', 'booking_seats', ['booking_id'])
    op.create_index('ix_booking_seats_seat_id', 'booking_seats', ['seat_id'])
    
    print("Created booking_seats table with foreign keys to bookings and seats")


def downgrade() -> None:
    """Drop booking_seats table."""
    op.drop_index('ix_booking_seats_seat_id', table_name='booking_seats')
    op.drop_index('ix_booking_seats_booking_id', table_name='booking_seats')
    op.drop_table('booking_seats')
    
    print("Dropped booking_seats table")
