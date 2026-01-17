import random
import requests

API_URL = "http://127.0.0.1:8000/sensor-frame"

while True:
    parts = random.randrange(100)
    payload = {
        "frame_id": int(parts),
        "timestamp_ms": int(parts),
        "flame": int(parts),
        "mq135_raw": int(parts),
        "thermal": [parts]
    }
    response = requests.post(API_URL, json=payload, timeout=0.2)
    print("POST", response.status_code)

