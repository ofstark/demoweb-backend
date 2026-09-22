from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.data.zones import ZONES
from app.models.schemas import AlertItem
from app.services.prediction import build_all_predictions

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertItem])
async def get_alerts():
    """
    Generate live alerts from the current flood-risk predictions.

    Alerts are derived from the latest predictions each time this
    endpoint is requested.
    """

    try:
        predictions = await build_all_predictions(ZONES)

    except Exception as exc:
        # Print the real error to Render logs so it can be diagnosed.
        print(
            f"[ALERTS ERROR] "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        # Return a useful error to the frontend.
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Failed to fetch prediction data",
                "error": type(exc).__name__,
                "details": str(exc),
            },
        ) from exc

    now = datetime.now(timezone.utc).strftime("%H:%M UTC")

    alerts: list[AlertItem] = []

    for prediction in predictions:

        if prediction.risk == "CRITICAL":
            alerts.append(
                AlertItem(
                    id=f"alert-{prediction.id}",
                    title="CRITICAL RISK DETECTED",
                    location=prediction.location,
                    severity="CRITICAL",
                    timestamp=now,
                    status="ACTIVE",
                    description=(
                        f"Probability {prediction.probability}% — "
                        f"rainfall {prediction.rainfall}mm, "
                        f"soil moisture {prediction.soilMoisture}%."
                    ),
                )
            )

        elif prediction.risk == "HIGH":
            alerts.append(
                AlertItem(
                    id=f"alert-{prediction.id}",
                    title="HIGH RISK DETECTED",
                    location=prediction.location,
                    severity="HIGH",
                    timestamp=now,
                    status="ACTIVE",
                    description=(
                        f"Probability {prediction.probability}% — "
                        f"rainfall {prediction.rainfall}mm, "
                        f"soil moisture {prediction.soilMoisture}%."
                    ),
                )
            )

        elif prediction.risk == "MODERATE":
            alerts.append(
                AlertItem(
                    id=f"alert-{prediction.id}",
                    title="ELEVATED CONDITIONS",
                    location=prediction.location,
                    severity="MODERATE",
                    timestamp=now,
                    status="MONITORING",
                    description=(
                        f"Probability {prediction.probability}% — "
                        f"conditions trending upward."
                    ),
                )
            )

    return alerts
