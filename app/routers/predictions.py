from fastapi import APIRouter, HTTPException
from app.data.zones import ZONES
from app.models.schemas import FloodPrediction, PredictRequest
from app.services.prediction import build_all_predictions, build_prediction

# AUTH TEMPORARILY DISABLED — re-add `Depends(get_current_user)` to
# dependencies below once login is confirmed working end-to-end.
router = APIRouter(prefix="/api", tags=["predictions"])


@router.get("/predictions", response_model=list[FloodPrediction])
async def get_predictions():
    """Live flood-risk predictions for every configured monitoring zone."""
    try:
        return await build_all_predictions(ZONES)
    except Exception as exc:  # noqa: BLE001 — surface upstream API failures clearly
        raise HTTPException(status_code=502, detail=f"Upstream data fetch failed: {exc}") from exc


@router.post("/predict", response_model=FloodPrediction)
async def predict_custom_location(payload: PredictRequest):
    """On-demand prediction for an arbitrary lat/lon, not just the fixed zones."""
    try:
        return await build_prediction(
            zone_id=f"custom-{payload.latitude}-{payload.longitude}",
            name=payload.location,
            region=payload.region,
            lat=payload.latitude,
            lng=payload.longitude,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Upstream data fetch failed: {exc}") from exc
