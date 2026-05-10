from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.booking import BookingStatus

class BookingBase(BaseModel):
    pass

class BookingCreate(BaseModel):
    """Create bookings for multiple seats on a trip."""
    trip_id: int
    seat_ids: List[int]

class BookingCreateWithSeats(BaseModel):
    """Create bookings with seat numbers for a trip."""
    trip_id: int
    seat_numbers: List[str]
    total_amount: float

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None

class BookingResponse(BaseModel):
    id: int
    user_id: int
    trip_id: int
    seat_id: int
    status: BookingStatus
    total_price: Optional[Decimal] = None
    booking_date: datetime
    
    class Config:
        from_attributes = True

class BookingSummary(BaseModel):
    """Summary of created bookings."""
    bookings: List[BookingResponse]
    total_seats: int
    message: str


class MyBooking(BaseModel):
    """Booking details for 'My Bookings' view."""
    booking_id: int
    bus_name: str
    source: str
    destination: str
    travel_date: datetime
    seat_numbers: List[str]
    status: BookingStatus
    total_price: Optional[Decimal] = None
    
    class Config:
        from_attributes = True
