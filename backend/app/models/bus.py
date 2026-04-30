from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import Base

class BusType(str, enum.Enum):
    AC_SLEEPER = "AC Sleeper"
    NON_AC_SLEEPER = "Non-AC Sleeper"
    AC_SEATER = "AC Seater"
    NON_AC_SEATER = "Non-AC Seater"

class Bus(Base):
    __tablename__ = "buses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    bus_type = Column(Enum(BusType), nullable=False)
    total_seats = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    seats = relationship("Seat", back_populates="bus", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="bus", cascade="all, delete-orphan")
