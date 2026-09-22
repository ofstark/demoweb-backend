"""
Terrain steepness proxy via Open-Elevation (free, no API key).

We sample the target point plus four neighbors ~500m to the north,
south, east and west, then compute the maximum elevation difference
across those samples as a simple slope proxy. This is intentionally
crude — for a real system, replace this with a proper DEM-derived
slope raster (e.g. via OpenTopography's SRTM data) sampled once per
zone at higher resolution.
"""

import httpx
from app.config import settings
from app.cache import elevation_cache

# ~500m in degrees latitude; longitude offset adjusted per-latitude below.
OFFSET_DEG = 0.0045


async def get_slope_signal(lat: float, lon: float) -> dict:
    cache_key = ("slope", round(lat, 3), round(lon, 3))
    if cache_key in elevation_cache:
        return elevation_cache[cache_key]

    lon_offset = OFFSET_DEG  # good enough approximation at mid-latitudes
    points = [
        (lat, lon),
        (lat + OFFSET_DEG, lon),
        (lat - OFFSET_DEG, lon),
        (lat, lon + lon_offset),
        (lat, lon - lon_offset),
    ]
    locations_param = "|".join(f"{p_lat},{p_lon}" for p_lat, p_lon in points)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                settings.open_elevation_url, params={"locations": locations_param}
            )
            resp.raise_for_status()
            data = resp.json()
        elevations = [r["elevation"] for r in data.get("results", [])]
    except (httpx.HTTPError, KeyError):
        elevations = []

    if len(elevations) >= 2:
        elevation_range_m = max(elevations) - min(elevations)
        # Normalize: >150m of relief across ~1km is steep hilly terrain.
        slope_score = round(min(elevation_range_m / 150, 1) * 100, 1)
    else:
        slope_score = 50.0  # neutral fallback if lookup fails

    result = {"slope_score": slope_score}
    elevation_cache[cache_key] = result
    return result
