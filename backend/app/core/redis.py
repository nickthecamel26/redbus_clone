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


def get_search_cache_key(source: str, destination: str, travel_date: str) -> str:
    """Generate cache key for trip search based on search parameters."""
    # Normalize source and destination to lowercase for consistent keys
    return f"trips_search:{source.lower()}:{destination.lower()}:{travel_date}"


def get_cached_search_results(source: str, destination: str, travel_date: str, model_type: Type[T]) -> Optional[List[T]]:
    """
    Retrieve cached search results from Redis.

    Args:
        source: Source city
        destination: Destination city
        travel_date: Travel date string (YYYY-MM-DD)
        model_type: The Pydantic model type to deserialize into

    Returns:
        List of Pydantic models if cache hit, None if cache miss
    """
    key = get_search_cache_key(source, destination, travel_date)
    print(f"[REDIS DEBUG] get_cached_search_results: Attempting to get key='{key}'")

    try:
        client = get_redis_client()
        print(f"[REDIS DEBUG] get_cached_search_results: Redis client obtained, calling get('{key}')")

        cached_data = client.get(key)
        print(f"[REDIS DEBUG] get_cached_search_results: redis.get('{key}') returned: {type(cached_data)} - {cached_data is not None}")

        if cached_data:
            print(f"[REDIS DEBUG] get_cached_search_results: Cache HIT for key='{key}', data length={len(cached_data)}")
            # Use TypeAdapter to deserialize list of Pydantic models
            type_adapter = TypeAdapter(List[model_type])
            result = type_adapter.validate_json(cached_data)
            print(f"[REDIS DEBUG] get_cached_search_results: Successfully deserialized {len(result)} items")
            return result

        print(f"[REDIS DEBUG] get_cached_search_results: Cache MISS for key='{key}' (returned None)")
        return None

    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] get_cached_search_results: Connection error for key='{key}': {type(e).__name__}: {e}")
        return None
    except redis.RedisError as e:
        print(f"[REDIS ERROR] get_cached_search_results: Redis error for key='{key}': {type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"[REDIS ERROR] get_cached_search_results: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return None


def set_cached_search_results(source: str, destination: str, travel_date: str, results_data: List[T], ttl: int = 300) -> bool:
    """
    Cache search results in Redis with TTL.

    Args:
        source: Source city
        destination: Destination city
        travel_date: Travel date string (YYYY-MM-DD)
        results_data: List of Pydantic models to cache
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)

    Returns:
        True if cached successfully, False otherwise
    """
    key = get_search_cache_key(source, destination, travel_date)
    print(f"[REDIS DEBUG] set_cached_search_results: Attempting to set key='{key}', ttl={ttl}s, data_count={len(results_data)}")

    try:
        client = get_redis_client()
        print(f"[REDIS DEBUG] set_cached_search_results: Redis client obtained")

        # Use TypeAdapter to serialize list of Pydantic models (handles Decimal, datetime, etc.)
        if results_data:
            type_adapter = TypeAdapter(List[type(results_data[0])])
            serialized_data = type_adapter.dump_json(results_data)
            print(f"[REDIS DEBUG] set_cached_search_results: Serialized {len(results_data)} items, data size={len(serialized_data)} bytes")
        else:
            serialized_data = b"[]"
            print(f"[REDIS DEBUG] set_cached_search_results: No data to cache, using empty array")

        result = client.setex(key, ttl, serialized_data)
        print(f"[REDIS DEBUG] set_cached_search_results: redis.setex('{key}', {ttl}, ...) returned: {result}")
        return True

    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] set_cached_search_results: Connection error for key='{key}': {type(e).__name__}: {e}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] set_cached_search_results: Redis error for key='{key}': {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] set_cached_search_results: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return False


def invalidate_search_cache(source: str, destination: str, travel_date: str) -> bool:
    """
    Invalidate cached search results for specific search parameters.

    Args:
        source: Source city
        destination: Destination city
        travel_date: Travel date string (YYYY-MM-DD)

    Returns:
        True if invalidated successfully, False otherwise
    """
    key = get_search_cache_key(source, destination, travel_date)
    print(f"[REDIS DEBUG] invalidate_search_cache: Attempting to delete key='{key}'")

    try:
        client = get_redis_client()
        result = client.delete(key)
        print(f"[REDIS DEBUG] invalidate_search_cache: redis.delete('{key}') returned: {result} (deleted {result} key(s))")
        return True
    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] invalidate_search_cache: Connection error for key='{key}': {type(e).__name__}: {e}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] invalidate_search_cache: Redis error for key='{key}': {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] invalidate_search_cache: Unexpected error for key='{key}': {type(e).__name__}: {e}")
        return False


def invalidate_booking_cache(trip_id: int, source: str, destination: str, travel_date_str: str) -> bool:
    """
    Invalidate all cache entries related to a booking.
    Deletes both seat map and search results cache.

    Args:
        trip_id: The trip ID
        source: Source city
        destination: Destination city
        travel_date_str: Travel date string (YYYY-MM-DD format)

    Returns:
        True if invalidation successful, False otherwise
    """
    seat_key = get_cache_key(trip_id)
    search_key = get_search_cache_key(source, destination, travel_date_str)

    print(f"[REDIS DEBUG] invalidate_booking_cache: Invalidating cache for Trip {trip_id}")
    print(f"[REDIS DEBUG] invalidate_booking_cache: Deleting seat key='{seat_key}', search key='{search_key}'")

    try:
        client = get_redis_client()

        # Delete both keys
        seat_deleted = client.delete(seat_key)
        search_deleted = client.delete(search_key)

        total_deleted = seat_deleted + search_deleted
        print(f"[REDIS DEBUG] Invalidated cache for Trip {trip_id}: deleted {total_deleted} key(s) "
              f"(seat_map={seat_deleted}, search={search_deleted})")
        return True

    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] invalidate_booking_cache: Connection error for trip_id={trip_id}: {type(e).__name__}: {e}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] invalidate_booking_cache: Redis error for trip_id={trip_id}: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] invalidate_booking_cache: Unexpected error for trip_id={trip_id}: {type(e).__name__}: {e}")
        return False

def clear_search_cache(source: str, destination: str, date: str) -> bool:
    """
    Clear all search cache entries for a specific route and date.
    Deletes keys that match pattern: trips_search:{source}:{destination}:{date}*
    
    Args:
        source: Source city
        destination: Destination city  
        date: Date string (YYYY-MM-DD format)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        
        # Build the key pattern for this route and date
        key_pattern = f"trips_search:{source}:{destination}:{date}*"
        print(f"[REDIS DEBUG] clear_search_cache: Clearing keys matching pattern='{key_pattern}'")
        
        # Find all keys matching the pattern
        keys = client.keys(key_pattern)
        
        if keys:
            # Delete all matching keys
            deleted_count = client.delete(*keys)
            print(f"[CACHE CLEAR] Deleted {deleted_count} search cache keys for {source} -> {destination} on {date}")
            return True
        else:
            print(f"[CACHE CLEAR] No search cache keys found for {source} -> {destination} on {date}")
            return True
            
    except redis.ConnectionError as e:
        print(f"[REDIS ERROR] clear_search_cache: Connection error - {str(e)}")
        return False
    except redis.RedisError as e:
        print(f"[REDIS ERROR] clear_search_cache: Redis error - {str(e)}")
        return False
    except Exception as e:
        print(f"[REDIS ERROR] clear_search_cache: Unexpected error - {type(e).__name__}: {str(e)}")
        return False
