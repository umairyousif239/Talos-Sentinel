from fastapi import APIRouter, Depends

from backend.api.login import get_current_user

from backend.modules.alert_loop import latest_alert
from backend.modules.alert_store import (
    fetch_alert_history,
    fetch_latest_alert
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/history", dependencies=[Depends(get_current_user)])
def get_history(limit: int = 100):
    """
    returns the last 100 triggered alerts
    """
    return fetch_alert_history(limit)

@router.get("/latest", dependencies=[Depends(get_current_user)])
def get_latest():
    """
    Returns most recent alert (if any)
    """
    alert = fetch_latest_alert()
    return alert or {"status": "NO_ALERT"}
