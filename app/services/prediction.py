import asyncio

from app.data.zones import Zone
from app.models.schemas import FloodPrediction
from app.services import open_meteo, elevation, scoring


async def build_prediction(
    zone_id: str,
    name: str,
    region: str,
    lat: float,
    lng: float,
) -> FloodPrediction:

    try:
        rainfall, soil, river, slope = await asyncio.gather(
            open_meteo.get_rainfall_signal(lat, lng),
            open_meteo.get_soil_moisture_signal(lat, lng),
            open_meteo.get_river_signal(lat, lng),
            elevation.get_slope_signal(lat, lng),
        )

    except Exception as exc:
        print(
            f"[PREDICTION ERROR] "
            f"zone={zone_id} "
            f"location={name} "
            f"lat={lat} "
            f"lng={lng} "
            f"error={type(exc).__name__}: {exc}",
            flush=True,
        )

        raise RuntimeError(
            f"Failed to fetch prediction data for {name}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        result = scoring.compute_risk(
            rainfall_6h_mm=rainfall["rainfall_6h_mm"],
            discharge_m3s=river["discharge_m3s"],
            discharge_rate=river["discharge_rate"],
            soil_moisture_pct=soil["soil_moisture_pct"],
            slope_score=slope["slope_score"],
        )

    except Exception as exc:
        print(
            f"[SCORING ERROR] "
            f"zone={zone_id} "
            f"error={type(exc).__name__}: {exc}",
            flush=True,
        )

        raise RuntimeError(
            f"Risk scoring failed for {name}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        return FloodPrediction(
            id=zone_id,
            location=name,
            region=region,
            latitude=lat,
            longitude=lng,
            probability=result["probability"],
            risk=result["risk"],
            rainfall=rainfall["rainfall_6h_mm"],
            riverLevel=river["discharge_m3s"],
            soilMoisture=soil["soil_moisture_pct"],
            updatedAt="just now",
        )

    except Exception as exc:
        print(
            f"[MODEL ERROR] "
            f"zone={zone_id} "
            f"error={type(exc).__name__}: {exc}",
            flush=True,
        )

        raise RuntimeError(
            f"Failed to create FloodPrediction for {name}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


async def build_prediction_for_zone(zone: Zone) -> FloodPrediction:
    return await build_prediction(
        zone.id,
        zone.name,
        zone.region,
        zone.lat,
        zone.lng,
    )


async def build_all_predictions(
    zones: list[Zone],
) -> list[FloodPrediction]:

    results = await asyncio.gather(
        *(build_prediction_for_zone(zone) for zone in zones),
        return_exceptions=True,
    )

    predictions: list[FloodPrediction] = []

    for zone, result in zip(zones, results):

        if isinstance(result, Exception):
            print(
                f"[ZONE ERROR] "
                f"zone={zone.id} "
                f"location={zone.name} "
                f"error={type(result).__name__}: {result}",
                flush=True,
            )

            # Re-raise so the router returns a proper error
            # instead of silently returning incomplete data.
            raise result

        predictions.append(result)

    return predictions
