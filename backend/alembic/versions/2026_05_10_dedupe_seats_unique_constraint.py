"""Dedupe seats and add unique constraint on (bus_id, seat_number).

Revision ID: 2026_05_10_dedupe_seats
Revises: 2026_05_01_add_is_window
Create Date: 2026-05-10 12:50:00.000000

This migration:
  1. Reassigns booking FK references (bookings.seat_id, booking_seats.seat_id)
     from duplicate seat rows to the canonical (lowest-id) row per
     (bus_id, seat_number) group.
  2. Deletes the now-orphaned duplicate seat rows.
  3. Adds a UNIQUE constraint on (bus_id, seat_number) so duplicates can never
     be inserted again.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "2026_05_10_dedupe_seats"
down_revision: Union[str, None] = "2026_05_01_add_is_window"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "uq_seats_bus_id_seat_number"


def upgrade() -> None:
    """Dedupe duplicate seats and enforce uniqueness."""
    bind = op.get_bind()

    # Step 1: Reassign booking_seats rows that would collide on the canonical
    # seat by deleting the duplicates outright (same logical seat anyway).
    bind.execute(
        text(
            """
            WITH canonical AS (
                SELECT bus_id, seat_number, MIN(id) AS keeper_id
                FROM seats
                GROUP BY bus_id, seat_number
            ),
            dup_to_keeper AS (
                SELECT s.id AS dup_id, c.keeper_id
                FROM seats s
                JOIN canonical c
                  ON c.bus_id = s.bus_id AND c.seat_number = s.seat_number
                WHERE s.id <> c.keeper_id
            )
            DELETE FROM booking_seats bs
            USING dup_to_keeper d
            WHERE bs.seat_id = d.dup_id
              AND EXISTS (
                  SELECT 1 FROM booking_seats bs2
                  WHERE bs2.booking_id = bs.booking_id
                    AND bs2.seat_id = d.keeper_id
              )
            """
        )
    )

    # Step 2: Reassign remaining booking_seats rows from dup -> keeper.
    bind.execute(
        text(
            """
            WITH canonical AS (
                SELECT bus_id, seat_number, MIN(id) AS keeper_id
                FROM seats
                GROUP BY bus_id, seat_number
            ),
            dup_to_keeper AS (
                SELECT s.id AS dup_id, c.keeper_id
                FROM seats s
                JOIN canonical c
                  ON c.bus_id = s.bus_id AND c.seat_number = s.seat_number
                WHERE s.id <> c.keeper_id
            )
            UPDATE booking_seats bs
            SET seat_id = d.keeper_id
            FROM dup_to_keeper d
            WHERE bs.seat_id = d.dup_id
            """
        )
    )

    # Step 3: Reassign bookings.seat_id FK from dup -> keeper.
    bind.execute(
        text(
            """
            WITH canonical AS (
                SELECT bus_id, seat_number, MIN(id) AS keeper_id
                FROM seats
                GROUP BY bus_id, seat_number
            ),
            dup_to_keeper AS (
                SELECT s.id AS dup_id, c.keeper_id
                FROM seats s
                JOIN canonical c
                  ON c.bus_id = s.bus_id AND c.seat_number = s.seat_number
                WHERE s.id <> c.keeper_id
            )
            UPDATE bookings b
            SET seat_id = d.keeper_id
            FROM dup_to_keeper d
            WHERE b.seat_id = d.dup_id
            """
        )
    )

    # Step 4: Delete duplicate seat rows (everything except MIN(id) per group).
    bind.execute(
        text(
            """
            DELETE FROM seats s
            USING (
                SELECT bus_id, seat_number, MIN(id) AS keeper_id
                FROM seats
                GROUP BY bus_id, seat_number
                HAVING COUNT(*) > 1
            ) c
            WHERE s.bus_id = c.bus_id
              AND s.seat_number = c.seat_number
              AND s.id <> c.keeper_id
            """
        )
    )

    # Step 5: Enforce uniqueness so this can never happen again.
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "seats",
        ["bus_id", "seat_number"],
    )


def downgrade() -> None:
    """Drop the unique constraint. Duplicate data is NOT restored."""
    op.drop_constraint(CONSTRAINT_NAME, "seats", type_="unique")
