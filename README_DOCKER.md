# Redbus Clone - Docker Containerization

## Overview
Complete containerized setup for the Redbus Clone application with FastAPI backend, PostgreSQL, Redis, and Celery worker.

## Quick Start

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

## Architecture

```
┌─────────────────┐
│   pgAdmin      │  (Port 5050)
├─────────────────┤
│   Backend       │  (Port 8001)
├─────────────────┤
│   Redis         │  (Port 6379)
├─────────────────┤
│   PostgreSQL    │  (Port 5432)
├─────────────────┤
│   Celery Worker │
└─────────────────┘
```

## Services

### Backend (FastAPI)
- **Image**: Built from `backend/Dockerfile`
- **Base**: Python 3.12-slim
- **Port**: 8001 (External) → 8000 (Internal)
- **Environment**: Dynamic Docker/localhost detection
- **Health Check**: `/health` endpoint
- **Features**: 
  - Redis caching (seat maps + search results)
  - "The Reaper" cleanup (expired pending bookings)
  - Pessimistic locking
  - Razorpay payment integration

### PostgreSQL
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Data Volume**: `postgres_data`
- **Environment**: 
  - POSTGRES_USER=postgres
  - POSTGRES_PASSWORD=postgres
  - POSTGRES_DB=redbus

### Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Data Volume**: `redis_data`
- **Health Check**: Redis CLI ping

### Celery Worker
- **Image**: Built from backend Dockerfile
- **Command**: `celery -A app.core.celery_app worker --loglevel=info`
- **Dependencies**: PostgreSQL + Redis

### pgAdmin (Optional)
- **Image**: dpage/pgadmin4:latest
- **Port**: 5050
- **Access**: http://localhost:5050
- **Default**: admin@redbus.com / admin

## Environment Configuration

### Docker Environment
When running in Docker, services use container names:
- `DATABASE_URL`: `postgresql://postgres:postgres@postgres:5432/redbus`
- `REDIS_URL`: `redis://redis:6379/0`

### Local Development
When running locally, services use localhost:
- `DATABASE_URL`: `postgresql://postgres:postgres@localhost:5432/redbus`
- `REDIS_URL`: `redis://localhost:6379/0`

### Environment Detection
The backend automatically detects Docker vs local environment:
```python
def is_running_in_docker() -> bool:
    return os.path.exists('/.dockerenv')
```

## Key Features

### 1. Redis Caching
- **Seat Maps**: `trip_seats:{trip_id}` (60s TTL)
- **Search Results**: `trips_search:{source}:{destination}:{date}` (5min TTL)
- **Cache Invalidation**: Automatic after booking creation

### 2. "The Reaper" - Expired Booking Cleanup
- **Trigger**: Runs on every new booking via FastAPI BackgroundTasks
- **Cleanup**: Bookings older than 15 minutes in "Pending" status
- **Actions**: 
  - Mark booking as "CANCELLED"
  - Release seat (`is_available = True`)
  - Invalidate cache entries

### 3. Pessimistic Locking
- **Seat Selection**: `.with_for_update(nowait=True)`
- **Race Condition Prevention**: Atomic transactions
- **Error Handling**: User-friendly conflict messages

### 4. Payment Integration
- **Razorpay**: Order creation + webhook handling
- **Webhook Security**: Signature verification
- **Background Tasks**: Payment confirmation processing

## Development Workflow

### Local Development
```bash
# Backend (uses localhost URLs)
cd backend
uvicorn app.main:app --reload

# Redis (local instance)
redis-server

# PostgreSQL (local instance)
# Setup your local PostgreSQL instance
```

### Docker Development
```bash
# All services with container networking
docker-compose up --build

# Only specific services
docker-compose up -d postgres redis
docker-compose up --build backend
```

## Production Considerations

### Security
- Non-root user in containers
- Health checks for all services
- Environment variables via .env file
- Proper secrets management

### Monitoring
- Structured logging with `[REAPER]`, `[CACHE]`, `[DEBUG]` prefixes
- Health check endpoints
- Celery worker monitoring

### Scaling
- Backend: Multiple instances via load balancer
- PostgreSQL: Connection pooling
- Redis: Clustering for high availability
- Celery: Multiple workers for task distribution

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 8001, 5432, 6379, 5050 are available
2. **Connection Issues**: Check service health status
3. **Cache Issues**: Verify Redis connectivity from backend container
4. **Database Issues**: Check PostgreSQL logs and connection strings

### Logs
```bash
# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# View all logs
docker-compose logs
```

## Next Steps

1. **Environment Variables**: Update `.env` with production values
2. **SSL/TLS**: Add HTTPS termination for production
3. **Monitoring**: Add Prometheus/Grafana stack
4. **CI/CD**: GitHub Actions for automated deployment
5. **Scaling**: Kubernetes deployment configuration
