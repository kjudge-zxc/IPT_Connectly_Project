"""
Cache utilities for the Connectly API.

This module provides caching functions for optimizing
API performance by storing frequently accessed data.

Features:
- Feed caching with configurable timeout
- Cache key generation for different endpoints
- Cache invalidation on data changes
- Cache statistics for monitoring
"""

from django.core.cache import cache
from singletons.logger_singleton import LoggerSingleton

# Initialize logger
logger = LoggerSingleton().get_logger()

# Cache key patterns
FEED_CACHE_KEY = 'feed:{user_id}:{feed_type}:{page}:{page_size}'
POST_LIST_CACHE_KEY = 'posts:list:{page}:{page_size}'
POST_DETAIL_CACHE_KEY = 'post:detail:{post_id}'
USER_FEED_CACHE_KEY = 'user:{user_id}:feed'

# Cache timeouts (in seconds)
FEED_CACHE_TIMEOUT = 300  # 5 minutes
POST_CACHE_TIMEOUT = 600  # 10 minutes


def get_feed_cache_key(user_id=None, feed_type='all', page=1, page_size=20):
    """
    Generate cache key for feed endpoint.
    
    Args:
        user_id: ID of the requesting user (None for anonymous)
        feed_type: Type of feed (all, following, liked)
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        str: Formatted cache key
    """
    return FEED_CACHE_KEY.format(
        user_id=user_id or 'anonymous',
        feed_type=feed_type,
        page=page,
        page_size=page_size
    )


def get_cached_feed(cache_key):
    """
    Retrieve cached feed data.
    
    Args:
        cache_key: The cache key to look up
        
    Returns:
        Cached data if found, None otherwise
    """
    data = cache.get(cache_key)
    if data:
        logger.info(f"Cache HIT: {cache_key}")
    else:
        logger.info(f"Cache MISS: {cache_key}")
    return data


def set_cached_feed(cache_key, data, timeout=FEED_CACHE_TIMEOUT):
    """
    Store feed data in cache.
    
    Args:
        cache_key: The cache key to store under
        data: The data to cache
        timeout: Cache expiration time in seconds
    """
    cache.set(cache_key, data, timeout)
    logger.info(f"Cache SET: {cache_key} (timeout: {timeout}s)")


def invalidate_feed_cache():
    """
    Invalidate all feed-related caches.
    
    Called when posts are created, updated, or deleted
    to ensure users see fresh data.
    """
    # Clear all cache (for LocMemCache)
    # For Redis, use pattern-based deletion
    cache.clear()
    logger.info("Cache INVALIDATED: All feed caches cleared")


def invalidate_post_cache(post_id):
    """
    Invalidate cache for a specific post.
    
    Args:
        post_id: ID of the post to invalidate
    """
    cache_key = POST_DETAIL_CACHE_KEY.format(post_id=post_id)
    cache.delete(cache_key)
    logger.info(f"Cache INVALIDATED: {cache_key}")


def get_cache_stats():
    """
    Return cache statistics for monitoring.
    
    Returns:
        dict: Cache backend info and status
        
    Note:
        LocMemCache doesn't provide detailed stats.
        Redis would provide more detailed information.
    """
    return {
        'backend': 'LocMemCache',
        'status': 'active'
    }