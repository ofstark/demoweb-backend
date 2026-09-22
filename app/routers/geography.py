from fastapi import APIRouter
from app.data import geography
from app.models.schemas import GeographyResponse, SettlementOut

# AUTH TEMPORARILY DISABLED — re-add `Depends(get_current_user)` to
# dependencies below once login is confirmed working end-to-end.
router = APIRouter(prefix="/api", tags=["geography"])


@router.get("/geography", response_model=GeographyResponse)
async def get_geography():
    """Static basin geometry: river course(s), roads, settlements, map
    center. This doesn't change at runtime, so it's not cached/fetched
    like the live environmental signals — it's just served directly
    from data."""
    return GeographyResponse(
        mapCenter=geography.MAP_CENTER,
        riverPaths=[geography.RIVER_PATH, geography.TRIBUTARY_PATH],
        roadPaths=geography.ROAD_PATHS,
        settlements=[
            SettlementOut(name=s.name, lat=s.lat, lng=s.lng) for s in geography.SETTLEMENTS
        ],
    )
