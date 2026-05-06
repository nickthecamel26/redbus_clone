"""Seed data script for RedBus Clone"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models import User, Bus, BusType, Route, Trip, Seat
from app.db.session import SessionLocal
from sqlalchemy import text

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/redbus"
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
        admin = User(email="admin@redbus.com", hashed_password="hashed_password", full_name="Admin User")
        user = User(email="user@example.com", hashed_password="hashed_password", full_name="Regular User")
        db.add_all([admin, user])
        db.flush()
        # Explicitly set IDs to ensure user_id=1 exists
        db.execute(text("UPDATE users SET id = 1 WHERE email = 'admin@redbus.com'"))
        db.execute(text("UPDATE users SET id = 2 WHERE email = 'user@example.com'"))
        db.execute(text("SELECT setval('users_id_seq', 2)"))
        db.flush()
        print(f"Created users: admin@redbus.com (id=1), user@example.com (id=2)")
        
        # Create Buses
        print("Creating buses...")
        buses = [
            Bus(name="Theni Travels - AC Sleeper", bus_type=BusType.AC_SLEEPER, total_seats=36),
            Bus(name="Madurai Express - AC Seater", bus_type=BusType.AC_SEATER, total_seats=40),
            Bus(name="Chennai King - Non-AC Sleeper", bus_type=BusType.NON_AC_SLEEPER, total_seats=30),
            Bus(name="South India Travels - Non-AC Seater", bus_type=BusType.NON_AC_SEATER, total_seats=45),
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
        
        # Create Routes
        print("Creating routes...")
        routes = [
            Route(source_city="Chennai", destination_city="Madurai", distance_km=450.00),
            Route(source_city="Madurai", destination_city="Chennai", distance_km=450.00),
            Route(source_city="Chennai", destination_city="Theni", distance_km=520.00),
            Route(source_city="Theni", destination_city="Chennai", distance_km=520.00),
            Route(source_city="Madurai", destination_city="Theni", distance_km=75.00),
            Route(source_city="Theni", destination_city="Madurai", distance_km=75.00),
        ]
        db.add_all(routes)
        db.flush()
        print(f"Created {len(routes)} routes")
        
        # Create Trips for today and tomorrow
        print("Creating trips...")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        trips = []
        trip_times = [
            ("06:00", "14:00"),  # Morning
            ("14:00", "22:00"),  # Afternoon
            ("21:00", "05:00"),  # Night (next day)
        ]
        
        base_prices = {
            "Chennai-Madurai": 899.00,
            "Madurai-Chennai": 899.00,
            "Chennai-Theni": 999.00,
            "Theni-Chennai": 999.00,
            "Madurai-Theni": 199.00,
            "Theni-Madurai": 199.00,
        }
        
        for route in routes:
            route_key = f"{route.source_city}-{route.destination_city}"
            base_price = base_prices.get(route_key, 500.00)
            
            for i, (dep_time, arr_time) in enumerate(trip_times):
                dep_hour, dep_min = map(int, dep_time.split(':'))
                arr_hour, arr_min = map(int, arr_time.split(':'))
                
                departure = today + timedelta(hours=dep_hour, minutes=dep_min)
                arrival = today + timedelta(hours=arr_hour, minutes=arr_min)
                
                # If arrival is before departure, add a day
                if arrival <= departure:
                    arrival += timedelta(days=1)
                
                # Use different buses for different times
                bus = buses[i % len(buses)]
                
                trip = Trip(
                    bus_id=bus.id,
                    route_id=route.id,
                    departure_time=departure,
                    arrival_time=arrival,
                    price=base_price
                )
                trips.append(trip)
        
        db.add_all(trips)
        db.flush()
        print(f"Created {len(trips)} trips")
        
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
