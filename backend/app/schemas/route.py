from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class RouteBase(BaseModel):
    source_city: str
    destination_city: str
    distance_km: Decimal

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    source_city: Optional[str] = None
    destination_city: Optional[str] = None
    distance_km: Optional[Decimal] = None

class RouteResponse(RouteBase):
    id: int
    
    class Config:
        from_attributes = True

class RouteSearch(BaseModel):
    source: str
    destination: str
    travel_date: datetime
