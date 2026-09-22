from fastapi import APIRouter, HTTPException
from app.data.zones import ZONES
from app.models.schemas import MonitoringZone
from app.services.prediction import build_all_predictions

# AUTH TEMPORARILY DISABLED — re-add `Depends(get_current_user)` to
# dependencies below once login is confirmed working end-to-end.
router = APIRouter(prefix="/api", tags=["locations"])


@router.get("/locations", response_model=list[MonitoringZone])
async def get_locations():
    """Monitoring zones enriched with their current live risk reading —
    used to render the GIS risk map markers."""
    try:
        predictions = await build_all_predictions(ZONES)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Upstream data fetch failed: {exc}") from exc

    zones_by_id = {z.id: z for z in ZONES}
    return [
        MonitoringZone(
            id=p.id,
            name=p.location,
            lat=zones_by_id[p.id].lat,
            lng=zones_by_id[p.id].lng,
            risk=p.risk,
            probability=p.probability,
            rainfall=p.rainfall,
            riverLevel=p.riverLevel,
            soilMoisture=p.soilMoisture,
        )
        for p in predictions
    ]


@router.get("/risk-map", response_model=list[MonitoringZone])
async def get_risk_map():
    """Alias of /locations — kept separate so the risk-map layer can
    evolve independently (e.g. add polygons instead of point radii)."""
    return await get_locations()
