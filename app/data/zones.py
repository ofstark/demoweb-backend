"""
Fixed monitoring locations. Swap these lat/lon pairs for your real
region's coordinates — everything downstream (weather, soil, river,
elevation lookups) is driven entirely from this list.
"""

from pydantic import BaseModel


class Zone(BaseModel):
    id: str
    name: str
    region: str
    lat: float
    lng: float


ZONES: list[Zone] = [
    Zone(id="zone-a", name="Valley Sector A", region="Central Basin", lat=30.34, lng=78.03),
    Zone(id="zone-b", name="River Station 04", region="Eastern Confluence", lat=30.29, lng=78.09),
    Zone(id="zone-c", name="Northern Basin", region="Upper Watershed", lat=30.40, lng=78.00),
    Zone(id="zone-d", name="Pinehill Settlement", region="Western Slope", lat=30.31, lng=77.96),
    Zone(id="zone-e", name="Eastern Ridge", region="Highland Corridor", lat=30.36, lng=78.14),
    Zone(id="zone-f", name="Cedar Fork", region="Central Basin", lat=30.35, lng=78.05),
    Zone(id="zone-g", name="Rivermouth", region="Eastern Confluence", lat=30.27, lng=78.11),
    Zone(id="zone-h", name="Ridgeview", region="Highland Corridor", lat=30.37, lng=78.13),
    Zone(id="zone-i", name="Lower Basin Outlet", region="Southern Reach", lat=30.22, lng=78.16),
    Zone(id="zone-j", name="Highland Pass", region="Upper Watershed", lat=30.43, lng=77.94),
    Zone(id="zone-k", name="Millbrook Crossing", region="Western Slope", lat=30.28, lng=77.90),
]


def get_zone(zone_id: str) -> Zone | None:
    return next((z for z in ZONES if z.id == zone_id), None)
