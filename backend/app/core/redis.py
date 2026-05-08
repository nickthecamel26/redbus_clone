"""Redis client utility for caching."""

import redis
from typing import Optional, List, TypeVar, Type
from pydantic import TypeAdapter
from app.core.config import settings

T = TypeVar('T')

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        print(f"[REDIS DEBUG] Attempting to connect to Redis at: {settings.REDIS_URL}")
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True  # Automatically decode bytes to strings
            )
            # Test connection
            _redis_client.ping()
            print(f"[REDIS DEBUG] Successfully connected to Redis")
        except Exception as e:
            print(f"[REDIS ERROR] Failed to connect to Redis: {type(e).__name__}: {e}")
            raise
    return _redis_client


def get_cache_key(trip_id: int) -> str:
    """Generate cache key for trip seats."""
    return f"trip_seats:{trip_id}"


def get_cached_seats(trip_id: int, model_type: Type[T]) -> Optional[List[T]]:
    """
    Retrieve cached seat data from Redis.

    Args:
        trip_id: The trip ID to look up
        model_type: The Pydantic model type to deserialize into

    Returns:
        List of Pydantic models if cache hit, None if cache miss
    """
    key = get_cache_key(trip_id)
    print(f"[REDIS DEBUG] get_cached_seats: Attempting to get key='{key}'")

    try:
        client = get_redis_client()
        print(f"[REDIS DEBUG] get_cached_seats: Redis client obtained, calling get('{key}')")

        cached_data = client.get(key)
        print(f"[REDIS DEBUG] get_cached_seats: redis.get('{key}') returned: {type(cached_data)} - {cached_data is not None}")

        if cached_data:
            print(f"[REDIS DEBUG] get_cached_seats: Cache HIT for key='{key}', data length={len(cached_data)}")
            # Use TypeAdapter to deserialize list of Pydantic models
            type_adapter = TypeAdapter(List[model_type])
            result = type_adapter.validate_json(cached_data)
            print(f"[REDIS DEBUG] get_cached_seats: Successfully deserialized {len(result)} items")
            return result

        print(f"[REDIS DEBUG] get_cached_seats: Cache MISS for key='{key}' (returned None)")
        return None

    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] get_cached_seats: Connection error for key='{key}': {type(e).__name__}: {e}")
        return None
    except redis.RedisError as e:
        print(f"[REDIS ERROR] get_cached_seats: Redis error for key='{key}': {type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"[REDIS ERROR] get_cached_seats: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return None


def set_cached_seats(trip_id: int, seats_data: List[T], ttl: int = 60) -> bool:
    """
    Cache seat data in Redis with TTL.

    Args:
        trip_id: The trip ID to cache
        seats_data: List of Pydantic models to cache
        ttl: Time-to-live in seconds (default: 60)

    Returns:
        True if cached successfully, False otherwise
    """
    key = get_cache_key(trip_id)
    print(f"[REDIS DEBUG] set_cached_seats: Attempting to set key='{key}', ttl={ttl}s, data_count={len(seats_data)}")

    try:
        client = get_redis_client()
        print(f"[REDIS DEBUG] set_cached_seats: Redis client obtained")

        # Use TypeAdapter to serialize list of Pydantic models (handles Decimal, etc.)
        if seats_data:
            type_adapter = TypeAdapter(List[type(seats_data[0])])
            serialized_data = type_adapter.dump_json(seats_data)
            print(f"[REDIS DEBUG] set_cached_seats: Serialized {len(seats_data)} items, data size={len(serialized_data)} bytes")
        else:
            serialized_data = b"[]"
            print(f"[REDIS DEBUG] set_cached_seats: No data to cache, using empty array")

        result = client.setex(key, ttl, serialized_data)
        print(f"[REDIS DEBUG] set_cached_seats: redis.setex('{key}', {ttl}, ...) returned: {result}")
        return True

    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] set_cached_seats: Connection error for key='{key}': {type(e).__name__}: {e}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] set_cached_seats: Redis error for key='{key}': {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] set_cached_seats: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return False


def invalidate_seats_cache(trip_id: int) -> bool:
    """
    Invalidate cached seat data for a trip.
    Call this after booking changes to ensure fresh data.

    Args:
        trip_id: The trip ID to invalidate

    Returns:
        True if invalidated successfully, False otherwise
    """
    key = get_cache_key(trip_id)
    print(f"[REDIS DEBUG] invalidate_seats_cache: Attempting to delete key='{key}'")

    try:
        client = get_redis_client()
        result = client.delete(key)
        print(f"[REDIS DEBUG] invalidate_seats_cache: redis.delete('{key}') returned: {result} (deleted {result} key(s))")
        return True
    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] invalidate_seats_cache: Connection error for key='{key}': {type(e).__name__}: {e}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] invalidate_seats_cache: Redis error for key='{key}': {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] invalidate_seats_cache: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return False
