"""Celery tasks for background processing."""

import logging
import os
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# IMPORTANT: Import your configured celery_app
from app.core.celery_app import celery_app
from app.models.booking import Booking, BookingStatus
from app.models.seat import Seat

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Detect if running inside Docker container
def is_running_in_docker():
    """Check if the application is running inside a Docker container."""
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                return True
    except (FileNotFoundError, PermissionError):
        pass
    return False

# Dynamic DATABASE_URL based on environment
if is_running_in_docker():
    # Docker environment - use service name
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/redbus")
else:
    # Local development - use localhost
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/redbus")

logger.info(f"[Celery Tasks] Running in Docker: {is_running_in_docker()}")
logger.info(f"[Celery Tasks] Using DATABASE_URL: {DATABASE_URL.replace('postgres:postgres@', '***@')}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# FIX 2: Use @celery_app.task instead of @shared_task to ensure it uses your Redis config
@celery_app.task(bind=True, max_retries=3, name="app.tasks.release_unpaid_seats")
def release_unpaid_seats(self, booking_ids: List[int]):
    logger.info(f"[Celery Task] Processing release_unpaid_seats for booking_ids: {booking_ids}")
    
    db = SessionLocal()
    try:
        released_count = 0
        for booking_id in booking_ids:
            logger.info(f"[Celery Task] Scanning Booking ID: {booking_id} for expiration...")
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                logger.warning(f"[Celery Task] Booking {booking_id} not found, skipping")
                continue
            
            if booking.status == BookingStatus.CONFIRMED:
                logger.info(f"[Celery Task] ACTION: SKIPPED - Booking {booking_id} is already CONFIRMED.")
                continue
            
            if booking.status == BookingStatus.PENDING:
                # Update status and release seat
                booking.status = BookingStatus.CANCELLED
                released_seat_id = None
                
                if booking.seat_id:
                    seat = db.query(Seat).filter(Seat.id == booking.seat_id).first()
                    if seat:
                        seat.is_available = True  # Cleanup: Flip is_available back to True
                        released_seat_id = seat.id
                        logger.info(f"[Celery Task] Released seat {seat.id} ({seat.seat_number}) - is_available flipped to TRUE")
                
                released_count += 1
                logger.info(f"[Celery Task] ACTION: CANCELLED - Booking {booking_id} expired and unpaid. Seat {released_seat_id} released.")
                logger.info(f"[Celery Task] Booking {booking_id} marked as CANCELLED (was PENDING), seat released")
            else:
                logger.info(f"[Celery Task] Booking {booking_id} is {booking.status.value}, skipping")
        
        db.commit()
        logger.info(f"[Celery Task] Released {released_count} seats from expired bookings")
        
        return {"status": "success", "released": released_count}
        
    except Exception as exc:
        logger.error(f"[Celery Task] Error: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
        SessionLocal.remove()

@celery_app.task(bind=True, name="app.tasks.silence_cleanup")
def silence_cleanup(self, booking_id: int):
    """Silence the cleanup task for a specific booking (payment confirmed)."""
    logger.info(f"[Celery Task] Silencing cleanup for booking {booking_id} - payment confirmed")

    # This task would normally revoke the scheduled cleanup task
    # For now, we just log that payment was confirmed
    # In production, you might use:
    # from celery.task.control import revoke
    # revoke(task_id=f"release_unpaid_seats-{booking_id}", terminate=True)

    return {"status": "silenced", "booking_id": booking_id}


@celery_app.task(bind=True, max_retries=3, name="app.tasks.release_expired_bookings")
def release_expired_bookings(self):
    """
    Self-healing inventory system: Release expired bookings.

    Queries bookings with status PENDING older than 10 minutes,
    sets status to EXPIRED, and releases seats back to inventory.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import and_

    logger.info("[Celery Task] Starting release_expired_bookings task")

    db = SessionLocal()
    try:
        # Calculate cutoff time (10 minutes ago) with timezone awareness
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        logger.info(f"[Celery Task] Searching for bookings older than {cutoff_time}")

        # Query pending bookings older than 10 minutes
        expired_bookings = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.booking_date <= cutoff_time
                )
            )
            .all()
        )

        if not expired_bookings:
            logger.info("[Celery Task] No expired bookings found")
            return {"status": "success", "released": 0}

        released_count = 0
        for booking in expired_bookings:
            # Use pessimistic locking to prevent race conditions
            seat = (
                db.query(Seat)
                .filter(Seat.id == booking.seat_id)
                .with_for_update()
                .first()
            )

            if seat:
                # Release the seat back to inventory
                seat.is_available = True
                logger.info(
                    f"[Celery Task] Released seat {seat.id} ({seat.seat_number}) "
                    f"for expired booking {booking.id}"
                )

            # Mark booking as expired
            booking.status = BookingStatus.EXPIRED
            released_count += 1
            logger.info(
                f"[Celery Task] Booking {booking.id} marked as EXPIRED "
                f"(was PENDING for >10 minutes)"
            )

        # Commit all changes in a single transaction
        db.commit()

        # Structured log showing count of released seats
        logger.info(f"[Celery Task] Released {released_count} seats for expired bookings")

        return {
            "status": "success",
            "released": released_count,
            "message": f"Released {released_count} seats for expired bookings"
        }

    except Exception as exc:
        logger.error(f"[Celery Task] Error in release_expired_bookings: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
        SessionLocal.remove()