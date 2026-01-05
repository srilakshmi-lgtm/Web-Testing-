from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import os

limiter = Limiter(key_func=get_remote_address)

# Use Redis if available, otherwise fallback to simple cache
redis_url = os.getenv('REDIS_URL')
if redis_url and redis_url != 'redis://localhost:6379':
    cache = Cache(config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': redis_url})
else:
    cache = Cache(config={'CACHE_TYPE': 'simple'})
