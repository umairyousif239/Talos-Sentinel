from fastapi import APIRouter
from pydantic import BaseModel
from backend.modules.alerts_engine import evaluate_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])

latest_alert = None

class AlertPayload(BaseModel):
    sensor: dict
    vision: dict

@router.post("/evaluate")
def evaluate(payload: AlertPayload):
    global latest_alert

    sensor_data = payload.sensor
    vision_data = payload.vision

    alert = evaluate_alerts(sensor_data, vision_data)

    if alert:
        latest_alert = alert
        return {"status": "ALERT", "alert": alert}

    return {"status": "OK"}

@router.get("/latest")
def get_latest():
    return latest_alert or {"status": "NO_ALERT"}
