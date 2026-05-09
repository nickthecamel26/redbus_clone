from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, time
from decimal import Decimal

from app.schemas.bus import BusResponse
from app.schemas.route import RouteResponse

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
    bus: Optional[BusResponse] = None
    route: Optional[RouteResponse] = None
    
    class Config:
        from_attributes = True

class TripSearch(BaseModel):
    source: str
    destination: str
    date: datetime

class TripSearchResult(BaseModel):
    id: int
    bus_name: str
    departure_time: datetime
    arrival_time: datetime
    available_seats: int
    price: Decimal
    
    class Config:
        from_attributes = True

class BulkScheduleRequest(BaseModel):
    bus_id: int
    route_id: int
    start_date: date
    number_of_days: int
    departure_time_daily: time
    travel_duration_hours: float
    base_price: Optional[Decimal] = None
    
    class Config:
        from_attributes = True
