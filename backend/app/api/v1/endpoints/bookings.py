from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from datetime import datetime, timezone
from decimal import Decimal
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
from app.core.logger import logger
from app.core.redis import invalidate_booking_cache
from app.crud.booking import cleanup_expired_bookings
from app.tasks import release_unpaid_seats
router = APIRouter()

@router.get("/", response_model=List[BookingResponse])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return bookings

@router.get("/me", response_model=List[MyBooking])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all bookings for the currently authenticated user."""
    try:
        logger.info(f"User {current_user.id} fetched booking history")
        
        # Query all bookings for current user with trip, bus, route, and seat details
        bookings = (
            db.query(Booking)
            .options(
                joinedload(Booking.trip)
                .joinedload(Trip.bus),
                joinedload(Booking.trip)
                .joinedload(Trip.route),
                joinedload(Booking.seat)
            )
            .filter(Booking.user_id == current_user.id)
            .order_by(Booking.booking_date.desc())  # Most recent first
            .all()
        )
        
        # Transform to response format matching MyBooking schema
        my_bookings = []
        for booking in bookings:
            trip = booking.trip
            bus = trip.bus if trip else None
            route = trip.route if trip else None
            
            my_booking = MyBooking(
                booking_id=booking.id,
                bus_name=bus.name if bus else "Unknown Bus",
                source=route.source_city if route else "Unknown",
                destination=route.destination_city if route else "Unknown",
                travel_date=trip.departure_time if trip else booking.booking_date,
                seat_numbers=[booking.seat.seat_number] if booking.seat else [],
                status=booking.status.value,  # Convert enum to string value
                total_price=booking.total_price
            )
            my_bookings.append(my_booking)
        
        return my_bookings
        
    except Exception as e:
        logger.error(f"Error fetching booking history for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch booking history")

@router.post("/", response_model=BookingSummary)
def create_booking(
    booking_data: BookingCreate, 
    background_tasks: BackgroundTasks,
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
        # Step 1: Lock the seats for update (pessimistic locking)
        # This prevents other transactions from modifying these rows until we commit
        seats = (
            db.query(Seat)
            .filter(Seat.id.in_(booking_data.seat_ids))
            .with_for_update(nowait=True)  # Lock rows, fail fast if already locked
            .all()
        )

        if len(seats) != len(booking_data.seat_ids):
            logger.error(
                f"Some seats not found. Requested: {booking_data.seat_ids}, "
                f"Found: {[s.id for s in seats]}"
            )
            raise HTTPException(status_code=400, detail="Some seats not found")

        # Step 2: Validate seats belong to correct bus and are available
        for seat in seats:
            # Check seat belongs to this trip's bus
            if seat.bus_id != trip.bus_id:
                logger.error(
                    f"Seat {seat.id} belongs to bus {seat.bus_id}, "
                    f"but trip uses bus {trip.bus_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Seat {seat.id} does not belong to this trip's bus"
                )

            # Step 3: Check if seat is still available after acquiring lock
            # If another transaction booked it while we were waiting, is_available will be False
            if not seat.is_available:
                logger.warning(
                    f"Seat {seat.id} ({seat.seat_number}) is no longer available "
                    f"after lock acquisition"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Seat {seat.seat_number} is no longer available."
                )

        # Step 4: Double-check for any active bookings in the database
        # This prevents race conditions where booking was created but seat flag not updated
        existing_bookings = (
            db.query(Booking)
            .filter(
                Booking.trip_id == booking_data.trip_id,
                Booking.seat_id.in_(booking_data.seat_ids),
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            )
            .all()
        )

        if existing_bookings:
            booked_seat_ids = [b.seat_id for b in existing_bookings]
            booked_seats = db.query(Seat).filter(Seat.id.in_(booked_seat_ids)).all()
            seat_numbers = [s.seat_number for s in booked_seats]

            logger.warning(
                f"Seats already have active bookings: {booked_seat_ids} ({seat_numbers})"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Seat {seat_numbers[0]} is no longer available."
            )

        # Step 5: Create bookings for each seat within the transaction (Atomic)
        created_bookings = []
        for seat in seats:
            # Atomic: Mark seat as unavailable within same transaction
            seat.is_available = False
            logger.info(f"[Atomic] Marked seat {seat.id} ({seat.seat_number}) is_available=False")
            
            # Calculate pricing (base price + 10% premium for window seats)
            base_price = trip.price
            window_premium = base_price * Decimal('0.10') if seat.is_window else Decimal('0')
            total_price = base_price + window_premium
            
            logger.info(f"[PRICING] Seat {seat.id} ({seat.seat_number}): Base={base_price}, Window={seat.is_window}, Premium={window_premium}, Total={total_price}")
            
            # Create booking
            booking = Booking(
                user_id=user_id,
                trip_id=booking_data.trip_id,
                seat_id=seat.id,
                status=BookingStatus.PENDING,
                total_price=total_price
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

        # Invalidate Redis cache for this trip to ensure fresh seat availability data
        # Get trip details for cache invalidation (source, destination, travel_date)
        try:
            # Load route relationship if not already loaded
            trip_with_route = db.query(Trip).options(joinedload(Trip.route)).filter(Trip.id == booking_data.trip_id).first()
            if trip_with_route and trip_with_route.route:
                source = trip_with_route.route.source_city
                destination = trip_with_route.route.destination_city
                travel_date_str = trip_with_route.departure_time.date().isoformat()

                invalidate_booking_cache(booking_data.trip_id, source, destination, travel_date_str)
                logger.info(f"[CACHE INVALIDATE] Clearing stale data for Trip ID {booking_data.trip_id}")
            else:
                logger.warning(f"[CACHE INVALIDATE] Could not load route for trip {booking_data.trip_id}, skipping search cache invalidation")
        except Exception as e:
            # Log error but don't fail the booking - Redis failure shouldn't rollback DB commit
            logger.error(f"[CACHE INVALIDATE] Error invalidating cache for trip {booking_data.trip_id}: {type(e).__name__}: {e}")
            # Continue with the response - booking is already committed

        # Trigger Celery task to release unpaid seats after 10 minutes
        booking_ids = [b.id for b in created_bookings]
        release_unpaid_seats.apply_async(args=[booking_ids], countdown=600)  # 600 seconds = 10 minutes
        logger.info(f"Scheduled release_unpaid_seats task for booking_ids: {booking_ids} (in 10 minutes)")
        
        # Trigger "The Reaper" - cleanup expired pending bookings via BackgroundTasks
        # Note: For larger production scale, this should be moved to Celery Beat cron job
        background_tasks.add_task(cleanup_expired_bookings, db)
        logger.info("[REAPER] Triggered cleanup of expired pending bookings")
        
        # Log successful booking creation with structured data
        seat_ids = [b.seat_id for b in created_bookings]
        logger.info(f"BOOKING_CREATED: user_id={user_id}, trip_id={booking_data.trip_id}, booking_ids={booking_ids}, seat_ids={seat_ids}")
        
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
        # Check for lock-related errors (concurrency conflicts)
        error_str = str(e).lower()
        if "lock" in error_str or "could not obtain" in error_str or "resource busy" in error_str or "nowait" in error_str:
            logger.error(f"Lock conflict during booking: {e}")
            raise HTTPException(
                status_code=400,
                detail="This seat is currently being booked by another user. Please try again in a moment."
            )
        # Handle serialization errors and other database concurrency issues
        from sqlalchemy.exc import OperationalError, IntegrityError
        if isinstance(e, (OperationalError, IntegrityError)):
            logger.error(f"Database serialization error during booking: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=400,
                detail="This seat is currently being booked by another user. Please try again in a moment."
            )
        logger.error(f"Exception in create_booking: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")



@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific booking by ID."""
    logger.info(f"[DEBUG] Fetching booking {booking_id} for response validation")
    
    try:
        # Use joinedload to ensure all related data is loaded
        booking = (
            db.query(Booking)
            .options(joinedload(Booking.trip), joinedload(Booking.seat))
            .filter(Booking.id == booking_id)
            .first()
        )
        
        # Explicitly check if booking exists
        if not booking:
            logger.warning(f"[DEBUG] Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Optional: Check if user owns this booking (security)
        if booking.user_id != current_user.id:
            logger.warning(f"[DEBUG] User {current_user.id} trying to access booking {booking_id} owned by user {booking.user_id}")
            raise HTTPException(status_code=403, detail="Access denied: You can only view your own bookings")
        
        logger.info(f"[DEBUG] Successfully retrieved booking {booking_id} for user {current_user.id}")
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Error fetching booking {booking_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch booking: {str(e)}")

@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, booking: BookingUpdate):
    # Placeholder - implement actual booking update
    pass

@router.patch("/{booking_id}/confirm", response_model=dict)
def confirm_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm a booking (mark as CONFIRMED to prevent auto-release)."""
    try:
        logger.info(f"Attempting to confirm booking {booking_id} for user {current_user.id}")
        
        # Fetch the booking
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            logger.warning(f"Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify ownership
        if booking.user_id != current_user.id:
            logger.warning(f"User {current_user.id} cannot confirm booking {booking_id} (belongs to user {booking.user_id})")
            raise HTTPException(status_code=403, detail="You can only confirm your own bookings")
        
        # Check current status
        if booking.status == BookingStatus.CONFIRMED:
            logger.info(f"Booking {booking_id} is already confirmed")
            return {"message": "Booking is already confirmed", "booking_id": booking_id, "status": "CONFIRMED"}
        
        if booking.status == BookingStatus.CANCELLED:
            logger.warning(f"Cannot confirm booking {booking_id} - it has been cancelled/expired")
            raise HTTPException(status_code=400, detail="Cannot confirm a cancelled/expired booking")
        
        # Update status to CONFIRMED
        booking.status = BookingStatus.CONFIRMED
        db.commit()
        db.refresh(booking)
        
        # Log successful booking confirmation with structured data
        app_logger.info(f"BOOKING_CONFIRMED: user_id={current_user.id}, booking_id={booking_id}, trip_id={booking.trip_id}, seat_id={booking.seat_id}")
        logger.info(f"Successfully confirmed booking {booking_id}")
        
        return {
            "message": "Booking confirmed successfully",
            "booking_id": booking.id,
            "status": "CONFIRMED",
            "trip_id": booking.trip_id,
            "seat_id": booking.seat_id,
            "total_price": float(booking.total_price) if booking.total_price else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in confirm_booking: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")


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
