"""
Terrain steepness proxy via Open-Elevation.

Samples the target point plus four nearby points and estimates
terrain steepness from the elevation range.

For production flood prediction, replace this with a proper
DEM-derived slope raster.
"""

import httpx

from app.config import settings
from app.cache import elevation_cache


# Approximately 500 m in latitude.
OFFSET_DEG = 0.0045


async def get_slope_signal(lat: float, lon: float) -> dict:
    cache_key = (
        "slope",
        round(lat, 3),
        round(lon, 3),
    )

    if cache_key in elevation_cache:
        return elevation_cache[cache_key]

    points = [
        (lat, lon),
        (lat + OFFSET_DEG, lon),
        (lat - OFFSET_DEG, lon),
        (lat, lon + OFFSET_DEG),
        (lat, lon - OFFSET_DEG),
    ]

    locations_param = "|".join(
        f"{point_lat},{point_lon}"
        for point_lat, point_lon in points
    )

    slope_score = 50.0

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                15.0,
                connect=5.0,
            )
        ) as client:

            response = await client.get(
                settings.open_elevation_url,
                params={
                    "locations": locations_param,
                },
            )

            print(
                f"[OPEN-ELEVATION] "
                f"{response.status_code} "
                f"{response.url}",
                flush=True,
            )

            response.raise_for_status()

            data = response.json()

        results = data.get("results", [])

        elevations = []

        for item in results:
            elevation = item.get("elevation")

            if elevation is not None:
                elevations.append(float(elevation))

        if len(elevations) >= 2:

            elevation_range_m = (
                max(elevations) - min(elevations)
            )

            # Normalize:
            # 0m relief → 0
            # 150m+ relief → 100
            slope_score = round(
                min(elevation_range_m / 150.0, 1.0)
                * 100.0,
                1,
            )

        else:
            print(
                "[ELEVATION] Insufficient elevation data; "
                "using neutral slope score.",
                flush=True,
            )

    except Exception as exc:

        print(
            f"[ELEVATION FALLBACK] "
            f"lat={lat}, "
            f"lon={lon}, "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        # Neutral fallback.
        slope_score = 50.0

    result = {
        "slope_score": slope_score,
    }

    elevation_cache[cache_key] = result

    return result
