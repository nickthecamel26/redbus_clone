from pydantic import BaseModel
from typing import Optional
from app.models.seat import SeatType, Deck

class SeatBase(BaseModel):
    bus_id: int
    seat_number: str
    seat_type: SeatType
    deck: Deck

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    seat_number: Optional[str] = None
    seat_type: Optional[SeatType] = None
    deck: Optional[Deck] = None
    is_available: Optional[bool] = None

class SeatResponse(SeatBase):
    id: int
    is_available: bool
    
    class Config:
        from_attributes = True
