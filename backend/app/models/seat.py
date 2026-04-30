from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import Base

class SeatType(str, enum.Enum):
    SLEEPER = "Sleeper"
    SEATER = "Seater"

class Deck(str, enum.Enum):
    LOWER = "Lower"
    UPPER = "Upper"

class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    seat_number = Column(String, nullable=False)
    seat_type = Column(Enum(SeatType), nullable=False)
    deck = Column(Enum(Deck), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    bus = relationship("Bus", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat", cascade="all, delete-orphan")
