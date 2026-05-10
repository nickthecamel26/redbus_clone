"""Seed data script for RedBus Clone"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.base import Base  # noqa: F401  (ensures models are registered)
from app.models import User, Bus, BusType, Route, Trip, Seat
from app.core.security import get_password_hash

# Database connection
# Prefer the DATABASE_URL environment variable (set in docker-compose for the
# backend service). Fall back to the Docker service hostname `postgres` so the
# script works when run via `docker compose exec backend python seed_data.py`.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/redbus",
)
print(f"[seed] Using DATABASE_URL host: {DATABASE_URL.split('@')[-1]}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def generate_standard_36_seats(bus_id):
    """Generate exactly 36 seats for a bus with standardized layout."""
    seats = []
    
    # Lower Deck (Deck 0): Rows 1-5, Columns 1-4 (20 seats)
    for row in range(1, 6):  # Rows 1-5
        for col in range(1, 5):  # Columns 1-4
            # Window seats are columns 1 and 4 (A and D)
            is_window = (col == 1 or col == 4)
            seat = Seat(
                bus_id=bus_id,
                seat_number=f"{row}{chr(64 + col)}",  # e.g., 1A, 1B, 1C, 1D
                row=row,
                column=col,
                is_sleeper=True,  # All AC Sleeper seats
                is_window=is_window,
                deck=0,  # Lower deck
                is_available=True
            )
            seats.append(seat)
    
    # Upper Deck (Deck 1): Rows 6-9, Columns 1-4 (16 seats)
    for row in range(6, 10):  # Rows 6-9
        for col in range(1, 5):  # Columns 1-4
            # Window seats are columns 1 and 4 (A and D)
            is_window = (col == 1 or col == 4)
            seat = Seat(
                bus_id=bus_id,
                seat_number=f"{row}{chr(64 + col)}",  # e.g., 6A, 6B, 6C, 6D
                row=row,
                column=col,
                is_sleeper=True,  # All AC Sleeper seats
                is_window=is_window,
                deck=1,  # Upper deck
                is_available=True
            )
            seats.append(seat)
    
    return seats

def generate_40_seats_2x2_layout(bus_id):
    """Generate 40 seats in a 2x2 layout (10 rows) for Trip 1."""
    seats = []
    
    # 10 rows, 4 columns (2x2 layout: 2 seats on left, aisle, 2 seats on right)
    # Seat arrangement: A  B | aisle | C  D
    for row in range(1, 11):  # Rows 1-10
        for col in range(1, 5):  # Columns 1-4 (A, B, C, D)
            seat_letter = chr(64 + col)  # A, B, C, D
            # Window seats: A (col 1) and D (col 4)
            is_window = (col == 1 or col == 4)
            seat = Seat(
                bus_id=bus_id,
                seat_number=f"{row}{seat_letter}",  # e.g., 1A, 1B, 1C, 1D
                row=row,
                column=col,
                is_sleeper=False,  # AC Seater
                is_window=is_window,
                deck=0,  # Single deck
                is_available=True
            )
            seats.append(seat)
    
    return seats


def seed_data():
    db = SessionLocal()
    
    try:
        # Reset all data and sequences
        print("Resetting database...")
        db.execute(text("""
            TRUNCATE TABLE bookings, seats, trips, routes, buses, users 
            RESTART IDENTITY CASCADE
        """))
        db.commit()
        print("Database reset complete")
        
        print("Seeding database...")
        
        # Create Users (ensuring id=1 for default user)
        print("Creating users...")
        admin = User(
            email="admin@redbus.com",
            hashed_password=get_password_hash("password123"),
            full_name="Admin User",
        )
        user = User(
            email="user@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Regular User",
        )
        nikhil = User(
            email="nikhil_test_final_v2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Nikhil Test",
        )
        db.add_all([admin, user, nikhil])
        db.flush()
        # Explicitly set IDs to ensure user_id=1 exists
        db.execute(text("UPDATE users SET id = 1 WHERE email = 'admin@redbus.com'"))
        db.execute(text("UPDATE users SET id = 2 WHERE email = 'user@example.com'"))
        db.execute(text("UPDATE users SET id = 3 WHERE email = 'nikhil_test_final_v2@example.com'"))
        db.execute(text("SELECT setval('users_id_seq', 3)"))
        db.flush()
        print(
            "Created users: "
            "admin@redbus.com (id=1), "
            "user@example.com (id=2), "
            "nikhil_test_final_v2@example.com (id=3)"
        )
        
        # Create Buses (16 diverse operators across South India)
        print("Creating buses...")
        buses = [
            Bus(name="Theni Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="Madurai Express - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
            Bus(name="Chennai King - Non-AC Sleeper", bus_type=BusType.NON_AC_SLEEPER, total_seats=36),
            Bus(name="South India Travels - Non-AC Seater", bus_type=BusType.NON_AC_SEATER, total_seats=40),
            Bus(name="KPN Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="SRS Travels - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
            Bus(name="Parveen Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="VRL Travels - Non-AC Sleeper", bus_type=BusType.NON_AC_SLEEPER, total_seats=36),
            Bus(name="Kallada Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="Orange Tours - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
            Bus(name="Sharma Transport - Non-AC Seater", bus_type=BusType.NON_AC_SEATER, total_seats=40),
            Bus(name="YBM Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="Universal Travels - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
            Bus(name="National Travels - Non-AC Sleeper", bus_type=BusType.NON_AC_SLEEPER, total_seats=36),
            Bus(name="Komitla Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="GreenLine - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
        ]
        db.add_all(buses)
        db.flush()
        print(f"Created {len(buses)} buses")
        
        # Cleanup: Delete all existing seats
        print("Cleaning up existing seats...")
        db.query(Seat).delete()
        db.flush()
        print("  Deleted all existing seats")
        
        # Create seats for each bus based on capacity
        print("Creating seats for each bus...")
        for bus in buses:
            if bus.total_seats == 40:
                # 40-seat bus: Use 2x2 layout (10 rows)
                seats = generate_40_seats_2x2_layout(bus.id)
                print(f"  Created {len(seats)} seats in 2x2 layout for {bus.name}")
            else:
                # Other buses: Use standard 36-seat layout
                seats = generate_standard_36_seats(bus.id)
                print(f"  Created {len(seats)} seats in standard layout for {bus.name}")
            db.add_all(seats)
        
        db.flush()
        
        # Create Routes (12 city pairs × 2 directions = 24 routes across 22 South India cities)
        print("Creating routes...")
        # Each tuple: (source, destination, distance_km, base_price)
        route_definitions = [
            ("Chennai", "Madurai", 450.00, 899.00),
            ("Chennai", "Bangalore", 350.00, 749.00),
            ("Chennai", "Coimbatore", 510.00, 999.00),
            ("Chennai", "Hyderabad", 630.00, 1199.00),
            ("Chennai", "Pondicherry", 165.00, 399.00),
            ("Chennai", "Trichy", 330.00, 649.00),
            ("Bangalore", "Mysore", 145.00, 449.00),
            ("Bangalore", "Hyderabad", 570.00, 1099.00),
            ("Bangalore", "Mangalore", 350.00, 849.00),
            ("Bangalore", "Tirupati", 250.00, 599.00),
            ("Coimbatore", "Kochi", 190.00, 499.00),
            ("Madurai", "Theni", 75.00, 199.00),
            ("Madurai", "Trivandrum", 305.00, 749.00),
            ("Madurai", "Tirunelveli", 165.00, 399.00),
            ("Hyderabad", "Vijayawada", 275.00, 649.00),
            ("Hyderabad", "Visakhapatnam", 620.00, 1299.00),
            ("Kochi", "Trivandrum", 220.00, 549.00),
            ("Kochi", "Calicut", 185.00, 449.00),
            ("Mangalore", "Calicut", 235.00, 599.00),
            ("Salem", "Coimbatore", 160.00, 399.00),
            ("Vijayawada", "Visakhapatnam", 350.00, 849.00),
            ("Tirupati", "Nellore", 135.00, 349.00),
            ("Hubli", "Belgaum", 105.00, 299.00),
            ("Kanyakumari", "Trivandrum", 85.00, 249.00),
        ]

        routes = []
        base_prices = {}
        for src, dst, distance, price in route_definitions:
            # Forward route
            routes.append(Route(source_city=src, destination_city=dst, distance_km=distance))
            base_prices[f"{src}-{dst}"] = price
            # Reverse route (same distance + price)
            routes.append(Route(source_city=dst, destination_city=src, distance_km=distance))
            base_prices[f"{dst}-{src}"] = price

        db.add_all(routes)
        db.flush()
        print(f"Created {len(routes)} routes across {len({r.source_city for r in routes} | {r.destination_city for r in routes})} cities")
        
        # Create Trips for the next 14 days so future-dated searches (e.g. May 16th)
        # always land on at least one bus per route per time-of-day.
        print("Creating trips...")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        DAYS_AHEAD = 14

        trips = []
        trip_times = [
            ("06:00", "14:00"),  # Morning
            ("14:00", "22:00"),  # Afternoon
            ("21:00", "05:00"),  # Night (next day)
        ]

        for day_offset in range(DAYS_AHEAD):
            day_base = today + timedelta(days=day_offset)
            for route_index, route in enumerate(routes):
                route_key = f"{route.source_city}-{route.destination_city}"
                base_price = base_prices.get(route_key, 500.00)

                for slot_index, (dep_time, arr_time) in enumerate(trip_times):
                    dep_hour, dep_min = map(int, dep_time.split(':'))
                    arr_hour, arr_min = map(int, arr_time.split(':'))

                    departure = day_base + timedelta(hours=dep_hour, minutes=dep_min)
                    arrival = day_base + timedelta(hours=arr_hour, minutes=arr_min)

                    # If arrival is before departure, the trip lands the next day.
                    if arrival <= departure:
                        arrival += timedelta(days=1)

                    # Rotate buses across day + slot + route so each combo gets variety.
                    bus = buses[(day_offset + slot_index + route_index) % len(buses)]

                    trip = Trip(
                        bus_id=bus.id,
                        route_id=route.id,
                        departure_time=departure,
                        arrival_time=arrival,
                        price=base_price,
                    )
                    trips.append(trip)

        db.add_all(trips)
        db.flush()
        last_day = (today + timedelta(days=DAYS_AHEAD - 1)).date()
        print(f"Created {len(trips)} trips across {DAYS_AHEAD} days (through {last_day.isoformat()})")
        
        # Commit all changes
        db.commit()
        print("✅ Database seeded successfully!")
        
        # Print summary
        print("\n--- Seed Data Summary ---")
        print(f"Users: {db.query(User).count()}")
        print(f"Buses: {db.query(Bus).count()}")
        print(f"Seats: {db.query(Seat).count()}")
        print(f"Routes: {db.query(Route).count()}")
        print(f"Trips: {db.query(Trip).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
