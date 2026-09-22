from fastapi import APIRouter, HTTPException

from app.data.zones import ZONES
from app.models.schemas import MonitoringZone
from app.services.prediction import build_all_predictions

router = APIRouter(prefix="/api", tags=["locations"])


@router.get("/locations", response_model=list[MonitoringZone])
async def get_locations():
    """Return monitoring zones with their current live risk readings."""

    try:
        predictions = await build_all_predictions(ZONES)

    except Exception as exc:
        print(
            f"[LOCATIONS ERROR] "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Failed to build monitoring locations",
                "error": type(exc).__name__,
                "details": str(exc),
            },
        ) from exc

    zones_by_id = {zone.id: zone for zone in ZONES}

    locations = []

    for prediction in predictions:
        zone = zones_by_id.get(prediction.id)

        if zone is None:
            print(
                f"[LOCATIONS ERROR] Unknown zone ID: {prediction.id}",
                flush=True,
            )

            continue

        locations.append(
            MonitoringZone(
                id=prediction.id,
                name=prediction.location,
                lat=zone.lat,
                lng=zone.lng,
                risk=prediction.risk,
                probability=prediction.probability,
                rainfall=prediction.rainfall,
                riverLevel=prediction.riverLevel,
                soilMoisture=prediction.soilMoisture,
            )
        )

    return locations


@router.get("/risk-map", response_model=list[MonitoringZone])
async def get_risk_map():
    """Alias for /locations."""

    return await get_locations()
