from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class SeatBase(BaseModel):
    bus_id: int
    seat_number: str
    row: int
    column: int
    is_sleeper: Optional[bool] = None
    is_window: Optional[bool] = False
    deck: int  # 0 for lower, 1 for upper

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    seat_number: Optional[str] = None
    row: Optional[int] = None
    column: Optional[int] = None
    is_sleeper: Optional[bool] = None
    is_window: Optional[bool] = None
    deck: Optional[int] = None
    is_available: Optional[bool] = None

class SeatResponse(SeatBase):
    id: int
    is_available: bool
    
    class Config:
        from_attributes = True

class SeatWithStatus(SeatResponse):
    """Seat with live availability status for a specific trip."""
    pass

class SeatWithPricing(BaseModel):
    """Seat with dynamic pricing for a specific trip."""
    id: int
    bus_id: int
    seat_number: str
    row: int
    column: int
    is_sleeper: Optional[bool] = None
    is_window: Optional[bool] = False
    deck: int
    is_available: bool
    base_price: Decimal
    dynamic_price: Decimal
    
    class Config:
        from_attributes = True
