from pydantic import BaseModel
from typing import Optional
from app.models.bus import BusType

class BusBase(BaseModel):
    bus_number: str
    operator_name: str
    bus_type: BusType
    capacity: int

class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    bus_number: Optional[str] = None
    operator_name: Optional[str] = None
    bus_type: Optional[BusType] = None
    capacity: Optional[int] = None

class Bus(BusBase):
    id: int
    
    class Config:
        from_attributes = True
