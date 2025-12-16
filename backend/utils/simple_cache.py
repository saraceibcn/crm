# backend/utils/simple_cache.py
import time

_cache = {}

def cache_get(key):
    item = _cache.get(key)
    if not item:
        return None

    value, expires = item
    if expires < time.time():
        del _cache[key]
        return None

    return value

def cache_set(key, value, ttl_seconds=60):
    expires = time.time() + ttl_seconds
    _cache[key] = (value, expires)
