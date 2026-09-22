"""
Tier 1 flood-risk scoring: an explainable, weighted combination of
normalized environmental factors. No training data required — this
is a legitimate, documented approach used in real early-warning
systems before (or alongside) a trained ML model.

Swap-in path to Tier 2: once you have a labeled historical dataset
(location + factors -> flood_occurred), replace `compute_risk` with
a call to a trained classifier (e.g. XGBoost) that takes the same
four normalized inputs and outputs a probability. Nothing else in
the pipeline needs to change.
"""

from app.models.schemas import RiskLevel

WEIGHTS = {
    "rainfall": 0.35,
    "river": 0.25,
    "soil": 0.25,
    "slope": 0.15,
}


def normalize_rainfall(rainfall_6h_mm: float) -> float:
    """0mm -> 0.0, 100mm+ in 6h -> 1.0 (heavy-rain threshold)."""
    return min(rainfall_6h_mm / 100, 1.0)


def normalize_river(discharge_m3s: float, discharge_rate: float) -> float:
    """Combines absolute discharge level with its rate of rise.
    Since discharge scale varies wildly by river size, this leans
    mostly on the *rate of change* as the signal, with a small
    contribution from absolute magnitude."""
    rate_component = min(max(discharge_rate, 0) / 50, 1.0)  # 50 m3/s/day rise = severe
    level_component = min(discharge_m3s / 500, 1.0)  # crude magnitude signal
    return round(0.7 * rate_component + 0.3 * level_component, 3)


def normalize_soil(soil_moisture_pct: float) -> float:
    return min(soil_moisture_pct / 100, 1.0)


def normalize_slope(slope_score: float) -> float:
    return min(slope_score / 100, 1.0)


def classify(probability: float) -> RiskLevel:
    if probability < 30:
        return "LOW"
    if probability < 55:
        return "MODERATE"
    if probability < 75:
        return "HIGH"
    return "CRITICAL"


def compute_risk(
    rainfall_6h_mm: float,
    discharge_m3s: float,
    discharge_rate: float,
    soil_moisture_pct: float,
    slope_score: float,
) -> dict:
    rainfall_n = normalize_rainfall(rainfall_6h_mm)
    river_n = normalize_river(discharge_m3s, discharge_rate)
    soil_n = normalize_soil(soil_moisture_pct)
    slope_n = normalize_slope(slope_score)

    score = (
        WEIGHTS["rainfall"] * rainfall_n
        + WEIGHTS["river"] * river_n
        + WEIGHTS["soil"] * soil_n
        + WEIGHTS["slope"] * slope_n
    )
    probability = round(score * 100, 1)

    return {
        "probability": probability,
        "risk": classify(probability),
        "factors": {
            "rainfall": round(rainfall_n * 100, 1),
            "river": round(river_n * 100, 1),
            "soil": round(soil_n * 100, 1),
            "slope": round(slope_n * 100, 1),
        },
    }
