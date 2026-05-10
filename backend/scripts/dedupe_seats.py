"""
Emergency cleanup: deduplicate the seats table.

For every (bus_id, seat_number) group that has more than one row, this script:
  1. Picks a canonical seat (the one with the lowest id).
  2. Reassigns all FK references in `bookings` and `booking_seats` from the
     duplicate seat ids -> the canonical seat id.
  3. Deletes the duplicate seat rows.

The script is idempotent: running it on a clean table is a no-op.

Usage (from project root):
    docker compose exec backend python scripts/dedupe_seats.py
or locally:
    python -m scripts.dedupe_seats
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("dedupe_seats")


def find_duplicate_groups(db: Session) -> Dict[Tuple[int, str], List[int]]:
    """Return {(bus_id, seat_number): [seat_id, ...]} for groups of size > 1."""
    rows = db.execute(
        text(
            """
            SELECT bus_id, seat_number, id
            FROM seats
            WHERE (bus_id, seat_number) IN (
                SELECT bus_id, seat_number
                FROM seats
                GROUP BY bus_id, seat_number
                HAVING COUNT(*) > 1
            )
            ORDER BY bus_id, seat_number, id
            """
        )
    ).fetchall()

    groups: Dict[Tuple[int, str], List[int]] = defaultdict(list)
    for bus_id, seat_number, seat_id in rows:
        groups[(bus_id, seat_number)].append(seat_id)
    return groups


def dedupe(db: Session) -> dict:
    groups = find_duplicate_groups(db)
    if not groups:
        log.info("No duplicate seats found. Table is clean.")
        return {"groups": 0, "duplicates_removed": 0, "bookings_reassigned": 0}

    log.info("Found %d duplicate (bus_id, seat_number) groups", len(groups))
    total_removed = 0
    total_reassigned = 0

    try:
        for (bus_id, seat_number), seat_ids in groups.items():
            canonical_id = seat_ids[0]
            duplicate_ids = seat_ids[1:]
            log.info(
                "[bus=%s seat=%s] keep id=%s, removing %s",
                bus_id, seat_number, canonical_id, duplicate_ids,
            )

            # Reassign bookings FK
            result = db.execute(
                text(
                    """
                    UPDATE bookings
                    SET seat_id = :canonical
                    WHERE seat_id = ANY(:dup_ids)
                    """
                ),
                {"canonical": canonical_id, "dup_ids": duplicate_ids},
            )
            total_reassigned += result.rowcount or 0

            # Reassign booking_seats junction (handle PK conflicts by deleting
            # rows that would collide, since they represent the same logical seat)
            db.execute(
                text(
                    """
                    DELETE FROM booking_seats
                    WHERE seat_id = ANY(:dup_ids)
                      AND booking_id IN (
                          SELECT booking_id FROM booking_seats
                          WHERE seat_id = :canonical
                      )
                    """
                ),
                {"canonical": canonical_id, "dup_ids": duplicate_ids},
            )
            db.execute(
                text(
                    """
                    UPDATE booking_seats
                    SET seat_id = :canonical
                    WHERE seat_id = ANY(:dup_ids)
                    """
                ),
                {"canonical": canonical_id, "dup_ids": duplicate_ids},
            )

            # Delete the duplicate seat rows
            result = db.execute(
                text("DELETE FROM seats WHERE id = ANY(:dup_ids)"),
                {"dup_ids": duplicate_ids},
            )
            total_removed += result.rowcount or 0

        db.commit()
        log.info(
            "Cleanup complete: %d duplicates deleted, %d bookings reassigned, %d groups processed",
            total_removed, total_reassigned, len(groups),
        )
        return {
            "groups": len(groups),
            "duplicates_removed": total_removed,
            "bookings_reassigned": total_reassigned,
        }
    except Exception:
        db.rollback()
        log.exception("Dedupe failed; transaction rolled back")
        raise


def main() -> None:
    db = SessionLocal()
    try:
        dedupe(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
