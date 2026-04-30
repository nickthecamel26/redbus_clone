from fastapi import APIRouter

from app.api.v1.endpoints import users, buses, routes, bookings, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(buses.router, prefix="/buses", tags=["buses"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
