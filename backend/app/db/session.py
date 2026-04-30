from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models import User, Bus, Route, Trip, Seat, Booking

# Use credentials from docker-compose.yml
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL or "postgresql://postgres:postgres@localhost:5432/redbus"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
