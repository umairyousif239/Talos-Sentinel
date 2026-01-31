import threading
import time
from backend.modules.alerts_engine import evaluate_alerts

# Shared state
latest_alert = None
last_alert_signature = None
ALERT_COOLDOWN_SEC = 10  # prevent spam


def alert_loop():
    global latest_alert, last_alert_signature

    while True:
        try:
            alert = evaluate_alerts()

            if alert:
                signature = (
                    alert["type"],
                    alert.get("source"),
                )

                # Deduplicate alerts
                if signature != last_alert_signature:
                    latest_alert = alert
                    last_alert_signature = signature
                    print("🚨 ALERT:", alert)

        except Exception as e:
            print("Alert loop error:", e)

        time.sleep(1)  # evaluate every 1 second


def start_alert_loop():
    thread = threading.Thread(target=alert_loop, daemon=True)
    thread.start()
