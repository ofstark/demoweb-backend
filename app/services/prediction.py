import asyncio
from app.data.zones import Zone
from app.models.schemas import FloodPrediction
from app.services import open_meteo, elevation, scoring


async def build_prediction(zone_id: str, name: str, region: str, lat: float, lng: float) -> FloodPrediction:
    rainfall, soil, river, slope = await asyncio.gather(
        open_meteo.get_rainfall_signal(lat, lng),
        open_meteo.get_soil_moisture_signal(lat, lng),
        open_meteo.get_river_signal(lat, lng),
        elevation.get_slope_signal(lat, lng),
    )

    result = scoring.compute_risk(
        rainfall_6h_mm=rainfall["rainfall_6h_mm"],
        discharge_m3s=river["discharge_m3s"],
        discharge_rate=river["discharge_rate"],
        soil_moisture_pct=soil["soil_moisture_pct"],
        slope_score=slope["slope_score"],
    )

    # riverLevel is expressed in the discharge proxy's native units here.
    # Replace with real gauge height (m) if you wire in a regional river API.
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


async def build_prediction_for_zone(zone: Zone) -> FloodPrediction:
    return await build_prediction(zone.id, zone.name, zone.region, zone.lat, zone.lng)


async def build_all_predictions(zones: list[Zone]) -> list[FloodPrediction]:
    return await asyncio.gather(*(build_prediction_for_zone(z) for z in zones))
