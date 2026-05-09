from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.session import get_db
from app.models.bus import Bus, BusType
from app.models.seat import Seat
from app.schemas.bus import BusResponse, BusCreate, BusUpdate
from app.core.logger import logger

router = APIRouter()

def generate_seats_for_bus(db: Session, bus_id: int, total_seats: int, bus_type: BusType) -> int:
    """Generate seats for a bus based on its capacity and type."""
    logger.info(f"Generating {total_seats} seats for bus {bus_id} of type {bus_type}")
    
    seats_created = 0
    
    # Determine seating layout based on bus type
    if "Sleeper" in bus_type:
        # Sleeper buses: 2 columns, 2 decks (upper/lower)
        seats_per_row = 2
        decks = 2
        seats_per_deck = total_seats // decks
    else:
        # Seater buses: 4 columns (2x2), 1 deck
        seats_per_row = 4
        decks = 1
        seats_per_deck = total_seats
    
    current_row = 1
    current_column = 1
    current_deck = 0
    
    for seat_num in range(1, total_seats + 1):
        # Determine seat number format
        if "Sleeper" in bus_type:
            # Sleeper format: L1, L2, U1, U2 (Lower/Upper)
            deck_prefix = "L" if current_deck == 0 else "U"
            seat_number = f"{deck_prefix}{current_column}"
        else:
            # Seater format: A1, A2, A3, A4, B1, B2, etc.
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
            
            # Check if we need to move to next deck (for sleeper buses)
            if "Sleeper" in bus_type and current_row > (seats_per_deck // seats_per_row):
                current_row = 1
                current_deck += 1
    
    logger.info(f"Generated {seats_created} seats for bus {bus_id}")
    return seats_created

@router.get("/", response_model=List[BusResponse])
def get_buses(db: Session = Depends(get_db)):
    """Get all buses with their seat counts."""
    buses = db.query(Bus).options(joinedload(Bus.seats)).all()
    return buses

@router.post("/", response_model=BusResponse)
def create_bus(bus: BusCreate, db: Session = Depends(get_db)):
    """Create a new bus with automatic seat generation."""
    logger.info(f"Creating bus: {bus.name}, type: {bus.bus_type}, capacity: {bus.total_seats}")
    
    try:
        # Create the bus
        new_bus = Bus(
            name=bus.name,
            bus_type=bus.bus_type,
            total_seats=bus.total_seats
        )
        db.add(new_bus)
        db.flush()  # Get the bus ID
        
        # Generate seats automatically
        seats_created = generate_seats_for_bus(db, new_bus.id, bus.total_seats, bus.bus_type)
        
        db.commit()
        db.refresh(new_bus)
        
        logger.info(f"Successfully created bus {new_bus.id} with {seats_created} seats")
        return new_bus
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bus: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bus: {str(e)}")

@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(bus_id: int, db: Session = Depends(get_db)):
    """Get a specific bus by ID with its seats."""
    bus = db.query(Bus).options(joinedload(Bus.seats)).filter(Bus.id == bus_id).first()
    if not bus:
        logger.warning(f"Bus {bus_id} not found")
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.put("/{bus_id}", response_model=BusResponse)
def update_bus(bus_id: int, bus: BusUpdate, db: Session = Depends(get_db)):
    """Update an existing bus."""
    existing_bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not existing_bus:
        logger.warning(f"Bus {bus_id} not found for update")
        raise HTTPException(status_code=404, detail="Bus not found")
    
    try:
        # Update bus fields
        update_data = bus.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_bus, field, value)
        
        db.commit()
        db.refresh(existing_bus)
        logger.info(f"Updated bus {bus_id}")
        return existing_bus
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating bus {bus_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bus: {str(e)}")

@router.delete("/{bus_id}")
def delete_bus(bus_id: int, db: Session = Depends(get_db)):
    """Delete a bus (this will also delete all associated seats and trips)."""
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        logger.warning(f"Bus {bus_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Bus not found")
    
    try:
        db.delete(bus)
        db.commit()
        logger.info(f"Deleted bus {bus_id}")
        return {"message": "Bus deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting bus {bus_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete bus: {str(e)}")
