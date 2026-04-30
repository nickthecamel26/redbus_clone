from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.booking import BookingStatus

class BookingBase(BaseModel):
    pass

class BookingCreate(BookingBase):
    trip_id: int
    seat_id: int

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None

class BookingResponse(BookingBase):
    id: int
    user_id: int
    trip_id: int
    seat_id: int
    status: BookingStatus
    booking_date: datetime
    
    class Config:
        from_attributes = True
