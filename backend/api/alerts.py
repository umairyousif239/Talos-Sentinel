from fastapi import APIRouter
from backend.modules.alert_loop import latest_alert, alert_history

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/history")
def get_history():
    """
    returns the last 100 triggered alerts
    """
    return alert_history

@router.get("/latest")
def get_latest():
    """
    Returns most recent alert (if any)
    """
    return latest_alert or {"status": "NO_ALERT"}
