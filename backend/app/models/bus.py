from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import Base

class BusType(str, enum.Enum):
    AC_SEATER = "ac_seater"
    AC_SLEEPER = "ac_sleeper"
    NON_AC_SEATER = "non_ac_seater"
    NON_AC_SLEEPER = "non_ac_sleeper"

class Bus(Base):
    __tablename__ = "buses"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String, unique=True, index=True, nullable=False)
    operator_name = Column(String, nullable=False)
    bus_type = Column(Enum(BusType), nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    routes = relationship("Route", back_populates="bus")
