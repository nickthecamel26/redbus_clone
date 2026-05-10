#!/usr/bin/env python3
"""
Database seeding script for Redbus clone.
Populates PostgreSQL with realistic test data for development and testing.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from app.db.session import get_db
from app.models.user import User
from app.models.bus import Bus, BusType
from app.models.route import Route
from app.models.trip import Trip
from app.models.seat import Seat
from app.models.booking import Booking, BookingStatus
from app.core.security import get_password_hash

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/redbus")
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def reset_database():
    """Clear all data from tables."""
    print("[SEED] Resetting database...")
    db = SessionLocal()
    try:
        # Delete in order of dependencies
        db.query(Booking).delete()
        db.query(Trip).delete()
        db.query(Seat).delete()
        db.query(Route).delete()
        db.query(Bus).delete()
        db.query(User).delete()
        db.commit()
        print("[SEED] Database cleared successfully")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to reset database: {e}")
    finally:
        db.close()

def seed_users():
    """Create admin and customer users."""
    print("[SEED] Creating users...")
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"[SEED] Users already exist ({existing_users}), skipping user creation")
            return
        
        users = [
            User(
                email="admin@redbus.com",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True
            ),
            User(
                email="customer1@gmail.com",
                full_name="Rahul Kumar",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_superuser=False
            ),
            User(
                email="customer2@gmail.com",
                full_name="Priya Sharma",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_superuser=False
            ),
            User(
                email="customer3@gmail.com",
                full_name="Arun Patel",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_superuser=False
            ),
            User(
                email="customer4@gmail.com",
                full_name="Sneha Reddy",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_superuser=False
            ),
            User(
                email="customer5@gmail.com",
                full_name="Vijay Kumar",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                is_superuser=False
            )
        ]
        
        for user in users:
            db.add(user)
        
        db.commit()
        print(f"[SEED] Created {len(users)} users (1 admin + 5 customers)")
        
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to create users: {e}")
    finally:
        db.close()

def seed_buses():
    """Create buses with different types."""
    print("[SEED] Creating buses...")
    db = SessionLocal()
    try:
        # Check if buses already exist
        existing_buses = db.query(Bus).count()
        if existing_buses > 0:
            print(f"[SEED] Buses already exist ({existing_buses}), skipping bus creation")
            return
        
        buses = [
            Bus(
                name="Volvo AC Sleeper",
                bus_type=BusType.AC_SLEEPER,
                total_seats=40
            ),
            Bus(
                name="Non-AC Sleeper Express",
                bus_type=BusType.NON_AC_SLEEPER,
                total_seats=36
            ),
            Bus(
                name="AC Seater Premium",
                bus_type=BusType.AC_SEATER,
                total_seats=48
            ),
            Bus(
                name="Non-AC Seater Economy",
                bus_type=BusType.NON_AC_SEATER,
                total_seats=52
            ),
            Bus(
                name="Luxury AC Sleeper",
                bus_type=BusType.AC_SLEEPER,
                total_seats=32
            )
        ]
        
        for bus in buses:
            db.add(bus)
        
        db.commit()
        print(f"[SEED] Created {len(buses)} buses with varying types")
        
        # Generate seats for each bus
        for bus in buses:
            generate_seats_for_bus(db, bus.id, bus.total_seats, bus.bus_type)
        
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to create buses: {e}")
    finally:
        db.close()

def generate_seats_for_bus(db, bus_id: int, total_seats: int, bus_type: BusType):
    """Generate seats for a bus based on its type."""
    seats_created = 0
    
    # Determine seating layout
    if "Sleeper" in bus_type:
        seats_per_row = 2
        decks = 2
        seats_per_deck = total_seats // decks
    else:
        seats_per_row = 4
        decks = 1
        seats_per_deck = total_seats
    
    current_row = 1
    current_column = 1
    current_deck = 0
    
    for seat_num in range(1, total_seats + 1):
        # Determine seat number format
        if "Sleeper" in bus_type:
            deck_prefix = "L" if current_deck == 0 else "U"
            seat_number = f"{deck_prefix}{current_column}"
        else:
            row_letter = chr(64 + current_row)  # A, B, C, etc.
            seat_number = f"{row_letter}{current_column}"
        
        # Determine if window seat
        is_window = (current_column == 1 or current_column == seats_per_row)
        
        # Create seat
        seat = Seat(
            bus_id=bus_id,
            seat_number=seat_number,
            row=current_row,
            column=current_column,
            is_window=is_window,
            is_sleeper=("Sleeper" in bus_type),
            deck=current_deck,
            is_available=True
        )
        db.add(seat)
        seats_created += 1
        
        # Update position for next seat
        current_column += 1
        if current_column > seats_per_row:
            current_column = 1
            current_row += 1
            
            if "Sleeper" in bus_type and current_row > (seats_per_deck // seats_per_row):
                current_row = 1
                current_deck += 1
    
    db.commit()
    print(f"[SEED] Generated {seats_created} seats for bus {bus_id} ({bus_type})")

def seed_routes():
    """Create major routes."""
    print("[SEED] Creating routes...")
    db = SessionLocal()
    try:
        # Check if routes already exist
        existing_routes = db.query(Route).count()
        if existing_routes > 0:
            print(f"[SEED] Routes already exist ({existing_routes}), skipping route creation")
            return
        
        routes = [
            Route(
                source_city="Chennai",
                destination_city="Bangalore",
                distance_km=Decimal("350.5")
            ),
            Route(
                source_city="Chennai",
                destination_city="Madurai",
                distance_km=Decimal("460.8")
            ),
            Route(
                source_city="Madurai",
                destination_city="Coimbatore",
                distance_km=Decimal("210.3")
            ),
            Route(
                source_city="Bangalore",
                destination_city="Coimbatore",
                distance_km=Decimal("365.2")
            )
        ]
        
        for route in routes:
            db.add(route)
        
        db.commit()
        print(f"[SEED] Created {len(routes)} major routes")
        
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to create routes: {e}")
    finally:
        db.close()

def seed_trips():
    """Schedule trips for next 7 days."""
    print("[SEED] Creating trips for next 7 days...")
    db = SessionLocal()
    try:
        # Check if trips already exist
        existing_trips = db.query(Trip).count()
        if existing_trips > 0:
            print(f"[SEED] Trips already exist ({existing_trips}), skipping trip creation")
            return
        
        # Get all buses and routes
        buses = db.query(Bus).all()
        routes = db.query(Route).all()
        
        trips_created = 0
        start_date = date.today()
        
        for route in routes:
            for day_offset in range(7):  # Next 7 days
                current_date = start_date + timedelta(days=day_offset)
                
                # Create 2 trips per day (morning and night)
                for shift in ["morning", "night"]:
                    if shift == "morning":
                        departure_time = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=0))
                        travel_hours = 8.5
                    else:  # night
                        departure_time = datetime.combine(current_date, datetime.min.time().replace(hour=21, minute=30))
                        travel_hours = 9.0
                    
                    arrival_time = departure_time + timedelta(hours=travel_hours)
                    
                    # Assign buses to routes (rotate through available buses)
                    bus = buses[trips_created % len(buses)]
                    
                    # Calculate price (distance * 2.5)
                    base_price = route.distance_km * Decimal("2.5")
                    
                    trip = Trip(
                        bus_id=bus.id,
                        route_id=route.id,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        price=base_price
                    )
                    db.add(trip)
                    trips_created += 1
        
        db.commit()
        print(f"[SEED] Created {trips_created} trips for next 7 days")
        
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to create trips: {e}")
    finally:
        db.close()

def create_special_scenarios():
    """Create special test scenarios."""
    print("[SEED] Creating special scenarios...")
    db = SessionLocal()
    try:
        # Get a popular trip (first Chennai-Bangalore trip)
        popular_trip = (
            db.query(Trip)
            .join(Route)
            .filter(Route.source_city == "Chennai", Route.destination_city == "Bangalore")
            .first()
        )
        
        if not popular_trip:
            print("[SEED] No Chennai-Bangalore trip found for special scenarios")
            return
        
        # Get seats for this trip
        seats = db.query(Seat).filter(Seat.bus_id == popular_trip.bus_id).all()
        
        # Pre-book 80% of seats (highly popular scenario)
        seats_to_book = int(len(seats) * 0.8)
        customer_user = db.query(User).filter(User.email == "customer1@gmail.com").first()
        
        if not customer_user:
            print("[SEED] Customer1 not found for pre-booking")
            return
        
        bookings_created = 0
        for i, seat in enumerate(seats[:seats_to_book]):
            # Create confirmed booking for highly popular trip
            booking = Booking(
                user_id=customer_user.id,
                trip_id=popular_trip.id,
                seat_id=seat.id,
                status=BookingStatus.CONFIRMED,
                total_price=popular_trip.price + (popular_trip.price * Decimal("0.10") if seat.is_window else Decimal("0"))
            )
            
            # Mark seat as unavailable
            seat.is_available = False
            db.add(booking)
            bookings_created += 1
        
        db.commit()
        print(f"[SEED] Created {bookings_created} pre-bookings for highly popular trip (80% capacity)")
        
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to create special scenarios: {e}")
    finally:
        db.close()

def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="Seed database with test data")
    parser.add_argument("--reset", action="store_true", help="Reset database before seeding")
    args = parser.parse_args()
    
    print("[SEED] Starting database seeding...")
    
    if args.reset:
        reset_database()
    
    # Seed data in order of dependencies
    seed_users()
    seed_buses()
    seed_routes()
    seed_trips()
    create_special_scenarios()
    
    print("[SEED] Database seeding completed successfully!")
    print("[SEED] Ready for frontend API calls")

if __name__ == "__main__":
    main()
