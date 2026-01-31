from fastapi import APIRouter
from backend.modules.alerts_engine import evaluate_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])

latest_alert = None


@router.get("/evaluate")
def evaluate():
    """
    Triggers alert evaluation.
    Pulls vision + sensor data internally.
    """
    global latest_alert

    alert = evaluate_alerts()

    if alert:
        latest_alert = alert
        return {
            "status": "ALERT",
            "alert": alert
        }

    return {
        "status": "OK"
    }


@router.get("/latest")
def get_latest():
    """
    Returns most recent alert (if any)
    """
    return latest_alert or {"status": "NO_ALERT"}
