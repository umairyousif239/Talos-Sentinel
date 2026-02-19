import time
import copy
import asyncio
from backend.modules.alert_store import init_db, upsert_alert, load_active_alert
import backend.modules.alerts_engine as alerts_engine
from backend.modules.alerts_engine import evaluate_alerts

# Database Integration
init_db()

restored = load_active_alert()
if restored:
    alerts_engine.current_alert = restored
    print("Restored active alert from DB: ", restored["id"])

# Shared state
latest_alert = None
last_alert_signature = None
last_alert_time = 0
alert_history = []
MAX_ALERT_HISTORY = 100

ALERT_COOLDOWN_SEC = 5

async def alert_loop():
    global latest_alert, last_alert_signature, last_alert_time
    
    while True:
        try:
            alert = evaluate_alerts()
            
            if alert:
                # 1. ALWAYS save to the database immediately!
                # This guarantees NEW, ACTIVE, and RESOLVED hit the frontend instantly.
                upsert_alert(alert)
                
                signature = (
                    alert["type"],
                    alert.get("source"),
                )
                
                now = time.time()
                
                # 2. Keep the cooldown strictly for tracking the history array
                if (
                    signature != last_alert_signature
                    or (now - last_alert_time) > ALERT_COOLDOWN_SEC
                ):
                    latest_alert = alert
                    last_alert_signature = signature
                    last_alert_time = now

                    # Alert history tracking
                    alert_history.append(copy.deepcopy(alert))
                    alert_history[:] = alert_history[-MAX_ALERT_HISTORY:]
                    
                    print("ALERT LOGGED TO HISTORY: ", alert)

        except Exception as e:
            print("Alert Loop Error: ", e)
        
        await asyncio.sleep(1)
