"""
Live environmental data from Open-Meteo — free, no API key required.

- Forecast API gives hourly precipitation and soil moisture.
- Flood API gives daily river discharge (m3/s), used as a river-level
  proxy since a public, keyless, global river *stage* (meters) API
  does not exist. If you have access to a real gauge network (e.g.
  CWC in India, USGS in the US) for your region, replace
  `get_river_signal` with a call to that instead — the rest of the
  scoring pipeline doesn't care where the number came from.
"""

import httpx
from app.config import settings
from app.cache import weather_cache


async def get_rainfall_signal(lat: float, lon: float) -> dict:
    """Returns last-6h rainfall total (mm) and a simple trend label."""
    cache_key = ("rainfall", round(lat, 3), round(lon, 3))
    if cache_key in weather_cache:
        return weather_cache[cache_key]

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation",
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.open_meteo_forecast_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data.get("hourly", {})
    precip_series: list[float] = hourly.get("precipitation", []) or []

    # Find "now" as the last entry with actual (non-forecast) data by
    # taking the most recent 6 hours of the past_days=1 + forecast_days=1
    # window's first half (past 24h are indices 0-23).
    past_24h = precip_series[:24] if len(precip_series) >= 24 else precip_series
    last_6h = past_24h[-6:] if len(past_24h) >= 6 else past_24h
    prev_6h = past_24h[-12:-6] if len(past_24h) >= 12 else []

    rainfall_6h = round(sum(last_6h), 1)
    rainfall_prev_6h = round(sum(prev_6h), 1) if prev_6h else rainfall_6h

    if rainfall_6h > rainfall_prev_6h * 1.1:
        trend = "Increasing"
    elif rainfall_6h < rainfall_prev_6h * 0.9:
        trend = "Decreasing"
    else:
        trend = "Steady"

    result = {"rainfall_6h_mm": rainfall_6h, "trend": trend}
    weather_cache[cache_key] = result
    return result


async def get_soil_moisture_signal(lat: float, lon: float) -> dict:
    """Returns near-surface soil moisture as a 0-100 saturation percentage."""
    cache_key = ("soil", round(lat, 3), round(lon, 3))
    if cache_key in weather_cache:
        return weather_cache[cache_key]

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "soil_moisture_0_to_1cm",
        "forecast_days": 1,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.open_meteo_forecast_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    series: list[float] = data.get("hourly", {}).get("soil_moisture_0_to_1cm", []) or []
    latest = series[-1] if series else 0.2  # m3/m3, fallback mid-range

    # Open-Meteo reports volumetric water content (m3/m3), typical range
    # 0.0 (dry) to ~0.5 (saturated) depending on soil type. Normalize to
    # a 0-100 "saturation" style percentage for the UI.
    saturation_pct = round(min(max(latest / 0.5, 0), 1) * 100, 1)

    result = {"soil_moisture_pct": saturation_pct}
    weather_cache[cache_key] = result
    return result


async def get_river_signal(lat: float, lon: float) -> dict:
    """Returns river discharge (m3/s) and its recent rate of change, used
    as a river-level proxy."""
    cache_key = ("river", round(lat, 3), round(lon, 3))
    if cache_key in weather_cache:
        return weather_cache[cache_key]

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "river_discharge",
        "past_days": 3,
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.open_meteo_flood_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        series: list[float] = data.get("daily", {}).get("river_discharge", []) or []
    except httpx.HTTPError:
        # Flood API has limited global coverage (mainly larger rivers) —
        # fall back to a neutral reading rather than failing the request.
        series = []

    if len(series) >= 2:
        latest, previous = series[-1], series[-2]
        rate = round(latest - previous, 2)
    elif series:
        latest, rate = series[-1], 0.0
    else:
        latest, rate = 0.0, 0.0

    result = {"discharge_m3s": round(latest, 2), "discharge_rate": rate}
    weather_cache[cache_key] = result
    return result
