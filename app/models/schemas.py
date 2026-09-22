from typing import Literal
from pydantic import BaseModel

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class FloodPrediction(BaseModel):
    id: str
    location: str
    region: str
    latitude: float
    longitude: float
    probability: float  # 0-100
    risk: RiskLevel
    rainfall: float  # mm, last 6h
    riverLevel: float  # proxy: normalized river discharge, meters-equivalent
    soilMoisture: float  # %
    updatedAt: str


class MonitoringZone(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    risk: RiskLevel
    probability: float
    rainfall: float
    riverLevel: float
    soilMoisture: float
    radius: int = 1800


class AlertItem(BaseModel):
    id: str
    title: str
    location: str
    severity: RiskLevel | Literal["INFO"]
    timestamp: str
    status: Literal["ACTIVE", "RESOLVED", "MONITORING"]
    description: str | None = None


class PredictRequest(BaseModel):
    latitude: float
    longitude: float
    location: str = "Custom Location"
    region: str = "Custom Region"


class SettlementOut(BaseModel):
    name: str
    lat: float
    lng: float


class GeographyResponse(BaseModel):
    mapCenter: tuple[float, float]
    riverPaths: list[list[tuple[float, float]]]
    roadPaths: list[list[tuple[float, float]]]
    settlements: list[SettlementOut]
