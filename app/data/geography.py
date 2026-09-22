"""
Static basin geography: river course, road network, settlements.

This is genuinely static (rivers/roads don't move), so unlike weather
data it isn't fetched from a live API — it's just committed data.
Replace these coordinates with real GIS data for your region (e.g.
traced from OpenStreetMap or a shapefile) when you have it; the shape
of the response is what matters for the frontend.
"""

from pydantic import BaseModel

MAP_CENTER: tuple[float, float] = (30.32, 78.05)

# Main river channel, running from the highland source down through the
# confluence and out to the southern reach.
RIVER_PATH: list[tuple[float, float]] = [
    (30.44, 77.94),
    (30.40, 78.00),
    (30.38, 78.01),
    (30.34, 78.03),
    (30.31, 78.06),
    (30.29, 78.09),
    (30.27, 78.11),
    (30.24, 78.14),
    (30.22, 78.16),
]

# A secondary tributary feeding into the main channel near the confluence.
TRIBUTARY_PATH: list[tuple[float, float]] = [
    (30.37, 78.13),
    (30.33, 78.11),
    (30.29, 78.09),
]

ROAD_PATHS: list[list[tuple[float, float]]] = [
    [
        (30.44, 77.95),
        (30.36, 78.00),
        (30.29, 78.10),
        (30.22, 78.17),
    ],
    [
        (30.31, 77.96),
        (30.34, 78.03),
        (30.36, 78.14),
    ],
    [
        (30.28, 77.90),
        (30.31, 77.96),
        (30.35, 78.05),
    ],
    [
        (30.43, 77.94),
        (30.40, 78.00),
        (30.37, 78.13),
    ],
]


class Settlement(BaseModel):
    name: str
    lat: float
    lng: float


SETTLEMENTS: list[Settlement] = [
    Settlement(name="Pinehill", lat=30.31, lng=77.96),
    Settlement(name="Cedar Fork", lat=30.35, lng=78.05),
    Settlement(name="Rivermouth", lat=30.27, lng=78.11),
    Settlement(name="Ridgeview", lat=30.37, lng=78.13),
    Settlement(name="Millbrook", lat=30.28, lng=77.90),
    Settlement(name="Highland Pass", lat=30.43, lng=77.94),
    Settlement(name="Southgate", lat=30.22, lng=78.16),
]
