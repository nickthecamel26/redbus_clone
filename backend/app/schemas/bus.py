from pydantic import BaseModel
from typing import Optional
from app.models.bus import BusType

class BusBase(BaseModel):
    name: str
    bus_type: BusType
    total_seats: int

class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    name: Optional[str] = None
    bus_type: Optional[BusType] = None
    total_seats: Optional[int] = None

class BusResponse(BusBase):
    id: int
    
    class Config:
        from_attributes = True
