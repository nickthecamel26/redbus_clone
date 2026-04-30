from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class RouteBase(BaseModel):
    source: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    fare: Decimal
    total_seats: int
    available_seats: int

class RouteCreate(RouteBase):
    bus_id: int

class RouteUpdate(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    fare: Optional[Decimal] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None

class Route(RouteBase):
    id: int
    bus_id: int
    
    class Config:
        from_attributes = True

class RouteSearch(BaseModel):
    source: str
    destination: str
    travel_date: datetime
