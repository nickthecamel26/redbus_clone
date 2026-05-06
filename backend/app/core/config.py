import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "RedBus Clone"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/redbus")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()