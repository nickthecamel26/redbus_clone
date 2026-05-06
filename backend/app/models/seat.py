from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    seat_number = Column(String(10), nullable=False)
    row = Column(Integer, nullable=False)
    column = Column(Integer, nullable=False)
    is_window = Column(Boolean, default=False)  # True for window seats
    is_sleeper = Column(Boolean, default=False)
    deck = Column(Integer, default=0)  # 0 for lower, 1 for upper
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    bus = relationship("Bus", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat", cascade="all, delete-orphan")
