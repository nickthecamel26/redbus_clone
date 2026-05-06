from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from datetime import datetime, timezone
import logging
import traceback

from app.db.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.trip import Trip
from app.models.seat import Seat
from app.models.bus import Bus
from app.models.route import Route
from app.models.user import User
from app.schemas.booking import BookingResponse, BookingCreate, BookingUpdate, BookingSummary, MyBooking
from app.core.security import get_current_user

# Set up logger
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[BookingResponse])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return bookings

@router.post("/", response_model=BookingSummary)
def create_booking(
    booking_data: BookingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create bookings for multiple seats on a trip with pessimistic locking."""
    # Use authenticated user's ID instead of hardcoded value
    user_id = current_user.id
    
    logger.info(f"Creating booking for trip_id={booking_data.trip_id}, seat_ids={booking_data.seat_ids}")
    
    # Get the trip to check price (outside transaction, read-only)
    trip = db.query(Trip).filter(Trip.id == booking_data.trip_id).first()
    if not trip:
        logger.warning(f"Trip {booking_data.trip_id} not found")
        raise HTTPException(status_code=404, detail="Trip not found")
    
    logger.info(f"Found trip with bus_id={trip.bus_id}, price={trip.price}")
    
    # Use pessimistic locking for seat availability check
    try:
        # Lock the seats for update (pessimistic locking) - session already active from Depends
        seats = (
            db.query(Seat)
            .filter(Seat.id.in_(booking_data.seat_ids))
            .with_for_update(nowait=True)  # Lock rows, fail fast if locked
            .all()
        )
        
        if len(seats) != len(booking_data.seat_ids):
            logger.error(f"Some seats not found. Requested: {booking_data.seat_ids}, Found: {[s.id for s in seats]}")
            raise HTTPException(status_code=400, detail="Some seats not found")
        
        # Check if seats are available and belong to correct bus
        for seat in seats:
            if seat.bus_id != trip.bus_id:
                logger.error(f"Seat {seat.id} belongs to bus {seat.bus_id}, but trip uses bus {trip.bus_id}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Seat {seat.id} does not belong to this trip's bus"
                )
            # Check if seat is available
            if not seat.is_available:
                logger.warning(f"Seat {seat.id} ({seat.seat_number}) is not available")
                raise HTTPException(
                    status_code=400,
                    detail=f"Seat {seat.seat_number} is not available"
                )
        
        # Check for existing active bookings on these seats for this trip
        existing_bookings = db.query(Booking).filter(
            Booking.trip_id == booking_data.trip_id,
            Booking.seat_id.in_(booking_data.seat_ids),
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).all()
        
        if existing_bookings:
            booked_seat_ids = [b.seat_id for b in existing_bookings]
            logger.warning(f"Seats already have active bookings: {booked_seat_ids}")
            raise HTTPException(
                status_code=400, 
                detail=f"Seats {booked_seat_ids} are already booked for this trip"
            )
        
        # Create bookings for each seat within the existing session transaction
        created_bookings = []
        for seat in seats:
            # Mark seat as unavailable
            seat.is_available = False
            logger.info(f"Marked seat {seat.id} ({seat.seat_number}) as unavailable")
            
            # Create booking
            booking = Booking(
                user_id=user_id,
                trip_id=booking_data.trip_id,
                seat_id=seat.id,
                status=BookingStatus.PENDING,
                total_price=trip.price
            )
            db.add(booking)
            db.flush()  # Flush to get the booking ID
            db.refresh(booking)
            created_bookings.append(booking)
            logger.info(f"Created booking {booking.id} for seat {seat.id}")
            
            # Insert into booking_seats junction table
            db.execute(
                text("INSERT INTO booking_seats (booking_id, seat_id) VALUES (:booking_id, :seat_id)"),
                {"booking_id": booking.id, "seat_id": seat.id}
            )
            logger.info(f"Inserted into booking_seats: booking_id={booking.id}, seat_id={seat.id}")
        
        # Commit the transaction (session from Depends handles this)
        db.commit()
        logger.info(f"Atomic transaction committed - {len(created_bookings)} bookings created")
        
        logger.info(f"Successfully created {len(created_bookings)} bookings")
        
        return BookingSummary(
            bookings=created_bookings,
            total_seats=len(created_bookings),
            message=f"Successfully booked {len(created_bookings)} seats"
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Check for lock-related errors
        error_str = str(e).lower()
        if "lock" in error_str or "could not obtain" in error_str or "resource busy" in error_str:
            logger.error(f"Lock conflict during booking: {e}")
            raise HTTPException(
                status_code=409, 
                detail="Seat is currently being processed by another user. Please try again."
            )
        logger.error(f"Exception in create_booking: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in create_booking: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")

@router.get("/my-bookings", response_model=List[MyBooking])
def get_my_bookings(db: Session = Depends(get_db)):
    """Get all bookings for the current user with trip and bus details."""
    # Hardcoded user_id for now (until frontend login is integrated)
    user_id = 1
    
    # Query bookings with joined data
    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.trip).joinedload(Trip.bus),
            joinedload(Booking.trip).joinedload(Trip.route),
            joinedload(Booking.seat)
        )
        .filter(Booking.user_id == user_id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    
    # Group bookings by trip_id to aggregate seat numbers
    from collections import defaultdict
    trip_bookings = defaultdict(list)
    
    for booking in bookings:
        trip_bookings[booking.trip_id].append(booking)
    
    # Build MyBooking responses
    my_bookings = []
    for trip_id, trip_booking_list in trip_bookings.items():
        first_booking = trip_booking_list[0]
        trip = first_booking.trip
        bus = trip.bus
        route = trip.route
        
        # Collect all seat numbers for this trip
        seat_numbers = [booking.seat.seat_number for booking in trip_booking_list]
        
        my_bookings.append(MyBooking(
            booking_id=first_booking.id,
            bus_name=bus.name,
            source=route.source_city,
            destination=route.destination_city,
            travel_date=trip.departure_time,
            seat_numbers=seat_numbers,
            status=first_booking.status,
            total_price=first_booking.total_price * len(seat_numbers) if first_booking.total_price else None
        ))
    
    return my_bookings


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int):
    # Placeholder - implement actual booking retrieval
    pass

@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, booking: BookingUpdate):
    # Placeholder - implement actual booking update
    pass

@router.patch("/{booking_id}/cancel", response_model=dict)
def cancel_booking(
    booking_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a booking if valid conditions are met. Users can only cancel their own bookings."""
    try:
        # Use authenticated user's ID
        user_id = current_user.id
        
        logger.info(f"Cancelling booking {booking_id} for user {user_id}")
        
        # Get the booking with trip and seat info
        booking = (
            db.query(Booking)
            .options(joinedload(Booking.trip), joinedload(Booking.seat))
            .filter(Booking.id == booking_id)
            .first()
        )
        
        # Check if booking exists
        if not booking:
            logger.warning(f"Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Security: Verify booking ownership - users can only cancel their own bookings
        if booking.user_id != user_id:
            logger.warning(f"User {user_id} attempted to cancel booking {booking_id} which belongs to user {booking.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only cancel your own bookings"
            )
        
        # Check if already cancelled
        if booking.status == BookingStatus.CANCELLED:
            logger.warning(f"Booking {booking_id} is already cancelled")
            raise HTTPException(status_code=400, detail="Booking is already cancelled")
        
        # Check if trip has already departed
        if booking.trip.departure_time < datetime.now(timezone.utc):
            logger.warning(f"Cannot cancel booking {booking_id} - trip has already departed")
            raise HTTPException(status_code=400, detail="Cannot cancel - trip has already departed")
        
        # Atomic transaction: both booking status and seat availability update together
        try:
            # Update booking status to CANCELLED
            booking.status = BookingStatus.CANCELLED
            
            # Update seat availability for this specific trip
            seat = booking.seat
            if seat:
                seat.is_available = True
                logger.info(f"Seat {seat.seat_number} (id={seat.id}) marked as available")
            
            # Delete from booking_seats junction table
            db.execute(
                text("DELETE FROM booking_seats WHERE booking_id = :booking_id AND seat_id = :seat_id"),
                {"booking_id": booking.id, "seat_id": booking.seat_id}
            )
            logger.info(f"Deleted from booking_seats: booking_id={booking.id}, seat_id={booking.seat_id}")
            
            db.commit()
            logger.info(f"Committed cancellation for booking {booking_id}")
        
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Cancellation failed due to database error")
        
        # Refresh to get updated state
        db.refresh(booking)
        if booking.seat:
            db.refresh(booking.seat)
        
        logger.info(f"Successfully cancelled booking {booking_id}")
        
        # Return clean list-like format
        return {
            "message": "Booking cancelled successfully",
            "cancelled_booking": {
                "booking_id": booking.id,
                "trip_id": booking.trip_id,
                "seat_id": booking.seat_id,
                "seat_number": booking.seat.seat_number if booking.seat else None,
                "status": booking.status.value,
                "total_price": float(booking.total_price) if booking.total_price else None,
                "refund_amount": float(booking.total_price) if booking.total_price else 0.0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in cancel_booking: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")
