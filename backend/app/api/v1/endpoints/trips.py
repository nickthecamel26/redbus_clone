from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.session import get_db
from app.models.trip import Trip
from app.models.route import Route
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.booking import Booking, BookingStatus
from app.schemas.trip import TripResponse, TripCreate, TripUpdate, TripSearchResult
from app.schemas.seat import SeatWithStatus, SeatWithPricing
from decimal import Decimal

router = APIRouter()

@router.get("/", response_model=List[TripResponse])
def get_trips():
    return []

@router.get("/search", response_model=List[TripSearchResult])
def search_trips(
    source: str = Query(..., description="Source city"),
    destination: str = Query(..., description="Destination city"),
    travel_date: date = Query(..., description="Travel date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Search for trips by source, destination, and date with available seat counts."""
    # Calculate start and end of the travel date (naive datetime for comparison with DB)
    start_of_day = datetime.combine(travel_date, datetime.min.time())
    end_of_day = datetime.combine(travel_date, datetime.max.time())
    
    # Query trips matching criteria
    trips = (
        db.query(Trip)
        .join(Route)
        .join(Bus)
        .filter(Route.source_city.ilike(f"%{source}%"))
        .filter(Route.destination_city.ilike(f"%{destination}%"))
        .filter(Trip.departure_time >= start_of_day)
        .filter(Trip.departure_time <= end_of_day)
        .options(joinedload(Trip.route), joinedload(Trip.bus))
        .all()
    )
    
    # Build search results with available seat counts
    results = []
    for trip in trips:
        # Get total seats for this trip's bus
        total_seats = db.query(Seat).filter(Seat.bus_id == trip.bus_id).count()
        
        # Get booked seats count for this trip
        booked_seats = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).count()
        
        # Calculate available seats
        available_seats = total_seats - booked_seats
        
        result = TripSearchResult(
            id=trip.id,
            bus_name=trip.bus.name if trip.bus else "Unknown",
            departure_time=trip.departure_time,
            arrival_time=trip.arrival_time,
            available_seats=available_seats,
            price=Decimal(str(trip.price)) if trip.price else Decimal("0.00")
        )
        results.append(result)
    
    return results

@router.post("/", response_model=TripResponse)
def create_trip(trip: TripCreate):
    # Placeholder - implement actual trip creation
    pass

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int):
    # Placeholder - implement actual trip retrieval
    pass

@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: int, trip: TripUpdate):
    # Placeholder - implement actual trip update
    pass

@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    # Placeholder - implement actual trip deletion
    pass

@router.get("/{trip_id}/seats", response_model=List[SeatWithPricing])
def get_trip_seats(trip_id: int, db: Session = Depends(get_db)):
    """Get all seats for a trip with dynamic pricing and row/column layout."""
    try:
        print(f"[DEBUG] Fetching seats for trip_id={trip_id}")
        
        # Get the trip with its bus
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            print(f"[DEBUG] Trip {trip_id} not found")
            raise HTTPException(status_code=404, detail="Trip not found")
        
        print(f"[DEBUG] Found trip with bus_id={trip.bus_id}, price={trip.price}")
        
        # Get all seats for the trip's bus
        seats = db.query(Seat).filter(Seat.bus_id == trip.bus_id).order_by(Seat.row, Seat.column).all()
        print(f"[DEBUG] Found {len(seats)} seats for bus_id={trip.bus_id}")
        
        # Get booked seat IDs for this trip (confirmed or pending bookings)
        booked_seat_ids = {
            booking.seat_id for booking in db.query(Booking).filter(
                Booking.trip_id == trip_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            ).all()
        }
        print(f"[DEBUG] Found {len(booked_seat_ids)} booked seats")
        
        # Base price from trip
        base_price = Decimal(str(trip.price)) if trip.price else Decimal("0.00")
        
        # Map seats with availability status and dynamic pricing
        seat_status_list = []
        for seat in seats:
            is_available = seat.id not in booked_seat_ids
            
            # Calculate dynamic price: 10% premium for window seats
            if seat.is_window:
                dynamic_price = base_price * Decimal("1.10")
            else:
                dynamic_price = base_price
            
            # Round to 2 decimal places
            dynamic_price = dynamic_price.quantize(Decimal("0.01"))
            
            seat_data = {
                "id": seat.id,
                "bus_id": seat.bus_id,
                "seat_number": seat.seat_number,
                "row": seat.row,
                "column": seat.column,
                "is_sleeper": seat.is_sleeper,
                "is_window": seat.is_window,
                "deck": seat.deck,
                "is_available": is_available,
                "base_price": base_price,
                "dynamic_price": dynamic_price
            }
            seat_status_list.append(SeatWithPricing(**seat_data))
        
        # Group seats by row for better visualization
        seats_by_row = {}
        for seat in seat_status_list:
            row = seat.row
            if row not in seats_by_row:
                seats_by_row[row] = []
            seats_by_row[row].append(seat)
        
        print(f"[DEBUG] Returning {len(seat_status_list)} seats grouped into {len(seats_by_row)} rows")
        
        return seat_status_list
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in get_trip_seats: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")
