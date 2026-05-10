"""Locations endpoint: returns the union of unique source and destination
city names from the routes table. Used by the frontend autocomplete."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.route import Route
from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=List[str])
def list_locations(db: Session = Depends(get_db)) -> List[str]:
    """Return a sorted, de-duplicated list of every city referenced as either
    a source or destination across all routes."""
    sources = db.query(Route.source_city).distinct().all()
    destinations = db.query(Route.destination_city).distinct().all()

    cities = {row[0] for row in sources if row[0]} | {row[0] for row in destinations if row[0]}
    sorted_cities = sorted(cities)

    logger.info(f"Returning {len(sorted_cities)} unique locations")
    return sorted_cities
