"""
Live environmental data from Open-Meteo.

Provides:
- Recent rainfall
- Soil moisture
- River discharge proxy

All external requests have fallbacks so one unavailable upstream
service does not crash the complete FloodGuard dashboard.
"""

import httpx

from app.config import settings
from app.cache import weather_cache


async def _get_json(url: str, params: dict) -> dict:
    """Make a safe HTTP request to an upstream API."""

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0)
        ) as client:
            response = await client.get(url, params=params)

            print(
                f"[OPEN-METEO] {response.status_code} "
                f"{response.url}",
                flush=True,
            )

            response.raise_for_status()
            return response.json()

    except Exception as exc:
        print(
            f"[OPEN-METEO ERROR] "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        raise


async def get_rainfall_signal(lat: float, lon: float) -> dict:
    """Return rainfall during the recent 6-hour period."""

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

    try:
        data = await _get_json(
            settings.open_meteo_forecast_url,
            params,
        )

        hourly = data.get("hourly", {})

        precipitation = (
            hourly.get("precipitation", []) or []
        )

        if not precipitation:
            raise ValueError(
                "Open-Meteo returned no precipitation data"
            )

        # Use the latest six available hourly values.
        last_6h = precipitation[-6:]

        previous_6h = (
            precipitation[-12:-6]
            if len(precipitation) >= 12
            else []
        )

        rainfall_6h = round(
            sum(float(x or 0) for x in last_6h),
            1,
        )

        rainfall_previous = (
            round(
                sum(float(x or 0) for x in previous_6h),
                1,
            )
            if previous_6h
            else rainfall_6h
        )

        if rainfall_6h > rainfall_previous * 1.1:
            trend = "Increasing"
        elif rainfall_6h < rainfall_previous * 0.9:
            trend = "Decreasing"
        else:
            trend = "Steady"

        result = {
            "rainfall_6h_mm": rainfall_6h,
            "trend": trend,
        }

    except Exception as exc:
        print(
            f"[RAINFALL FALLBACK] "
            f"lat={lat}, lon={lon}, "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        # Neutral fallback so the dashboard remains operational.
        result = {
            "rainfall_6h_mm": 0.0,
            "trend": "Unknown",
        }

    weather_cache[cache_key] = result
    return result


async def get_soil_moisture_signal(lat: float, lon: float) -> dict:
    """Return near-surface soil moisture as a percentage."""

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

    try:
        data = await _get_json(
            settings.open_meteo_forecast_url,
            params,
        )

        series = (
            data.get("hourly", {})
            .get("soil_moisture_0_to_1cm", [])
            or []
        )

        if not series:
            raise ValueError(
                "Open-Meteo returned no soil moisture data"
            )

        latest = float(series[-1])

        # Convert volumetric water content to a simple
        # 0-100 UI percentage.
        saturation_pct = round(
            min(max(latest / 0.5, 0), 1) * 100,
            1,
        )

        result = {
            "soil_moisture_pct": saturation_pct,
        }

    except Exception as exc:
        print(
            f"[SOIL FALLBACK] "
            f"lat={lat}, lon={lon}, "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        result = {
            "soil_moisture_pct": 40.0,
        }

    weather_cache[cache_key] = result
    return result


async def get_river_signal(lat: float, lon: float) -> dict:
    """Return river discharge and recent discharge change."""

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
        data = await _get_json(
            settings.open_meteo_flood_url,
            params,
        )

        series = (
            data.get("daily", {})
            .get("river_discharge", [])
            or []
        )

        if len(series) >= 2:
            latest = float(series[-1])
            previous = float(series[-2])
            rate = round(latest - previous, 2)

        elif series:
            latest = float(series[-1])
            rate = 0.0

        else:
            latest = 0.0
            rate = 0.0

        result = {
            "discharge_m3s": round(latest, 2),
            "discharge_rate": rate,
        }

    except Exception as exc:
        print(
            f"[RIVER FALLBACK] "
            f"lat={lat}, lon={lon}, "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        result = {
            "discharge_m3s": 0.0,
            "discharge_rate": 0.0,
        }

    weather_cache[cache_key] = result
    return result
