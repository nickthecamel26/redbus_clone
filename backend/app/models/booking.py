from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import Base

class BookingStatus(str, enum.Enum):
    CONFIRMED = "Confirmed"
    PENDING = "Pending"
    CANCELLED = "Cancelled"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    booking_date = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="bookings")
    trip = relationship("Trip", back_populates="bookings")
    seat = relationship("Seat", back_populates="bookings")
