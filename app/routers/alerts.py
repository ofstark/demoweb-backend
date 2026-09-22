from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.data.zones import ZONES
from app.models.schemas import AlertItem
from app.services.prediction import build_all_predictions

# AUTH TEMPORARILY DISABLED — re-add `Depends(get_current_user)` to
# dependencies below once login is confirmed working end-to-end.
router = APIRouter(prefix="/api", tags=["alerts"])

# NOTE: this derives alerts live from current risk levels on every call.
# For real alert history (resolved alerts, "12 minutes ago" timestamps
# that persist across restarts), back this with a database that logs
# each risk-level change as it happens, rather than recomputing here.


@router.get("/alerts", response_model=list[AlertItem])
async def get_alerts():
    try:
        predictions = await build_all_predictions(ZONES)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Upstream data fetch failed: {exc}") from exc

    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    alerts: list[AlertItem] = []

    for p in predictions:
        if p.risk == "CRITICAL":
            alerts.append(
                AlertItem(
                    id=f"alert-{p.id}",
                    title="CRITICAL RISK DETECTED",
                    location=p.location,
                    severity="CRITICAL",
                    timestamp=now,
                    status="ACTIVE",
                    description=f"Probability {p.probability}% — rainfall {p.rainfall}mm, soil moisture {p.soilMoisture}%.",
                )
            )
        elif p.risk == "HIGH":
            alerts.append(
                AlertItem(
                    id=f"alert-{p.id}",
                    title="HIGH RISK DETECTED",
                    location=p.location,
                    severity="HIGH",
                    timestamp=now,
                    status="ACTIVE",
                    description=f"Probability {p.probability}% — rainfall {p.rainfall}mm, soil moisture {p.soilMoisture}%.",
                )
            )
        elif p.risk == "MODERATE":
            alerts.append(
                AlertItem(
                    id=f"alert-{p.id}",
                    title="ELEVATED CONDITIONS",
                    location=p.location,
                    severity="MODERATE",
                    timestamp=now,
                    status="MONITORING",
                    description=f"Probability {p.probability}% — conditions trending upward.",
                )
            )

    return alerts
