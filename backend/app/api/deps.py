"""
API dependencies for rate limiting and other shared functionality."""

import time
import ipaddress
from typing import Optional
from fastapi import HTTPException, Request, Response
from app.core.redis import get_redis_client

class RateLimiter:
    """Redis-based rate limiter using fixed window counter."""
    
    def __init__(self, redis_key_prefix: str, limit: int, window_seconds: int = 60):
        self.redis_key_prefix = redis_key_prefix
        self.limit = limit
        self.window_seconds = window_seconds
        self.redis_client = get_redis_client()
    
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[int], Optional[int]]:
        """
        Check if request is allowed based on rate limit.
        
        Returns:
            (allowed, remaining, reset_time)
            allowed: bool - whether request is allowed
            remaining: Optional[int] - remaining requests in window
            reset_time: Optional[int] - Unix timestamp when window resets
        """
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # Redis key for this identifier and window
            key = f"{self.redis_key_prefix}:{identifier}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration on key
            pipe.expire(key, self.window_seconds)
            
            # Execute pipeline
            results = pipe.execute()
            current_requests = results[1]  # zcard result
            
            remaining = max(0, self.limit - current_requests)
            allowed = current_requests < self.limit
            reset_time = current_time + self.window_seconds
            
            if not allowed:
                print(f"[RATE LIMIT] Blocked {identifier}: {current_requests}/{self.limit} requests")
            
            return allowed, remaining, reset_time
            
        except Exception as e:
            print(f"[RATE LIMIT ERROR] Redis error: {type(e).__name__}: {e}")
            # Allow request if Redis fails (fail open)
            return True, None, None

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (common with proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the list
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"

def create_rate_limiter(limit: int, window_seconds: int = 60):
    """Factory function to create rate limiter dependency."""
    def rate_limit_dependency(request: Request, response: Response):
        """Rate limiting dependency function."""
        client_ip = get_client_ip(request)
        
        # Create rate limiter instance
        limiter = RateLimiter("rate_limit", limit, window_seconds)
        
        # Check if request is allowed
        allowed, remaining, reset_time = limiter.is_allowed(client_ip)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        if remaining is not None:
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        if reset_time is not None:
            response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again in a minute."
            )
        
        return None  # Dependency doesn't return anything
    
    return rate_limit_dependency

# Predefined rate limiters for different endpoints
search_rate_limiter = create_rate_limiter(limit=20, window_seconds=60)  # 20 requests per minute
booking_rate_limiter = create_rate_limiter(limit=5, window_seconds=60)   # 5 requests per minute
