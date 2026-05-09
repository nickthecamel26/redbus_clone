import os
from pydantic_settings import BaseSettings
from typing import Optional


def is_running_in_docker() -> bool:
    """Check if the application is running inside Docker container."""
    # Check for the existence of .dockerenv file (Docker creates this file)
    return os.path.exists('/.dockerenv')


class Settings(BaseSettings):
    PROJECT_NAME: str = "RedBus Clone"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Dynamic URL configuration based on environment
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        "redis://redis:6379/0" if is_running_in_docker() else "redis://localhost:6379/0"
    )
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@postgres:5432/redbus" if is_running_in_docker() else "postgresql://postgres:postgres@localhost:5432/redbus"
    )
    
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra environment variables

settings = Settings()