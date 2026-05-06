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

logger = logging.getLogger(__name__)

# FIX 1: Change localhost to postgres for Docker internal networking
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/redbus")

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
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                logger.warning(f"[Celery Task] Booking {booking_id} not found, skipping")
                continue
            
            if booking.status == BookingStatus.PENDING:
                # Update status and release seat
                booking.status = BookingStatus.CANCELLED 
                
                if booking.seat_id:
                    seat = db.query(Seat).filter(Seat.id == booking.seat_id).first()
                    if seat:
                        seat.is_available = True
                        logger.info(f"[Celery Task] Released seat {seat.id} for booking {booking_id}")
                
                released_count += 1
            else:
                logger.info(f"[Celery Task] Booking {booking_id} is {booking.status}, skipping")
        
        db.commit()
        return {"status": "success", "released": released_count}
        
    except Exception as exc:
        logger.error(f"[Celery Task] Error: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
        SessionLocal.remove()