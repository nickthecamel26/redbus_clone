"""CRUD operations for bookings."""

from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from app.models.booking import Booking, BookingStatus
from app.models.seat import Seat
from app.models.trip import Trip
from app.core.redis import invalidate_booking_cache
from app.core.logger import logger


def cleanup_expired_bookings(db: Session) -> int:
    """
    Clean up expired pending bookings.
    
    Finds all bookings with status == 'Pending' created more than 15 minutes ago,
    releases seats, and invalidates cache.
    
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
                # Defensive guard: strictly skip non-PENDING bookings
                # (handles race conditions where status was changed between query and update)
                if booking.status != BookingStatus.PENDING:
                    logger.info(
                        f"[REAPER] SKIPPED - Booking {booking.id} status is "
                        f"{booking.status.value}, not PENDING. Ignoring."
                    )
                    continue

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
                
                # Release seat back to available
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


def create_with_seats(db: Session, trip_id: int, seat_numbers: List[str], user_id: int, total_amount: float) -> dict:
    """
    Create bookings with seat numbers, ensuring atomic seat reservation.
    
    Args:
        db: Database session
        trip_id: ID of trip to book
        seat_numbers: List of seat numbers to book
        user_id: ID of user making booking
        total_amount: Total price for all seats
        
    Returns:
        Dictionary with booking details or error message
        
    Raises:
        ValueError: If seats are not available
    """
    logger.info(f"[BOOKING] Creating booking for trip {trip_id}, seats {seat_numbers}, user {user_id}")
    
    try:
        # Start transaction
        db.begin()
        
        # Get trip details
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")
        
        # Find seats for the given trip
        seats = (
            db.query(Seat)
            .join(Seat.bus)
            .filter(
                Seat.bus_id == trip.bus_id,
                Seat.seat_number.in_(seat_numbers)
            )
            .all()
        )
        
        if len(seats) != len(seat_numbers):
            raise ValueError(f"Only found {len(seats)} out of {len(seat_numbers)} requested seats")
        
        # Check if any seats are already booked
        unavailable_seats = []
        for seat in seats:
            if not seat.is_available:
                unavailable_seats.append(seat.seat_number)
        
        if unavailable_seats:
            error_msg = f"Seats already taken: {', '.join(unavailable_seats)}"
            logger.warning(f"[BOOKING] {error_msg}")
            db.rollback()
            return {"error": error_msg, "unavailable_seats": unavailable_seats}
        
        # Mark seats as unavailable (atomic operation)
        for seat in seats:
            seat.is_available = False
            logger.info(f"[BOOKING] Marked seat {seat.seat_number} as unavailable")
        
        # Create booking records
        bookings = []
        for seat in seats:
            booking = Booking(
                user_id=user_id,
                trip_id=trip_id,
                seat_id=seat.id,
                status=BookingStatus.PENDING,
                total_price=total_amount / len(seats),  # Price per seat
                booking_date=datetime.now(timezone.utc)
            )
            db.add(booking)
            bookings.append(booking)
            logger.info(f"[BOOKING] Created booking {booking.id} for seat {seat.seat_number}")
        
        # Commit transaction
        db.commit()
        
        # Invalidate cache for this trip
        trip_with_route = (
            db.query(Trip)
            .join(Trip.route)
            .filter(Trip.id == trip_id)
            .first()
        )
        
        if trip_with_route and trip_with_route.trip and trip_with_route.trip.route:
            source = trip_with_route.trip.route.source_city
            destination = trip_with_route.trip.route.destination_city
            travel_date_str = trip_with_route.trip.departure_time.date().isoformat()
            
            invalidate_booking_cache(trip_id, source, destination, travel_date_str)
            logger.info(f"[BOOKING] Invalidated cache for trip {trip_id}")
        
        logger.info(f"[BOOKING] Successfully created {len(bookings)} bookings for trip {trip_id}")
        
        return {
            "success": True,
            "bookings": [
                {
                    "id": booking.id,
                    "user_id": booking.user_id,
                    "trip_id": booking.trip_id,
                    "seat_id": booking.seat_id,
                    "seat_number": seat.seat_number,
                    "status": booking.status.value,
                    "total_price": float(booking.total_price),
                    "booking_date": booking.booking_date.isoformat()
                }
                for booking in bookings
            ],
            "total_seats": len(bookings),
            "total_amount": total_amount,
            "message": f"Successfully booked {len(bookings)} seats"
        }
        
    except ValueError as e:
        logger.error(f"[BOOKING] Validation error: {str(e)}")
        db.rollback()
        return {"error": str(e), "unavailable_seats": unavailable_seats if 'unavailable_seats' in locals() else []}
        
    except Exception as e:
        logger.error(f"[BOOKING] Unexpected error: {type(e).__name__}: {e}")
        db.rollback()
        return {"error": "Failed to create booking due to server error"}
