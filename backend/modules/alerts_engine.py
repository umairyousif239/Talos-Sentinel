import os
import cv2
import time
import requests
from enum import Enum
from typing import Optional

from backend.api.vision import get_latest as fetch_latest_vision, get_snapshot_frame
from backend.api.sensors import get_latest as fetch_latest_sensors

from backend.modules.alert_state import AlertStatus, AlertSeverity

from backend.modules.alert_config import (
    VISION_FIRE_CONF,
    VISION_SMOKE_CONF,
    MQ135_SMOKE_RAW,
    THERMAL_FIRE_TEMP,
    THERMAL_DELTA,
    FLAME_DETECTED
)

# Weights
W_VISION_FIRE   = 0.35
W_VISION_SMOKE  = 0.15
W_FLAME         = 0.25
W_THERMAL       = 0.15
W_MQ135         = 0.10

TRIGGER_THRESHOLD = 0.50

# Global Alert Memory
current_alert = None
last_trigger_time = 0
PERSISTENCE_SECONDS = 5 #Alert must persist to ensure its not a false positive
RESOLVE_TIMEOUT = 10 # Seconds without trigger results in resolved status

# --- Evidence Capture Setup ---
SNAPSHOT_DIR = "backend/data/snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Rate of Rise Memory
last_max_temp_val = None
last_temp_time_val = None

def compute_severity(risk_score: float):
    """Dynamically scales the severity based on the mathematical risk."""
    if risk_score >= 0.75:
        return AlertSeverity.HIGH
    if risk_score >= 0.45:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW

# Core Evaluation Logic
def evaluate_alerts() -> Optional[dict]:
    """
    Pulls latest sensor and vision data
    Evaluates alert conditions
    Manages alert lifecycle
    """

    global current_alert, last_trigger_time
    global last_max_temp_val, last_temp_time_val

    vision = fetch_latest_vision()
    sensors = fetch_latest_sensors()

    now = time.time()
    timestamp_ms = int(now * 1000)

    if not vision or not sensors:
        return None

    # -----------------------------
    # Vision Scoring (0.0 to 1.0)
    # -----------------------------
    v_fire = vision.get("fire_confidence", 0.0)
    if v_fire < VISION_FIRE_CONF:
        v_fire = 0.0 # Zero out the noise

    v_smoke = vision.get("smoke_confidence", 0.0)
    if v_smoke < VISION_SMOKE_CONF:
        v_smoke = 0.0

    # -----------------------------
    # Sensor Normalization (0.0 to 1.0)
    # -----------------------------
    flame = sensors.get("flame", 0)
    mq135 = sensors.get("mq135_raw", 0)
    thermal = sensors.get("thermal", [])

    if not thermal:
        return None

    max_temp = max(thermal)
    min_temp = min(thermal)
    delta_temp = max_temp - min_temp
    
    # Rate of Rise Math
    thermal_ror = False
    if last_max_temp_val is not None and last_temp_time_val is not None:
        dt = max_temp - last_max_temp_val
        time_diff = now - last_temp_time_val
        
        if time_diff > 0:
            rate_of_rise = dt / time_diff
            # Trigger if temp jumps more than 2.0 celsius per second
            if rate_of_rise > 2.0:
                thermal_ror = True
                print(f"Rate of Rise SPIKE DETECTED: +{rate_of_rise:.1f}°C/s")
                
    # save the current state for the next frame's math
    last_max_temp_val = max_temp
    last_temp_time_val = now

    # Normalizing sensor values
    # Flame will be 1 if flame detected, 0 if not
    s_flame = 1.0 if flame == FLAME_DETECTED else 0.0

    # thermal: 1.0 if absolute temp hits 50 or RoR spikes or delta is massive
    s_thermal = 0.0
    if max_temp >= THERMAL_FIRE_TEMP or thermal_ror or delta_temp >= THERMAL_DELTA:
        s_thermal = 1.0
    elif max_temp >= 35.0:
        # partial score if its getting unusually warm (35c to 50c)
        s_thermal = min((max_temp - 35.0) / 15.0, 1.0)
    
    # MQ135L 400 is heavy smoke and 200 would give a score of 0.5
    s_mq135 = min(mq135 / MQ135_SMOKE_RAW, 1.0)


    # -----------------------------
    # Weighted Fusion Engine
    # -----------------------------
    risk_score = (
        (W_VISION_FIRE * v_fire) +
        (W_VISION_SMOKE * v_smoke) +
        (W_FLAME * s_flame) +
        (W_THERMAL * s_thermal) +
        (W_MQ135 * s_mq135)
    )
    
    risk_score = round(min(risk_score, 1.0), 2)

    # -----------------------------
    # Trigger Logic & Source Labeling
    # -----------------------------
    trigger = risk_score >= TRIGGER_THRESHOLD
    
    if v_fire > 0 or v_smoke > 0:
        source = "FUSED" if (s_flame  == 1 or s_thermal > 0 or s_mq135 > 0) else "VISION_ONLY"
    else:
        source = "SENSOR_ONLY"
    # -----------------------------
    # No Trigger → Possibly Resolve
    # -----------------------------
    if not trigger:
        if current_alert and (now - last_trigger_time) > RESOLVE_TIMEOUT:
            current_alert["status"] = AlertStatus.RESOLVED
            current_alert["resolved_at"] = timestamp_ms
            resolved = current_alert
            current_alert = None
            return resolved
        return None

    # -----------------------------
    # Trigger Active
    # -----------------------------
    severity = compute_severity(risk_score)

    # -----------------------------
    # Create New Alert
    # -----------------------------
    if current_alert is None:
        alert_id = f"alert_{int(now)}"
        
        current_alert = {
            "id": alert_id,
            "type": "FIRE" if (v_fire > v_smoke or s_flame == 1) else "SMOKE",
            "source": source,
            "status": AlertStatus.NEW,
            "severity": severity.name if isinstance(severity, Enum) else severity,
            "confidence": risk_score,
            "created_at": timestamp_ms,
            "snapshot_path": None, 
            "signals": {
                "vision_fire": v_fire > 0,
                "smoke": v_smoke > 0 or s_mq135 >= 0.5,
                "flame": s_flame == 1,
                "max_temp": round(max_temp, 1),
                "delta_temp": round(delta_temp, 1),
                "thermal_ror": thermal_ror,
                "mq135_raw": mq135,
            },
        }
        
        # Evidence Capture Logic
        frame = get_snapshot_frame()
        if frame is not None:
            filename = f"{alert_id}.jpg"
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            
            # write the image to the hard drive
            cv2.imwrite(filepath, frame)
            
            # attach the path to the alert dictionary
            current_alert["snapshot_path"] = filepath

        # Start persistence timer properly
        last_trigger_time = now
        return current_alert

    # -----------------------------
    # Update Existing Alert
    # -----------------------------

    # Promote NEW → ACTIVE after persistence window
    # Promote NEW → ACTIVE after persistence window
    if current_alert["status"] == AlertStatus.NEW:
        created_time_sec = current_alert["created_at"] / 1000.0
        if (now - created_time_sec) >= PERSISTENCE_SECONDS:
            current_alert["status"] = AlertStatus.ACTIVE

    # Update running alert
    current_alert.update({
        "severity": severity.name if isinstance(severity, Enum) else severity,
        "confidence": risk_score,
        "updated_at": timestamp_ms,
    })

    # Keep refreshing trigger timer while active
    last_trigger_time = now
    return current_alert
