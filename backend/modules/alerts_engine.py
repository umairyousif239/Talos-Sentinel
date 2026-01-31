import time
import requests

from backend.modules.alert_config import (
    VISION_FIRE_CONF,
    MQ135_SMOKE_RAW,
    THERMAL_FIRE_TEMP,
    THERMAL_DELTA,
    FLAME_DETECTED,
)

# -----------------------------
# API endpoints (internal pull)
# -----------------------------
VISION_URL = "http://127.0.0.1:8000/vision/detections/latest"
SENSORS_URL = "http://127.0.0.1:8000/sensors/latest"

REQUEST_TIMEOUT = 0.25  # seconds


# -----------------------------
# Data Fetchers
# -----------------------------
def fetch_latest_vision():
    try:
        resp = requests.get(VISION_URL, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if "detections" in data:
                return data
    except Exception:
        pass
    return None


def fetch_latest_sensors():
    try:
        resp = requests.get(SENSORS_URL, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if "thermal" in data:
                return data
    except Exception:
        pass
    return None


# -----------------------------
# Alert Evaluation
# -----------------------------
def evaluate_alerts():
    """
    Pulls latest vision + sensor data
    Evaluates alert conditions
    Returns alert dict or None
    """

    vision = fetch_latest_vision()
    sensors = fetch_latest_sensors()

    if not vision or not sensors:
        return None

    # -----------------------------
    # Extract sensor values
    # -----------------------------
    detections = vision.get("detections", [])
    flame = sensors.get("flame", 0)
    mq135 = sensors.get("mq135_raw", 0)
    thermal = sensors.get("thermal", [])

    if not thermal:
        return None

    # -----------------------------
    # Derived thermal signals
    # -----------------------------
    max_temp = max(thermal)
    min_temp = min(thermal)
    delta_temp = max_temp - min_temp

    # -----------------------------
    # Vision signals
    # -----------------------------
    fire_detected = any(
        d["class"] == "fire" and d["confidence"] >= VISION_FIRE_CONF
        for d in detections
    )

    # -----------------------------
    # Sensor signals
    # -----------------------------
    smoke_detected = mq135 >= MQ135_SMOKE_RAW
    flame_detected = flame == FLAME_DETECTED
    thermal_fire = max_temp >= THERMAL_FIRE_TEMP
    thermal_spike = delta_temp >= THERMAL_DELTA

    timestamp_ms = int(time.time() * 1000)

    # -----------------------------
    # Alert decision matrix
    # -----------------------------
    if fire_detected and (smoke_detected or flame_detected or thermal_fire):
        return {
            "type": "FIRE_ALERT",
            "severity": "HIGH",
            "timestamp_ms": timestamp_ms,
            "signals": {
                "vision_fire": fire_detected,
                "smoke": smoke_detected,
                "flame": flame_detected,
                "max_temp": round(max_temp, 1),
                "delta_temp": round(delta_temp, 1),
                "mq135_raw": mq135,
            }
        }

    if smoke_detected and thermal_spike:
        return {
            "type": "SMOKE_ALERT",
            "severity": "MEDIUM",
            "timestamp_ms": timestamp_ms,
            "signals": {
                "smoke": smoke_detected,
                "max_temp": round(max_temp, 1),
                "delta_temp": round(delta_temp, 1),
                "mq135_raw": mq135,
            }
        }

    return None
