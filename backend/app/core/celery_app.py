import os
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 1. Configuration - Use Docker service names as defaults
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
# IMPORTANT: Changed localhost to postgres for Docker networking
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/redbus")

# 2. Create Celery app
celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# 3. Explicit Configuration
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
)

# 4. Database Setup for the Worker
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# To import your tasks automatically, add this:
celery_app.autodiscover_tasks(['app'])