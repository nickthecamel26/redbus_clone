"""CRUD operations for bookings."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.booking import Booking, BookingStatus
from app.models.seat import Seat
from app.core.redis import invalidate_booking_cache
from app.core.logger import logger


def cleanup_expired_bookings(db: Session) -> int:
    """
    Clean up expired pending bookings.
    
    Finds all bookings with status == 'Pending' created more than 15 minutes ago,
    releases the seats, and invalidates cache.
    
    Args:
        db: Database session
        
    Returns:
        Number of expired bookings cleaned up
    """
    logger.info("[REAPER] Scanning for expired pending bookings...")
    
    # Calculate cutoff time (15 minutes ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    logger.info(f"[REAPER] Cutoff time: {cutoff_time}")
    
    try:
        # Find expired pending bookings
        expired_bookings = (
            db.query(Booking)
            .filter(
                Booking.status == BookingStatus.PENDING,
                Booking.booking_date < cutoff_time
            )
            .all()
        )
        
        if not expired_bookings:
            logger.info("[REAPER] No expired bookings found")
            return 0
        
        logger.info(f"[REAPER] Found {len(expired_bookings)} expired bookings to clean up")
        
        cleaned_count = 0
        for booking in expired_bookings:
            try:
                # Get trip details for cache invalidation
                trip_with_route = (
                    db.query(Booking)
                    .join(Booking.trip)
                    .join(Booking.trip, Booking.trip.route)
                    .filter(Booking.id == booking.id)
                    .first()
                )
                
                if trip_with_route and trip_with_route.trip and trip_with_route.trip.route:
                    source = trip_with_route.trip.route.source_city
                    destination = trip_with_route.trip.route.destination_city
                    travel_date_str = trip_with_route.trip.departure_time.date().isoformat()
                    
                    # Invalidate cache for this booking
                    invalidate_booking_cache(
                        booking.trip_id, 
                        source, 
                        destination, 
                        travel_date_str
                    )
                    logger.info(f"[REAPER] Invalidated cache for expired booking {booking.id}")
                
                # Release the seat back to available
                seat = db.query(Seat).filter(Seat.id == booking.seat_id).first()
                if seat:
                    seat.is_available = True
                    logger.info(f"[REAPER] Released seat {seat.id} ({seat.seat_number}) from expired booking {booking.id}")
                
                # Mark booking as cancelled (or delete if preferred)
                booking.status = BookingStatus.CANCELLED
                logger.info(f"[REAPER] Marked booking {booking.id} as CANCELLED")
                
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"[REAPER] Error processing expired booking {booking.id}: {type(e).__name__}: {e}")
                # Continue with other bookings
                continue
        
        # Commit all changes
        db.commit()
        logger.info(f"[REAPER] Released {cleaned_count} seats from expired bookings")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"[REAPER] Error in cleanup_expired_bookings: {type(e).__name__}: {e}")
        db.rollback()
        return 0
