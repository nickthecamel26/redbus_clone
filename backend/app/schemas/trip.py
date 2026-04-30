from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TripBase(BaseModel):
    bus_id: int
    route_id: int
    departure_time: datetime
    arrival_time: datetime
    price: Decimal

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    bus_id: Optional[int] = None
    route_id: Optional[int] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    price: Optional[Decimal] = None

class TripResponse(TripBase):
    id: int
    
    class Config:
        from_attributes = True
