from cachetools import TTLCache
from app.config import settings

# Live environmental readings (rainfall, soil moisture, river discharge)
# refresh every WEATHER_CACHE_TTL seconds — avoids hammering free public
# APIs on every dashboard poll.
weather_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.weather_cache_ttl)

# Elevation/slope is effectively static — cache it for a long time.
elevation_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.elevation_cache_ttl)
