from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.booking import BookingStatus, PaymentStatus

class BookingBase(BaseModel):
    seat_numbers: str

class BookingCreate(BookingBase):
    route_id: int

class BookingUpdate(BaseModel):
    seat_numbers: Optional[str] = None
    status: Optional[BookingStatus] = None
    payment_status: Optional[PaymentStatus] = None

class Booking(BookingBase):
    id: int
    user_id: int
    route_id: int
    total_fare: Decimal
    status: BookingStatus
    payment_status: PaymentStatus
    booked_at: datetime
    
    class Config:
        from_attributes = True
