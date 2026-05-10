import logging
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.db.session import get_db
from app.models.trip import Trip
from app.models.route import Route
from app.models.bus import Bus, BusType
from app.models.seat import Seat
from app.models.booking import Booking, BookingStatus
from app.schemas.trip import TripResponse, TripCreate, TripUpdate, TripSearchResult, BulkScheduleRequest
from app.schemas.seat import SeatWithStatus, SeatWithPricing
from app.core.redis import get_cached_seats, set_cached_seats, get_cached_search_results, set_cached_search_results, invalidate_booking_cache, clear_search_cache
from app.api.deps import search_rate_limiter
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/locations", response_model=List[str])
def get_trip_locations(db: Session = Depends(get_db)) -> List[str]:
    """Return a sorted, de-duplicated list of every city referenced as either
    a source or destination across all routes.

    Powers the frontend autocomplete on the home page search bar.
    Example response: ["Bangalore", "Chennai", "Coimbatore", ...]
    """
    sources = db.query(Route.source_city).distinct().all()
    destinations = db.query(Route.destination_city).distinct().all()

    cities = {row[0] for row in sources if row[0]} | {row[0] for row in destinations if row[0]}
    sorted_cities = sorted(cities)

    logger.info(f"[trips/locations] Returning {len(sorted_cities)} unique city names")
    return sorted_cities


@router.get("/", response_model=List[TripResponse])
def get_trips(db: Session = Depends(get_db)):
    """Get all upcoming trips (departure_time >= now)."""
    now = datetime.now()
    trips = (
        db.query(Trip)
        .options(joinedload(Trip.bus), joinedload(Trip.route))
        .filter(Trip.departure_time >= now)
        .order_by(Trip.departure_time)
        .all()
    )
    logger.info(f"Retrieved {len(trips)} upcoming trips")
    return trips

@router.get("/search", response_model=List[TripSearchResult])
def search_trips(
    request: Request,
    response: Response,
    source: str = Query(..., description="Source city"),
    destination: str = Query(..., description="Destination city"),
    travel_date: date = Query(..., description="Travel date (YYYY-MM-DD)"),
    bus_types: Optional[List[str]] = Query(None, description="Filter by bus types (e.g., AC Sleeper, Non-AC Seater)"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    departure_window: Optional[str] = Query(None, description="Departure window: morning, afternoon, evening, night"),
    sort_by: Optional[str] = Query("earliest", description="Sort by: price_asc, price_desc, earliest, latest"),
    db: Session = Depends(get_db),
    rate_limit: None = Depends(search_rate_limiter)
):
    """Search for trips by source, destination, and date with available seat counts."""
    print(f"DEBUG: Entered search_trips route with source={source}, destination={destination}, travel_date={travel_date}")

    # Cache-Aside Pattern: Check Redis cache first
    travel_date_str = travel_date.isoformat()
    cached_results = get_cached_search_results(source, destination, travel_date_str, TripSearchResult)
    if cached_results is not None:
        print(f"[CACHE HIT] Returning cached search results for {source} -> {destination} on {travel_date_str}")
        return cached_results

    print(f"[CACHE MISS] No cached data found for {source} -> {destination} on {travel_date_str}, querying database")

    # Calculate start and end of the travel date (naive datetime for comparison with DB)
    start_of_day = datetime.combine(travel_date, datetime.min.time())
    end_of_day = datetime.combine(travel_date, datetime.max.time())
    
    # Build dynamic query with filters
    print(f"[DEBUG] Search parameters: source='{source}', destination='{destination}', start_of_day={start_of_day}, end_of_day={end_of_day}")
    print(f"[DEBUG] Filters - bus_types={bus_types}, min_price={min_price}, max_price={max_price}, departure_window={departure_window}, sort_by={sort_by}")
    
    # Base query with joins
    query = (
        db.query(Trip)
        .join(Route)
        .join(Bus)
        .filter(Route.source_city.ilike(f"%{source}%"))
        .filter(Route.destination_city.ilike(f"%{destination}%"))
        .filter(Trip.departure_time.between(start_of_day, end_of_day))
        .options(joinedload(Trip.route), joinedload(Trip.bus))
    )
    
    # Apply bus type filter
    if bus_types:
        bus_type_conditions = []
        for bus_type in bus_types:
            if "AC Sleeper" in bus_type:
                bus_type_conditions.append(Bus.bus_type == BusType.AC_SLEEPER)
            elif "Non-AC Sleeper" in bus_type:
                bus_type_conditions.append(Bus.bus_type == BusType.NON_AC_SLEEPER)
            elif "AC Seater" in bus_type:
                bus_type_conditions.append(Bus.bus_type == BusType.AC_SEATER)
            elif "Non-AC Seater" in bus_type:
                bus_type_conditions.append(Bus.bus_type == BusType.NON_AC_SEATER)
        
        if bus_type_conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*bus_type_conditions))
    
    # Apply price range filter
    if min_price is not None:
        query = query.filter(Trip.price >= float(min_price))
    
    if max_price is not None:
        query = query.filter(Trip.price <= float(max_price))
    
    # Apply departure window filter
    if departure_window:
        morning_start = start_of_day.replace(hour=6, minute=0)
        morning_end = start_of_day.replace(hour=12, minute=0)
        afternoon_start = start_of_day.replace(hour=12, minute=0)
        afternoon_end = start_of_day.replace(hour=18, minute=0)
        evening_start = start_of_day.replace(hour=18, minute=0)
        evening_end = start_of_day.replace(hour=23, minute=59)
        night_start = start_of_day.replace(hour=0, minute=0)
        night_end = start_of_day.replace(hour=6, minute=0)
        
        from sqlalchemy import or_
        if departure_window.lower() == "morning":
            query = query.filter(Trip.departure_time.between(morning_start, morning_end))
        elif departure_window.lower() == "afternoon":
            query = query.filter(Trip.departure_time.between(afternoon_start, afternoon_end))
        elif departure_window.lower() == "evening":
            query = query.filter(Trip.departure_time.between(evening_start, evening_end))
        elif departure_window.lower() == "night":
            query = query.filter(Trip.departure_time.between(night_start, night_end))
    
    # Apply sorting
    if sort_by:
        if sort_by.lower() == "price_asc":
            query = query.order_by(Trip.price.asc())
        elif sort_by.lower() == "price_desc":
            query = query.order_by(Trip.price.desc())
        elif sort_by.lower() == "earliest":
            query = query.order_by(Trip.departure_time.asc())
        elif sort_by.lower() == "latest":
            query = query.order_by(Trip.departure_time.desc())
    else:
        # Default sort by earliest departure
        query = query.order_by(Trip.departure_time.asc())
    
    # Execute query
    trips = query.all()
    
    print(f"[DEBUG] Found {len(trips)} trips before filtering")
    
    # Debug: Print route information for found trips
    for trip in trips:
        print(f"[DEBUG] Found Trip {trip.id}: Route='{trip.route.source_city} -> {trip.route.destination_city}', Departure={trip.departure_time}, Bus='{trip.bus.name}'")
    
    # Build search results with available seat counts
    results = []
    print(f"[DEBUG] Processing {len(trips)} trips for search results")
    
    for trip in trips:
        # Get total seats for this trip's bus
        total_seats = db.query(Seat).filter(Seat.bus_id == trip.bus_id).count()

        # Get occupied seats count for this trip (both CONFIRMED and PENDING bookings)
        occupied_seats = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).count()

        # Calculate available seats
        available_seats = total_seats - occupied_seats

        # Debug logging for seat availability
        print(f"[DEBUG] Trip {trip.id}: Total={total_seats}, Occupied(Confirmed+Pending)={occupied_seats}, Available={available_seats}")
        
        result = TripSearchResult(
            id=trip.id,
            bus_name=trip.bus.name if trip.bus else "Unknown",
            departure_time=trip.departure_time,
            arrival_time=trip.arrival_time,
            available_seats=available_seats,
            price=Decimal(str(trip.price)) if trip.price else Decimal("0.00")
        )
        results.append(result)

    # Cache-Aside Pattern: Store result in Redis with 300s TTL (5 minutes)
    set_cached_search_results(source, destination, travel_date_str, results, ttl=300)
    print(f"[CACHE SET] Stored {len(results)} search results in cache for {source} -> {destination} on {travel_date_str}")

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
    print(f"DEBUG: Entered get_trip_seats route with trip_id={trip_id}")
    try:
        print(f"[DEBUG] Fetching seats for trip_id={trip_id}")

        # Cache-Aside Pattern: Check Redis cache first
        cached_seats = get_cached_seats(trip_id, SeatWithPricing)
        if cached_seats is not None:
            print(f"[CACHE HIT] Returning cached seats for trip_id={trip_id}")
            # TypeAdapter already returns list of SeatWithPricing models
            return cached_seats

        print(f"[CACHE MISS] No cached data found for trip_id={trip_id}, querying database")
        
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

        # Cache-Aside Pattern: Store result in Redis with 60s TTL
        # Pass SeatWithPricing models directly - TypeAdapter handles serialization
        set_cached_seats(trip_id, seat_status_list, ttl=60)
        print(f"[CACHE SET] Stored {len(seat_status_list)} seats in cache for trip_id={trip_id}")

        return seat_status_list
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in get_trip_seats: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}: {e}")

@router.post("/bulk-schedule", response_model=List[TripResponse])
def bulk_schedule_trips(request: BulkScheduleRequest, db: Session = Depends(get_db)):
    """Schedule multiple trips in bulk for a bus on a route over several days."""
    logger.info(f"[SCHEDULER] Starting bulk schedule: Bus {request.bus_id}, Route {request.route_id}, {request.number_of_days} days")
    
    try:
        # Validate bus and route exist
        bus = db.query(Bus).filter(Bus.id == request.bus_id).first()
        if not bus:
            logger.warning(f"[SCHEDULER] Bus {request.bus_id} not found")
            raise HTTPException(status_code=404, detail=f"Bus {request.bus_id} not found")
        
        route = db.query(Route).filter(Route.id == request.route_id).first()
        if not route:
            logger.warning(f"[SCHEDULER] Route {request.route_id} not found")
            raise HTTPException(status_code=404, detail=f"Route {request.route_id} not found")
        
        # Determine price (use provided base_price or fallback to route-based calculation)
        if request.base_price:
            base_price = request.base_price
        else:
            # Simple price calculation: distance_km * 2 (can be enhanced)
            base_price = Decimal(str(route.distance_km)) * Decimal('2')
        
        created_trips = []
        
        # Generate trips for each day
        for day_offset in range(request.number_of_days):
            current_date = request.start_date + timedelta(days=day_offset)
            
            # Calculate departure and arrival times
            departure_datetime = datetime.combine(current_date, request.departure_time_daily)
            arrival_datetime = departure_datetime + timedelta(hours=request.travel_duration_hours)
            
            # Create trip
            trip = Trip(
                bus_id=request.bus_id,
                route_id=request.route_id,
                departure_time=departure_datetime,
                arrival_time=arrival_datetime,
                price=base_price
            )
            
            db.add(trip)
            created_trips.append(trip)
        
        # Commit all trips
        db.commit()
        
        # Refresh trips to get IDs and relationships
        for trip in created_trips:
            db.refresh(trip)
        
        # Clear search cache for all scheduled dates to ensure new trips appear immediately
        try:
            # Clear cache for each day that was scheduled
            for day_offset in range(request.number_of_days):
                current_date = request.start_date + timedelta(days=day_offset)
                date_str = current_date.isoformat()
                
                # Clear search cache for this specific route and date
                clear_search_cache(
                    source=route.source_city,
                    destination=route.destination_city,
                    date=date_str
                )
            
            logger.info(f"[SCHEDULER] Cleared search cache for {request.number_of_days} days on route {route.source_city} -> {route.destination_city}")
        except Exception as e:
            logger.warning(f"[SCHEDULER] Cache clearing failed: {type(e).__name__}: {e}")
        
        logger.info(f"[SCHEDULER] Generated {len(created_trips)} trips for Bus {request.bus_id} on Route {request.route_id}")
        return created_trips
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[SCHEDULER] Error in bulk schedule: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk schedule failed: {str(e)}")
