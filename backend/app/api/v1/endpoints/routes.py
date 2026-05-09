from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.route import Route
from app.schemas.route import RouteResponse, RouteCreate, RouteUpdate, RouteSearch
from app.core.logger import logger

router = APIRouter()

@router.get("/search")
def search_routes(source: str, destination: str, date: datetime, db: Session = Depends(get_db)):
    """Simple city pair checker - returns if route exists between cities."""
    logger.info(f"Searching for route: {source} -> {destination} on {date}")
    
    # Simple check if route exists between source and destination
    route = (
        db.query(Route)
        .filter(
            Route.source_city.ilike(f"%{source}%"),
            Route.destination_city.ilike(f"%{destination}%")
        )
        .first()
    )
    
    if route:
        return {
            "found": True,
            "source": route.source_city,
            "destination": route.destination_city,
            "distance_km": float(route.distance_km),
            "message": f"Route found between {source} and {destination}"
        }
    else:
        return {
            "found": False,
            "source": source,
            "destination": destination,
            "message": f"No route found between {source} and {destination}"
        }

@router.get("/", response_model=List[RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    """Get all active routes."""
    routes = db.query(Route).options(joinedload(Route.trips)).all()
    logger.info(f"Retrieved {len(routes)} routes")
    return routes

@router.post("/", response_model=RouteResponse)
def create_route(route: RouteCreate, db: Session = Depends(get_db)):
    """Create a new route."""
    logger.info(f"Creating route: {route.source_city} -> {route.destination_city}, distance: {route.distance_km}km")
    
    try:
        # Check if route already exists
        existing_route = (
            db.query(Route)
            .filter(
                Route.source_city == route.source_city,
                Route.destination_city == route.destination_city
            )
            .first()
        )
        
        if existing_route:
            logger.warning(f"Route already exists: {route.source_city} -> {route.destination_city}")
            raise HTTPException(
                status_code=400, 
                detail=f"Route from {route.source_city} to {route.destination_city} already exists"
            )
        
        # Create new route
        new_route = Route(
            source_city=route.source_city,
            destination_city=route.destination_city,
            distance_km=route.distance_km
        )
        
        db.add(new_route)
        db.commit()
        db.refresh(new_route)
        
        logger.info(f"Successfully created route {new_route.id}: {route.source_city} -> {route.destination_city}")
        return new_route
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating route: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create route: {str(e)}")

@router.get("/{route_id}", response_model=RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route by ID with its trips."""
    route = db.query(Route).options(joinedload(Route.trips)).filter(Route.id == route_id).first()
    if not route:
        logger.warning(f"Route {route_id} not found")
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.put("/{route_id}", response_model=RouteResponse)
def update_route(route_id: int, route: RouteUpdate, db: Session = Depends(get_db)):
    """Update an existing route."""
    existing_route = db.query(Route).filter(Route.id == route_id).first()
    if not existing_route:
        logger.warning(f"Route {route_id} not found for update")
        raise HTTPException(status_code=404, detail="Route not found")
    
    try:
        # Update route fields
        update_data = route.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_route, field, value)
        
        db.commit()
        db.refresh(existing_route)
        logger.info(f"Updated route {route_id}")
        return existing_route
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating route {route_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update route: {str(e)}")

@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """Delete a route (this will also delete all associated trips)."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        logger.warning(f"Route {route_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Route not found")
    
    try:
        db.delete(route)
        db.commit()
        logger.info(f"Deleted route {route_id}")
        return {"message": "Route deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting route {route_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete route: {str(e)}")
