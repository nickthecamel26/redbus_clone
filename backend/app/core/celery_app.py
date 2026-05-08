import os
import socket
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Detect if running inside Docker container
def is_running_in_docker():
    """Check if the application is running inside a Docker container."""
    # Check for .dockerenv file (Docker creates this in containers)
    if os.path.exists('/.dockerenv'):
        return True
    # Check if 'docker' appears in /proc/1/cgroup (Linux containers)
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                return True
    except (FileNotFoundError, PermissionError):
        # /proc/1/cgroup doesn't exist on macOS, which means we're NOT in Docker
        pass
    return False

# 1. Configuration - Use appropriate defaults based on environment
if is_running_in_docker():
    # Docker environment - use service names
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/redbus")
else:
    # Local development - use localhost
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/redbus")

print(f"[Celery Config] Running in Docker: {is_running_in_docker()}")
print(f"[Celery Config] Using REDIS_URL: {REDIS_URL.replace('redis://', 'redis://***@')}")
print(f"[Celery Config] Using DATABASE_URL: {DATABASE_URL.replace('postgres:postgres@', '***@')}")

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
    # 4. Beat Schedule - Self-healing inventory system
    beat_schedule={
        "release-expired-bookings": {
            "task": "app.tasks.release_expired_bookings",
            "schedule": 60.0,  # Run every 60 seconds
        },
    },
)

# 4. Database Setup for the Worker
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# To import your tasks automatically, add this:
celery_app.autodiscover_tasks(['app'])